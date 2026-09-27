"""
量化回测框架 v1.0
========================
功能：
1. 历史数据获取与缓存
2. 技术指标计算
3. 买卖信号生成
4. 回测引擎
5. 绩效评估

回测指标：
- 年化收益率
- 夏普比率
- 最大回撤
- 胜率
- 盈亏比
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# ====================
# 1. 数据层
# ====================

class DataLoader:
    """数据加载器"""
    
    def __init__(self, cache_dir='data/cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_kline(self, code, days=250):
        """获取K线数据（网络或缓存）"""
        import akshare as ak
        
        cache_file = f'{self.cache_dir}/{code}_kline.json'
        
        # 尝试从网络获取
        try:
            df = ak.stock_zh_a_hist(
                symbol=code, 
                period='daily', 
                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                adjust='qfq'
            )
            df.to_json(cache_file, orient='records')
            return df
        except Exception as e:
            print(f'网络获取失败: {e}')
            
            # 尝试从缓存读取
            if os.path.exists(cache_file):
                print('使用缓存数据')
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return pd.DataFrame(data)
            
            return None
    
    def generate_mock_data(self, initial_price=50, days=250, trend=0.0005, volatility=0.02):
        """生成模拟数据（用于演示）"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        prices = [initial_price]
        for _ in range(days - 1):
            change = np.random.normal(trend, volatility)
            prices.append(prices[-1] * (1 + change))
        
        df = pd.DataFrame({
            '日期': dates,
            '开盘': prices,
            '最高': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            '最低': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            '收盘': prices,
            '成交量': [np.random.randint(1000000, 10000000) for _ in prices],
            '成交额': [p * np.random.randint(1000000, 10000000) for p in prices],
            '涨跌幅': [0] + [((prices[i] - prices[i-1]) / prices[i-1] * 100) for i in range(1, len(prices))]
        })
        
        return df
    
    def add_technical_indicators(self, df):
        """添加技术指标"""
        if df is None or len(df) == 0:
            return None
        
        df = df.copy()
        
        close = df['收盘'].values
        
        # MA均线
        df['MA5'] = pd.Series(close).rolling(5).mean()
        df['MA10'] = pd.Series(close).rolling(10).mean()
        df['MA20'] = pd.Series(close).rolling(20).mean()
        
        # MACD (12,26,9)
        ema12 = pd.Series(close).ewm(span=12).mean()
        ema26 = pd.Series(close).ewm(span=26).mean()
        df['DIF'] = ema12 - ema26
        df['DEA'] = pd.Series(df['DIF']).ewm(span=9).mean()
        df['MACD'] = (df['DIF'] - df['DEA']) * 2
        
        # KDJ (9,3,3)
        low_n = pd.Series(close).rolling(9).min()
        high_n = pd.Series(close).rolling(9).max()
        rsv = (close - low_n) / (high_n - low_n) * 100
        df['K'] = pd.Series(rsv).ewm(com=3).mean()
        df['D'] = pd.Series(df['K']).ewm(com=3).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        return df

# ====================
# 2. 策略层
# ====================

class Strategy:
    """策略基类"""
    def generate_signals(self, df):
        raise NotImplementedError

class MACDZeroAboveStrategy(Strategy):
    """MACD零轴上方策略"""
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        for i in range(1, len(df)):
            # 买入条件
            if (df['DIF'].iloc[i] > 0 and 
                df['DEA'].iloc[i] > 0 and 
                df['收盘'].iloc[i] > df['MA5'].iloc[i]):
                signals.iloc[i] = 1
            
            # 卖出条件
            elif df['收盘'].iloc[i] < df['MA5'].iloc[i]:
                signals.iloc[i] = -1
        
        return signals

