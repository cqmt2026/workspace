#!/usr/bin/env python3
"""
妯℃嫙浜ゆ槗绯荤粺 V1.0
=================
鍩轰簬绛栫暐鎵弿(ML+PPE+鑸嗘儏+渚涘簲閾?淇″彿锛屾墽琛屾ā鎷熺洏涔板崠銆?- 榛樿铏氭嫙璧勯噾: 100,000鍏?- 鏈€澶ф寔浠?鍙紝鍗曞彧涓嶈秴杩囨€昏祫浜?5%
- 5%纭鎹?+ 鍔ㄦ€佹鎹?娴泩5%涓婄Щ2%)
- 姝㈢泩: 鍗曟棩>7%鍑忎粨1/3, 绱>30%鍑忎粨1/3
- 姣忔棩鏈€澶氫拱1鍙紝鍗栦笉闄?
鐢ㄦ硶:
  python scripts/sim_trade.py                        # 榛樿10涓囪祫閲?  python scripts/sim_trade.py --capital 200000       # 20涓囪祫閲?  python scripts/sim_trade.py --date 2026-07-10      # 鎸囧畾鏃ユ湡
  python scripts/sim_trade.py --dry-run               # 鍙嚭鎶ュ憡涓嶆墽琛?"""
import sys, os, json, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# 瀵煎叆绱ф€ュ仠姝㈠紑鍏?try:
    from alice_quant.execution.emergency_stop import EmergencyStop
except ImportError:
    EmergencyStop = None

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
SYMBOL_DIR = WORK_DIR / 'out_data' / 'ml_snapshots'

