#!/usr/bin/env python3
"""
模拟交易系统 V1.0
=================
基于策略扫描(ML+PPE+舆情+供应链)信号，执行模拟盘买卖。
- 默认虚拟资金: 100,000元
- 最大持仓4只，单只不超过总资产25%
- 5%硬止损 + 动态止损(浮盈5%上移2%)
- 止盈: 单日>7%减仓1/3, 累计>30%减仓1/3
- 每日最多买1只，卖不限

用法:
  python scripts/sim_trade.py                        # 默认10万资金
  python scripts/sim_trade.py --capital 200000       # 20万资金
  python scripts/sim_trade.py --date 2026-07-10      # 指定日期
  python scripts/sim_trade.py --dry-run               # 只出报告不执行
"""
import sys, os, json, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# 导入紧急停止开关
try:
    from alice_quant.execution.emergency_stop import EmergencyStop
except ImportError:
    EmergencyStop = None

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
SYMBOL_DIR = WORK_DIR / 'out_data' / 'ml_snapshots'

# ─── 模拟账户 ──────────────────────────────────────
class SimAccount:
    """模拟盘账户"""
    def __init__(self, initial_capital=100000):
        self.path = WORK_DIR / 'data' / 'sim_portfolio.json'
        if self.path.exists():
            with open(self.path, encoding='utf-8') as f:
                data = json.load(f)
            self.capital = data.get('capital', initial_capital)
            self.initial_capital = data.get('initial_capital', initial_capital)
            self.positions = data.get('positions', [])
            self.trade_history = data.get('trade_history', [])
            self.stats = data.get('stats', {
                'total_trades': 0, 'win_count': 0, 'loss_count': 0,
                'win_rate': 0, 'total_return_pct': 0
            })
            # 重置资金（用户指定时）
        else:
            self.capital = initial_capital
            self.initial_capital = initial_capital
            self.positions = []
            self.trade_history = []
            self.stats = {
                'total_trades': 0, 'win_count': 0, 'loss_count': 0,
                'win_rate': 0, 'total_return_pct': 0
            }
    
    def total_assets(self, date=None):
        """总资产 = 现金 + 持仓市值"""
        assets = self.capital
        for p in self.positions:
            price = p.get('current_price', p.get('buy_price', 0))
            if date:
                # 从DB查当日收盘价
                price = self._get_close(date, p['code'])
                if price and price > 0:
                    p['current_price'] = price
            assets += price * p.get('shares', 0)
        return assets
    
    def max_shares_for(self, code, current_price, max_pct=0.25):
        """单只最大可买股数（不超过总资产25%）"""
        assets = self.total_assets()
        max_amount = assets * max_pct - self._position_value(code)
        if max_amount <= 0:
            return 0
        return int(max_amount / current_price)
    
    def available_capital(self):
        """可用现金"""
        return self.capital
    
    def can_buy(self, code, shares, price):
        """检查能否买入"""
        if self._find_position(code) is not None:
            return False, "已有持仓"
        cost = shares * price
        if cost > self.capital:
            return False, "资金不足"
        max_shares = self.max_shares_for(code, price)
        if shares > max_shares:
            shares = max_shares
            if shares <= 0:
                return False, "已达25%仓位上限"
        return True, shares
    
    def buy(self, code, name, price, shares, reason):
        """买入"""
        can, shares_or_reason = self.can_buy(code, shares, price)
        if not can:
            return {'success': False, 'reason': shares_or_reason, 'shares': 0}
        
        shares = int(shares_or_reason)
        cost = shares * price
        # 手续费 (万2.5，最低5元)
        fee = max(cost * 0.00025, 5)
        self.capital -= (cost + fee)
        
        position = {
            'code': code,
            'name': name,
            'buy_price': price,
            'shares': shares,
            'buy_date': datetime.now().strftime('%Y-%m-%d'),
            'buy_time': datetime.now().strftime('%H:%M:%S'),
            'current_price': price,
            'stop_loss_5': round(price * 0.95, 2),
            'dynamic_stop': round(price * 0.95, 2),
            'reason': reason,
        }
        self.positions.append(position)
        
        trade = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': 'BUY', 'code': code, 'name': name,
            'price': price, 'shares': shares,
            'amount': cost, 'fee': round(fee, 2),
            'reason': reason,
        }
        self.trade_history.append(trade)
        self._save()
        return {'success': True, 'shares': shares, 'cost': cost + fee}
    
    def sell(self, code, price, reason, pct=1.0):
        """卖出（pct=1.0全卖，pct=0.33减1/3）"""
        pos = self._find_position(code)
        if not pos:
            return {'success': False, 'reason': '无持仓'}
        
        sell_shares = int(pos['shares'] * pct)
        if sell_shares <= 0:
            return {'success': False, 'reason': '股数为0'}
        
        revenue = sell_shares * price
        fee = max(revenue * 0.00025, 5)
        realized = (price - pos['buy_price']) * sell_shares
        
        self.capital += (revenue - fee)
        pos['shares'] -= sell_shares
        
        trade = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'action': 'SELL', 'code': code, 'name': pos['name'],
            'price': price, 'shares': sell_shares,
            'amount': revenue, 'fee': round(fee, 2),
            'realized_pnl': round(realized, 2),
            'reason': reason,
        }
        self.trade_history.append(trade)
        
        if pos['shares'] <= 0:
            self.positions.remove(pos)
            self.stats['total_trades'] += 1
            if realized >= 0:
                self.stats['win_count'] += 1
            else:
                self.stats['loss_count'] += 1
            self.stats['win_rate'] = round(
                self.stats['win_count'] / max(self.stats['total_trades'], 1), 3)
        
        self._save()
        return {'success': True, 'shares': sell_shares, 'realized': realized}
    
    def check_stop_loss(self, date=None):
        """检查止损（返回需要卖出的列表）"""
        to_sell = []
        for pos in self.positions:
            # 先更新当前价格
            if date:
                p = self._get_close(date, pos['code'])
                if p:
                    pos['current_price'] = p
            
            price = pos.get('current_price', pos['buy_price'])
            if price <= 0:
                continue
            
            # 5%硬止损
            if price <= pos['stop_loss_5']:
                to_sell.append((pos['code'], price, '跌破5%止损线', 1.0))
                continue
            
            # 动态止损：浮盈15%以上止损上移
            pnl_pct = (price - pos['buy_price']) / pos['buy_price']
            if pnl_pct >= 0.15:
                new_stop = pos['buy_price'] * 0.98
                if price <= new_stop:
                    to_sell.append((pos['code'], price, '动态止损触发', 1.0))
                continue
            
            # 单日>7%减仓1/3
            # 需要比较前一天收盘价
            prev_close = self._get_prev_close(date, pos['code'])
            if prev_close and price > 0:
                daily_chg = (price - prev_close) / prev_close
                if daily_chg > 0.07:
                    to_sell.append((pos['code'], price, '单日涨>7%止盈减仓1/3', 1/3))
                # 累计>30%减仓1/3
                if pnl_pct > 0.30 and 'already_reduced_30' not in pos:
                    to_sell.append((pos['code'], price, '累计涨>30%减仓1/3', 1/3))
                    pos['already_reduced_30'] = True
        
        return to_sell
    
    def _find_position(self, code):
        for p in self.positions:
            if p['code'] == code:
                return p
        return None
    
    def _position_value(self, code):
        for p in self.positions:
            if p['code'] == code:
                return p['buy_price'] * p['shares']
        return 0
    
    def _get_close(self, date, code):
        try:
            conn = sqlite3.connect(DB)
            # 查date当天或最近
            rows = conn.execute(
                'SELECT close FROM daily_k WHERE code=? AND date<=? ORDER BY date DESC LIMIT 1',
                (code, date)
            ).fetchall()
            conn.close()
            if rows:
                return float(rows[0][0])
        except:
            pass
        return 0
    
    def _get_prev_close(self, date, code):
        if not date:
            return 0
        try:
            d = datetime.strptime(date, '%Y-%m-%d')
            prev = (d - timedelta(days=1)).strftime('%Y-%m-%d')
            return self._get_close(prev, code)
        except:
            return 0
    
    def _save(self):
        data = {
            'capital': self.capital,
            'initial_capital': self.initial_capital,
            'positions': self.positions,
            'trade_history': self.trade_history[-200:],  # 只保留最近200笔
            'stats': self.stats,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def print_status(self, date=None):
        assets = self.total_assets(date)
        return_pct = (assets - self.initial_capital) / self.initial_capital * 100
        print(f'模拟账户总资产: {assets:,.0f}元 (初始{self.initial_capital:,}元)')
        print(f'收益率: {return_pct:+.2f}%')
        print(f'可用资金: {self.capital:,.0f}元')
        print(f'持仓: {len(self.positions)}只')
        for p in self.positions:
            pnl = (p.get('current_price', p['buy_price']) - p['buy_price']) / p['buy_price'] * 100
            print(f'  {p["code"]} {p["name"]}: {p["shares"]}股 浮盈{pnl:+.1f}% 止损{p["stop_loss_5"]}')


def load_candidates(date):
    """加载strategy_scan的候选票"""
    cand_path = SYMBOL_DIR / f'ml_candidates_{date.replace("-", "")}.json'
    if not cand_path.exists():
        return []
    with open(cand_path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', [])


def run_sim_trade(date=None, capital=100000, dry_run=False):
    """执行模拟盘交易"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 初始化紧急停止开关
    es = EmergencyStop() if EmergencyStop else None
    
    # 自动触发条件：单日亏损超过10%
    def auto_stop_condition():
        if es and es.is_stopped:
            return True
        assets = account.total_assets(date)
        loss_pct = (assets - account.initial_capital) / account.initial_capital
        return loss_pct < -0.10
    
    print(f'=== 模拟盘交易系统 {date} ===')
    print(f'{'='*60}')
    
    account = SimAccount(capital)
    
    # 检查紧急停止
    if es and es.is_stopped:
        print(f'\n🚨 紧急停止已触发: {es.stop_reason}')
        account.print_status(date)
        return account
    
    # 1. 更新持仓价格
    print('\n[Step 1] 更新持仓价格...')
    for pos in account.positions:
        price = account._get_close(date, pos['code'])
        if price and price > 0:
            pos['current_price'] = price
        # 动态止损上移
        current = pos.get('current_price', pos['buy_price'])
        pnl_pct = (current - pos['buy_price']) / pos['buy_price']
        if pnl_pct >= 0.05:
            new_stop = pos['buy_price'] * (0.95 + min(pnl_pct * 2, 0.04))
            if new_stop > pos['dynamic_stop']:
                pos['dynamic_stop'] = round(new_stop, 2)
                pos['stop_loss_5'] = round(new_stop, 2)
    account._save()
    
    # 2. 检查止损止盈
    print('\n[Step 2] 检查止损止盈...')
    stops = account.check_stop_loss(date)
    for code, price, reason, pct in stops:
        if dry_run:
            print(f'  [模拟] 卖出 {code}: {reason} ({pct*100:.0f}%)')
        else:
            result = account.sell(code, price, reason, pct)
            print(f'  {"✅" if result["success"] else "❌"} {code}: {reason} -> {result.get("shares", 0)}股, 盈亏{result.get("realized", 0):+,.0f}元')
    
    # 3. 加载候选票
    print('\n[Step 3] 加载候选票...')
    candidates = load_candidates(date)
    if not candidates:
        print('  无候选票数据，退出')
        return
    
    # 筛选: 评分>=50, ML概率>=0.5
    tradable = [c for c in candidates if c.get('score', 0) >= 60 and c.get('ml_prob', 0) >= 0.6]
    print(f'  候选{len(candidates)}只, 满足交易条件{len(tradable)}只')
    
    if not tradable:
        print('  无满足条件的股票，退出')
        return
    
    # 按评分排序
    tradable.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # 4. 执行买入（每天最多买1只）
    print('\n[Step 4] 执行买入...')
    today_buys = sum(1 for t in account.trade_history 
                     if t['action'] == 'BUY' and t['date'].startswith(date))
    
    if today_buys >= 1:
        print('  今日已买入1只，跳过')
    elif len(account.positions) >= 4:
        print('  持仓已达上限4只，跳过')
    else:
        # 取最高分
        best = tradable[0]
        code = best['code']
        # 查收盘价
        close_price = account._get_close(date, code)
        if not close_price or close_price == 0:
            # 查实时行情（收盘前，通过统一接口）
            try:
                from scripts.data_api import DataAPI
                rt = DataAPI.get_realtime([code])
                if rt:
                    for k, v in rt.items():
                        close_price = v['price']
                        break
            except:
                close_price = 0
        
        if close_price and close_price > 0:
            # 按可用资金的20%买入（留出余地）
            target_amount = min(account.capital * 0.20, 
                              account.total_assets() * 0.25)
            shares = max(int(target_amount / close_price / 100) * 100, 100)
            
            if dry_run:
                cost = shares * close_price
                print(f'  [模拟] 买入 {code} {best["name"]}: {shares}股 @ {close_price:.2f}元 (成本{cost:,.0f}元)')
            else:
                result = account.buy(code, best['name'], close_price, shares, 
                                    f"ML:{best.get('ml_prob', 0):.0%} 评分:{best.get('score', 0):.1f} {best.get('sentiment_keywords', '')}")
                if result['success']:
                    print(f'  ✅ 买入 {code} {best["name"]}: {result["shares"]}股 @ {close_price:.2f}元')
                    print(f'     成本: {result["cost"]:,.0f}元')
                else:
                    print(f'  ❌ 买入失败: {result["reason"]}')
    
    # 5. 打印状态
    print(f'\n{'='*60}')
    account.print_status(date)
    print(f'\n总交易数: {account.stats["total_trades"]} 胜率: {account.stats["win_rate"]*100:.1f}%')
    
    # 6. 保存日志
    log_path = SYMBOL_DIR / f'sim_trade_{date.replace("-", "")}.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date,
            'account': {
                'capital': account.capital,
                'positions': account.positions,
                'stats': account.stats,
            },
            'today_trades': [t for t in account.trade_history if t['date'].startswith(date)],
            'candidates_evaluated': len(candidates),
            'tradable': len(tradable),
        }, f, ensure_ascii=False, indent=2)
    
    print(f'\n日志已保存: {log_path}')
    return account


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--capital', type=int, default=100000)
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--dry-run', action='store_true', help='只出报告不执行')
    args = parser.parse_args()
    
    run_sim_trade(date=args.date, capital=args.capital, dry_run=args.dry_run)