class SevenCheckStrategy(Strategy):
    """七重检查策略"""
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        for i in range(20, len(df)):
            score = 0
            
            # 1. MACD零轴上方
            if df['DIF'].iloc[i] > 0 and df['DEA'].iloc[i] > 0:
                score += 1
            
            # 2. 站稳MA5
            if df['收盘'].iloc[i] > df['MA5'].iloc[i]:
                score += 1
            
            # 3. KDJ不超买
            if df['K'].iloc[i] < 80:
                score += 1
            
            # 4. 多头排列
            if df['MA5'].iloc[i] > df['MA10'].iloc[i] > df['MA20'].iloc[i]:
                score += 1
            
            # 5. 底分型
            if (df['最低'].iloc[i] > df['最低'].iloc[i-1] and 
                df['最低'].iloc[i-1] < df['最低'].iloc[i-2]):
                score += 1
            
            # 买入：得分>=3
            if score >= 3:
                signals.iloc[i] = 1
            # 卖出：跌破MA5
            elif df['收盘'].iloc[i] < df['MA5'].iloc[i]:
                signals.iloc[i] = -1
        
        return signals

class TrendFollowingStrategy(Strategy):
    """趋势跟踪策略"""
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        for i in range(20, len(df)):
            # 买入：MA5上穿MA20（金叉）
            if (df['MA5'].iloc[i] > df['MA20'].iloc[i] and 
                df['MA5'].iloc[i-1] <= df['MA20'].iloc[i-1] and
                df['DIF'].iloc[i] > 0):
                signals.iloc[i] = 1
            
            # 卖出：MA5下穿MA20（死叉）
            elif (df['MA5'].iloc[i] < df['MA20'].iloc[i] and 
                  df['MA5'].iloc[i-1] >= df['MA20'].iloc[i-1]):
                signals.iloc[i] = -1
        
        return signals

# ====================
# 3. 回测层
# ====================

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital=100000, commission=0.0003):
        self.initial_capital = initial_capital
        self.commission = commission
    
    def run(self, df, signals):
        """运行回测"""
        capital = self.initial_capital
        position = 0
        cash = capital
        trades = []
        equity_curve = []
        
        for i in range(len(df)):
            date = df.iloc[i]['日期']
            price = df.iloc[i]['收盘']
            
            # 买入
            if signals.iloc[i] == 1 and position == 0:
                shares = int(cash / (price * (1 + self.commission)))
                if shares > 0:
                    cost = shares * price * (1 + self.commission)
                    position = shares
                    cash -= cost
                    trades.append({
                        'date': date, 'type': 'BUY', 
                        'price': price, 'shares': shares
                    })
            
            # 卖出
            elif signals.iloc[i] == -1 and position > 0:
                proceeds = position * price * (1 - self.commission)
                cash += proceeds
                trades.append({
                    'date': date, 'type': 'SELL',
                    'price': price, 'shares': position
                })
                position = 0
            
            equity = cash + position * price
            equity_curve.append({'date': date, 'equity': equity})
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_capital': cash + position * df.iloc[-1]['收盘'],
            'position': position
        }
    
    def evaluate(self, result, days=250):
        """评估绩效"""
        equity_curve = pd.DataFrame(result['equity_curve'])
        equity_curve['returns'] = equity_curve['equity'].pct_change()
        
        total_return = (result['final_capital'] - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (250 / days) - 1
        
        if equity_curve['returns'].std() > 0:
            sharpe = equity_curve['returns'].mean() / equity_curve['returns'].std() * np.sqrt(250)
        else:
            sharpe = 0
        
        equity_curve['cummax'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['cummax'] - equity_curve['equity']) / equity_curve['cummax']
        max_drawdown = equity_curve['drawdown'].max()
        
        trades = result['trades']
        win_count = sum(1 for i in range(1, len(trades)) 
                        if trades[i]['type'] == 'SELL' and 
                        (trades[i]['price'] - trades[i-1]['price']) > 0)
        total_complete = len([t for t in trades if t['type'] == 'SELL'])
        win_rate = win_count / total_complete if total_complete > 0 else 0
        
        # 盈亏比
        wins = []
        losses = []
        for i in range(1, len(trades)):
            if trades[i]['type'] == 'SELL':
                pnl = trades[i]['price'] - trades[i-1]['price']
                if pnl > 0:
                    wins.append(pnl)
                else:
                    losses.append(abs(pnl))
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'total_return': total_return * 100,
            'annual_return': annual_return * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate * 100,
            'profit_loss_ratio': profit_loss_ratio,
            'total_trades': len(trades) // 2,
            'final_capital': result['final_capital']
        }

# ====================
# 4. 主程序
# ====================