# 鈹€鈹€鈹€ 妯℃嫙璐︽埛 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class SimAccount:
    """妯℃嫙鐩樿处鎴?""
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
            # 閲嶇疆璧勯噾锛堢敤鎴锋寚瀹氭椂锛?        else:
            self.capital = initial_capital
            self.initial_capital = initial_capital
            self.positions = []
            self.trade_history = []
            self.stats = {
                'total_trades': 0, 'win_count': 0, 'loss_count': 0,
                'win_rate': 0, 'total_return_pct': 0
            }
    
    def total_assets(self, date=None):
        """鎬昏祫浜?= 鐜伴噾 + 鎸佷粨甯傚€?""
        assets = self.capital
        for p in self.positions:
            price = p.get('current_price', p.get('buy_price', 0))
            if date:
                # 浠嶥B鏌ュ綋鏃ユ敹鐩樹环
                price = self._get_close(date, p['code'])
                if price and price > 0:
                    p['current_price'] = price
            assets += price * p.get('shares', 0)
        return assets
    
    def max_shares_for(self, code, current_price, max_pct=0.25):
        """鍗曞彧鏈€澶у彲涔拌偂鏁帮紙涓嶈秴杩囨€昏祫浜?5%锛?""
        assets = self.total_assets()
        max_amount = assets * max_pct - self._position_value(code)
        if max_amount <= 0:
            return 0
        return int(max_amount / current_price)
    
    def available_capital(self):
        """鍙敤鐜伴噾"""
        return self.capital
    
    def can_buy(self, code, shares, price):
        """妫€鏌ヨ兘鍚︿拱鍏?""
        if self._find_position(code) is not None:
            return False, "宸叉湁鎸佷粨"
        cost = shares * price
        if cost > self.capital:
            return False, "璧勯噾涓嶈冻"
        max_shares = self.max_shares_for(code, price)
        if shares > max_shares:
            shares = max_shares
            if shares <= 0:
                return False, "宸茶揪25%浠撲綅涓婇檺"
        return True, shares
    
    def buy(self, code, name, price, shares, reason):
        """涔板叆"""
        can, shares_or_reason = self.can_buy(code, shares, price)
        if not can:
            return {'success': False, 'reason': shares_or_reason, 'shares': 0}
        
        shares = int(shares_or_reason)
        cost = shares * price
        # 鎵嬬画璐?(涓?.5锛屾渶浣?鍏?
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
        """鍗栧嚭锛坧ct=1.0鍏ㄥ崠锛宲ct=0.33鍑?/3锛?""
        pos = self._find_position(code)
        if not pos:
            return {'success': False, 'reason': '鏃犳寔浠?}
        
        sell_shares = int(pos['shares'] * pct)
        if sell_shares <= 0:
            return {'success': False, 'reason': '鑲℃暟涓?'}
        
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
        """妫€鏌ユ鎹燂紙杩斿洖闇€瑕佸崠鍑虹殑鍒楄〃锛?""
        to_sell = []
        for pos in self.positions:
            # 鍏堟洿鏂板綋鍓嶄环鏍?            if date:
                p = self._get_close(date, pos['code'])
                if p:
                    pos['current_price'] = p
            
            price = pos.get('current_price', pos['buy_price'])
            if price <= 0:
                continue
            
            # 5%纭鎹?            if price <= pos['stop_loss_5']:
                to_sell.append((pos['code'], price, '璺岀牬5%姝㈡崯绾?, 1.0))
                continue
            
            # 鍔ㄦ€佹鎹燂細娴泩15%浠ヤ笂姝㈡崯涓婄Щ
            pnl_pct = (price - pos['buy_price']) / pos['buy_price']
            if pnl_pct >= 0.15:
                new_stop = pos['buy_price'] * 0.98
                if price <= new_stop:
                    to_sell.append((pos['code'], price, '鍔ㄦ€佹鎹熻Е鍙?, 1.0))
                continue
            
            # 鍗曟棩>7%鍑忎粨1/3
            # 闇€瑕佹瘮杈冨墠涓€澶╂敹鐩樹环
            prev_close = self._get_prev_close(date, pos['code'])
            if prev_close and price > 0:
                daily_chg = (price - prev_close) / prev_close
                if daily_chg > 0.07:
                    to_sell.append((pos['code'], price, '鍗曟棩娑?7%姝㈢泩鍑忎粨1/3', 1/3))
                # 绱>30%鍑忎粨1/3
                if pnl_pct > 0.30 and 'already_reduced_30' not in pos:
                    to_sell.append((pos['code'], price, '绱娑?30%鍑忎粨1/3', 1/3))
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
            # 鏌ate褰撳ぉ鎴栨渶杩?            rows = conn.execute(
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
            'trade_history': self.trade_history[-200:],  # 鍙繚鐣欐渶杩?00绗?            'stats': self.stats,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def print_status(self, date=None):
        assets = self.total_assets(date)
        return_pct = (assets - self.initial_capital) / self.initial_capital * 100
        print(f'妯℃嫙璐︽埛鎬昏祫浜? {assets:,.0f}鍏?(鍒濆{self.initial_capital:,}鍏?')
        print(f'鏀剁泭鐜? {return_pct:+.2f}%')
        print(f'鍙敤璧勯噾: {self.capital:,.0f}鍏?)
        print(f'鎸佷粨: {len(self.positions)}鍙?)
        for p in self.positions:
            pnl = (p.get('current_price', p['buy_price']) - p['buy_price']) / p['buy_price'] * 100
            print(f'  {p["code"]} {p["name"]}: {p["shares"]}鑲?娴泩{pnl:+.1f}% 姝㈡崯{p["stop_loss_5"]}')


def load_candidates(date):
    """鍔犺浇strategy_scan鐨勫€欓€夌エ"""
    cand_path = SYMBOL_DIR / f'ml_candidates_{date.replace("-", "")}.json'
    if not cand_path.exists():
        return []
    with open(cand_path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', [])


def run_sim_trade(date=None, capital=100000, dry_run=False):
    """鎵ц妯℃嫙鐩樹氦鏄?""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 鍒濆鍖栫揣鎬ュ仠姝㈠紑鍏?    es = EmergencyStop() if EmergencyStop else None
    
    # 鑷姩瑙﹀彂鏉′欢锛氬崟鏃ヤ簭鎹熻秴杩?0%
    def auto_stop_condition():
        if es and es.is_stopped:
            return True
        assets = account.total_assets(date)
        loss_pct = (assets - account.initial_capital) / account.initial_capital
        return loss_pct < -0.10
    
    print(f'=== 妯℃嫙鐩樹氦鏄撶郴缁?{date} ===')
    print(f'{'='*60}')
    
    account = SimAccount(capital)
    
    # 妫€鏌ョ揣鎬ュ仠姝?    if es and es.is_stopped:
        print(f'\n馃毃 绱ф€ュ仠姝㈠凡瑙﹀彂: {es.stop_reason}')
        account.print_status(date)
        return account
    
    # 1. 鏇存柊鎸佷粨浠锋牸
    print('\n[Step 1] 鏇存柊鎸佷粨浠锋牸...')
    for pos in account.positions:
        price = account._get_close(date, pos['code'])
        if price and price > 0:
            pos['current_price'] = price
        # 鍔ㄦ€佹鎹熶笂绉?        current = pos.get('current_price', pos['buy_price'])
        pnl_pct = (current - pos['buy_price']) / pos['buy_price']
        if pnl_pct >= 0.05:
            new_stop = pos['buy_price'] * (0.95 + min(pnl_pct * 2, 0.04))
            if new_stop > pos['dynamic_stop']:
                pos['dynamic_stop'] = round(new_stop, 2)
                pos['stop_loss_5'] = round(new_stop, 2)
    account._save()
    
    # 2. 妫€鏌ユ鎹熸鐩?    print('\n[Step 2] 妫€鏌ユ鎹熸鐩?..')
    stops = account.check_stop_loss(date)
    for code, price, reason, pct in stops:
        if dry_run:
            print(f'  [妯℃嫙] 鍗栧嚭 {code}: {reason} ({pct*100:.0f}%)')
        else:
            result = account.sell(code, price, reason, pct)
            print(f'  {"鉁? if result["success"] else "鉂?} {code}: {reason} -> {result.get("shares", 0)}鑲? 鐩堜簭{result.get("realized", 0):+,.0f}鍏?)
    
    # 3. 鍔犺浇鍊欓€夌エ
    print('\n[Step 3] 鍔犺浇鍊欓€夌エ...')
    candidates = load_candidates(date)
    if not candidates:
        print('  鏃犲€欓€夌エ鏁版嵁锛岄€€鍑?)
        return
    
    # 绛涢€? 璇勫垎>=50, ML姒傜巼>=0.5
    tradable = [c for c in candidates if c.get('score', 0) >= 60 and c.get('ml_prob', 0) >= 0.6]
    print(f'  鍊欓€墈len(candidates)}鍙? 婊¤冻浜ゆ槗鏉′欢{len(tradable)}鍙?)
    
    if not tradable:
        print('  鏃犳弧瓒虫潯浠剁殑鑲＄エ锛岄€€鍑?)
        return
    
    # 鎸夎瘎鍒嗘帓搴?    tradable.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # 4. 鎵ц涔板叆锛堟瘡澶╂渶澶氫拱1鍙級
    print('\n[Step 4] 鎵ц涔板叆...')
    today_buys = sum(1 for t in account.trade_history 
                     if t['action'] == 'BUY' and t['date'].startswith(date))
    
    if today_buys >= 1:
        print('  浠婃棩宸蹭拱鍏?鍙紝璺宠繃')
    elif len(account.positions) >= 4:
        print('  鎸佷粨宸茶揪涓婇檺4鍙紝璺宠繃')
    else:
        # 鍙栨渶楂樺垎
        best = tradable[0]
        code = best['code']
        # 鏌ユ敹鐩樹环
        close_price = account._get_close(date, code)
        if not close_price or close_price == 0:
            # 鏌ュ疄鏃惰鎯咃紙鏀剁洏鍓嶏紝閫氳繃缁熶竴鎺ュ彛锛?            try:
                from scripts.data_api import DataAPI
                rt = DataAPI.get_realtime([code])
                if rt:
                    for k, v in rt.items():
                        close_price = v['price']
                        break
            except:
                close_price = 0
        
        if close_price and close_price > 0:
            # 鎸夊彲鐢ㄨ祫閲戠殑20%涔板叆锛堢暀鍑轰綑鍦帮級
            target_amount = min(account.capital * 0.20, 
                              account.total_assets() * 0.25)
            shares = max(int(target_amount / close_price / 100) * 100, 100)
            
            if dry_run:
                cost = shares * close_price
                print(f'  [妯℃嫙] 涔板叆 {code} {best["name"]}: {shares}鑲?@ {close_price:.2f}鍏?(鎴愭湰{cost:,.0f}鍏?')
            else:
                result = account.buy(code, best['name'], close_price, shares, 
                                    f"ML:{best.get('ml_prob', 0):.0%} 璇勫垎:{best.get('score', 0):.1f} {best.get('sentiment_keywords', '')}")
                if result['success']:
                    print(f'  鉁?涔板叆 {code} {best["name"]}: {result["shares"]}鑲?@ {close_price:.2f}鍏?)
                    print(f'     鎴愭湰: {result["cost"]:,.0f}鍏?)
                else:
                    print(f'  鉂?涔板叆澶辫触: {result["reason"]}')
    
    # 5. 鎵撳嵃鐘舵€?    print(f'\n{'='*60}')
    account.print_status(date)
    print(f'\n鎬讳氦鏄撴暟: {account.stats["total_trades"]} 鑳滅巼: {account.stats["win_rate"]*100:.1f}%')
    
    # 6. 淇濆瓨鏃ュ織
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
    
    print(f'\n鏃ュ織宸蹭繚瀛? {log_path}')
    return account


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--capital', type=int, default=100000)
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--dry-run', action='store_true', help='鍙嚭鎶ュ憡涓嶆墽琛?)
    args = parser.parse_args()
    
    run_sim_trade(date=args.date, capital=args.capital, dry_run=args.dry_run)

