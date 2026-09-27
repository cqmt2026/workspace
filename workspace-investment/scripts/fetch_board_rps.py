# -*- coding: utf-8 -*-
"""
板RPS数据采集
每天16:10运行
1. 从akshare获取90个申万行业板块的收盘价
2. 计算各周期RPS（5/10/20/60日）
3. 保存到out_data/rps_history/
   RPS_board_YYYYMMDD.json 格式
"""
import io
import sys, os, json, time, signal
from datetime import datetime, date, timedelta
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# AkShare单次请求超时（秒）
AKSHARE_TIMEOUT = 30

class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError('AkShare请求超时')

def ak_get_with_timeout(func, *args, **kwargs):
    """带超时的AkShare调用"""
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(AKSHARE_TIMEOUT)
    try:
        result = func(*args, **kwargs)
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        return result
    except TimeoutError:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        raise
    except Exception as e:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        raise e

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
HIST_DIR = os.path.join(WORK_DIR, 'out_data', 'rps_history')
os.makedirs(HIST_DIR, exist_ok=True)

today_str = date.today().strftime('%Y%m%d')
today_fmt = date.today().strftime('%Y-%m-%d')
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')


def get_board_list():
    """获取90个申万行业板块"""
    import akshare as ak
    import time
    for retry in range(3):
        try:
            df = ak_get_with_timeout(ak.stock_board_industry_name_ths)
            if df is not None and len(df) > 0:
                print(f"  申万行业板块: {len(df)}个")
                return [(row['code'], row['name']) for _, row in df.iterrows()]
        except Exception:
            if retry < 2:
                print(f"  [重试{retry+1}] akshare失败，5秒后重试...")
                time.sleep(5)
            else:
                print(f"  [失败] akshare 3次重试均失败")
                return []
    return []


def calc_return(series, periods):
    """计算多周期收益率，返回dict {period: return}"""
    result = {}
    for p in periods:
        if len(series) > p:
            result[p] = (series[-1] - series[-1-p]) / series[-1-p] * 100
        else:
            result[p] = 0.0
    return result


def main():
    print("=" * 60)
    print(f"申万板块RPS采集 {timestamp}")
    print("=" * 60)

    print("[1/3] 获取板块列表...")
    boards = get_board_list()
    if not boards:
        print("  失败，退出")
        return

    import akshare as ak

    # 回退日期（最多90天）
    end = date.today()
    start = end - timedelta(days=90)
    start_str = start.strftime('%Y%m%d')
    end_str = end.strftime('%Y%m%d')

    all_board_data = []
    total = len(boards)
    errors = 0

    print(f"[2/3] 获取板块历史数据 (回退90天)...")
    for i, (code, name) in enumerate(boards):
        try:
            df = ak_get_with_timeout(ak.stock_board_industry_index_ths, symbol=name, start_date=start_str, end_date=end_str)
            if df is None or df.empty:
                errors += 1
                continue

            # 解析收盘价
            closes = df['收盘价'].values
            rets = calc_return(closes, [5, 10, 20, 60])

            # 最近一日涨跌幅
            if len(closes) >= 2:
                chg_pct = (closes[-1] - closes[-2]) / closes[-2] * 100
            else:
                chg_pct = 0.0

            all_board_data.append({
                'code': code,
                'name': name,
                'close': float(closes[-1]),
                'change_pct': round(chg_pct, 2),
                'returns': {str(k): round(v, 2) for k, v in rets.items()},
            })

            if (i+1) % 30 == 0 or i == total - 1:
                print(f"  进度: {i+1}/{total}, 成功{len(all_board_data)}, 失败{errors}")
            time.sleep(0.5)  # 限速

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  [WARN] {name}({code}): {e}")
            time.sleep(1)

    print(f"  完成: 成功{len(all_board_data)}/{total}, 失败{errors}")

    if not all_board_data:
        print("无数据，退出")
        return

    # RPS计算（对每个周期分别算）
    print("[3/3] 计算RPS...")
    periods = [5, 10, 20, 60]
    for p in periods:
        key = str(p)
        sorted_data = sorted(all_board_data, key=lambda x: x['returns'].get(key, 0), reverse=True)
        n = len(sorted_data)
        for idx, item in enumerate(sorted_data):
            rps = round((1 - idx / n) * 100, 1)
            item[f'rps_{p}d'] = rps

    # 统一输出格式
    out_boards = []
    for item in all_board_data:
        out_boards.append({
            'board_code': item['code'],
            'name': item['name'],
            'close': item['close'],
            'change_pct': item['change_pct'],
            'returns': item['returns'],
            'rps_5d': item['rps_5d'],
            'rps_10d': item['rps_10d'],
            'rps_20d': item['rps_20d'],
            'rps_60d': item['rps_60d'],
        })

    out = {
        'date': today_str,
        'timestamp': timestamp,
        'total': len(out_boards),
        'source': 'ths',
        'rps_data': out_boards,
    }
    out_file = os.path.join(HIST_DIR, f"RPS_board_{today_str}.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {out_file} ({len(all_board_data)}个板块)")

    # 摘要
    print(f"\n--- RPS5 TOP10 ---")
    sorted_rps5 = sorted(all_board_data, key=lambda x: x.get('rps_5d', 0), reverse=True)
    for item in sorted_rps5[:10]:
        print(f"  {item['name']:<10} RPS5={item['rps_5d']:>5.1f} 涨幅={item['returns'].get('5', 0):>6.2f}%")
    print(f"\n--- RPS5 BOTTOM5 ---")
    for item in sorted_rps5[-5:]:
        print(f"  {item['name']:<10} RPS5={item['rps_5d']:>5.1f} 涨幅={item['returns'].get('5', 0):>6.2f}%")
    print("=" * 60)


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()