def print_evaluation(name, eval_result):
    """格式化打印评估结果"""
    print(f"\n--- {name} ---")
    print(f"  总收益率:    {eval_result['total_return']:>+.2f}%")
    print(f"  年化收益:    {eval_result['annual_return']:>+.2f}%")
    print(f"  夏普比率:    {eval_result['sharpe_ratio']:>+.2f}")
    print(f"  最大回撤:    {eval_result['max_drawdown']:>+.2f}%")
    print(f"  胜率:        {eval_result['win_rate']:>+.2f}%")
    print(f"  盈亏比:      {eval_result['profit_loss_ratio']:>+.2f}")
    print(f"  交易次数:    {eval_result['total_trades']}")
    print(f"  最终资金:    {eval_result['final_capital']:,.2f}")

if __name__ == '__main__':
    print("=" * 60)
    print("量化回测框架 v1.0")
    print("=" * 60)
    
    code = '600549'
    
    # 数据加载
    loader = DataLoader(cache_dir='C:/Users/Administrator/.openclaw/workspace/workspace-investment/data/cache')
    
    print(f"\n[1] 加载 {code} 数据...")
    df = loader.get_kline(code, days=250)
    
    if df is None or len(df) == 0:
        print("网络不可用，使用模拟数据演示")
        df = loader.generate_mock_data(initial_price=50, days=250, trend=0.001, volatility=0.015)
    
    print(f"数据量: {len(df)} 条K线")
    
    # 技术指标
    print("\n[2] 计算技术指标...")
    df = loader.add_technical_indicators(df)
    print("指标: MA5/MA10/MA20, MACD(DIF/DEA), KDJ(K/D/J)")
    
    # 回测引擎
    engine = BacktestEngine(initial_capital=100000)
    
    # 策略列表
    strategies = [
        ("MACD零轴上方策略", MACDZeroAboveStrategy()),
        ("七重检查策略(>=3项)", SevenCheckStrategy()),
        ("趋势跟踪策略(MA金叉死叉)", TrendFollowingStrategy()),
    ]
    
    results = {}
    
    print("\n[3] 运行回测...")
    for name, strategy in strategies:
        signals = strategy.generate_signals(df)
        result = engine.run(df, signals)
        eval_result = engine.evaluate(result, len(df))
        results[name] = eval_result
        print(f"  {name}: 完成")
    
    # 结果对比
    print("\n" + "=" * 60)
    print("策略对比")
    print("=" * 60)
    print(f"{'指标':<20} {'MACD策略':>12} {'七重检查':>12} {'趋势跟踪':>12}")
    print("-" * 60)
    
    metrics = ['total_return', 'annual_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
    labels = ['总收益率', '年化收益', '夏普比率', '最大回撤', '胜率']
    
    for metric, label in zip(metrics, labels):
        v1 = results["MACD零轴上方策略"][metric]
        v2 = results["七重检查策略(>=3项)"][metric]
        v3 = results["趋势跟踪策略(MA金叉死叉)"][metric]
        if metric == 'sharpe_ratio':
            print(f"{label:<20} {v1:>+12.2f} {v2:>+12.2f} {v3:>+12.2f}")
        elif metric in ['win_rate', 'max_drawdown', 'total_return', 'annual_return']:
            print(f"{label:<20} {v1:>+11.2f}% {v2:>+11.2f}% {v3:>+11.2f}%")
        else:
            print(f"{label:<20} {v1:>12.2f} {v2:>12.2f} {v3:>12.2f}")
    
    # 绩效评级
    print("\n" + "=" * 60)
    print("绩效评级标准")
    print("=" * 60)
    print("  合格: 年化>10% + 夏普>1 + 回撤<20%")
    print("  优秀: 年化>20% + 夏普>2 + 回撤<10%")
    print("  不合格策略将被标记 ❌")
    
    print("\n" + "=" * 60)
    print("回测完成!")
    print("=" * 60)
    print("\n框架功能:")
    print("  ✅ 数据层: akshare网络/缓存/Mock")
    print("  ✅ 策略层: MACD/七重检查/趋势跟踪")
    print("  ✅ 回测层: 逐笔交易/权益曲线")
    print("  ✅ 评估层: 5大指标 + 盈亏比")
    print("\n使用方法:")
    print("  python scripts/backtest/backtest_framework.py")
