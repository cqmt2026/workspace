# -*- coding: utf-8 -*-
"""
反前瞻偏误工具 - Anti-Look-Ahead Bias Utilities
源自 HKU DS / AI-Trader 数据管道设计
功能: 对日线数据的最新日期进行掩码，防止未来数据泄露到回测中
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

# ==================== 核心掩码函数 ====================

def mask_latest_date(data: Dict) -> Dict:
    """
    对单股票日线数据做反前瞻掩码。
    最新日期只保留买入价，卖出价字段被物理删除。
    
    Args:
        data: 原始数据字典，支持以下格式:
            格式1: {"Time Series Daily": {"2026-05-07": {"1. open": x, "4. close": y}, ...}}
            格式2: {"klines": [{"date": "2026-05-07", "open": x, "close": y}, ...]}
            格式3: 东财格式 {"data": {"klines": ["2026-05-07,open,high,low,close,vol"]}}
            
    Returns:
        处理后的数据（latest_date 只有 buy price，无 sell price）
    """
    if not data or not isinstance(data, dict):
        return data
    
    # 格式1: Alpha Vantage 风格 (Time Series)
    for key in ['Time Series Daily', 'Time Series (Daily)', 'daily']:
        if key in data and isinstance(data[key], dict):
            return _mask_alpha_vantage_style(data, key)
    
    # 格式2: 扁平化列表风格 [{"date": ..., "open": ..., "close": ...}]
    if 'klines' in data and isinstance(data['klines'], list):
        return _mask_klines_style(data)
    
    # 格式3: 东财 push2his 格式 ["2026-05-07,open,high,low,close,vol", ...]
    if 'data' in data and isinstance(data.get('data'), dict):
        klines = data['data'].get('klines', [])
        if klines and isinstance(klines[0], str) and ',' in str(klines[0]):
            return _mask_dongfu_style(data)
    
    return data


def _mask_alpha_vantage_style(data: Dict, series_key: str) -> Dict:
    """处理 Alpha Vantage 风格的 Time Series 格式"""
    series = data[series_key]
    if not isinstance(series, dict) or not series:
        return data
    
    # 找最新日期
    dates = []
    for d in series.keys():
        try:
            dates.append((d, datetime.strptime(d[:10], '%Y-%m-%d')))
        except:
            pass
    
    if not dates:
        return data
    
    latest_date_str = max(dates, key=lambda x: x[1])[0]
    latest_bar = series.get(latest_date_str, {})
    
    if isinstance(latest_bar, dict):
        # 保留买入价，删除卖出价
        buy_price = latest_bar.get("1. buy price") or latest_bar.get("1. open")
        if buy_price is not None:
            series[latest_date_str] = {"1. buy price": buy_price}
        else:
            series[latest_date_str] = {}
    
    return data


def _mask_klines_style(data: Dict) -> Dict:
    """处理扁平列表风格 klines"""
    klines = data['klines']
    if not klines:
        return data
    
    # 找最新日期那条
    valid_klines = []
    for kl in klines:
        if isinstance(kl, dict) and 'date' in kl:
            try:
                dt = datetime.strptime(str(kl['date'])[:10], '%Y-%m-%d')
                valid_klines.append((kl, dt))
            except:
                pass
    
    if not valid_klines:
        return data
    
    latest_kl, _ = max(valid_klines, key=lambda x: x[1])
    idx = klines.index(latest_kl)
    
    # 掩码：只保留 open，删除 close
    new_latest = dict(latest_kl)
    new_latest.pop('close', None)
    new_latest['close'] = None  # 显式置空，不能用None，会被当字段存在
    # 用一个特殊标记表示已掩码
    new_latest['_masked'] = True
    klines[idx] = new_latest
    
    return data


def _mask_dongfu_style(data: Dict) -> Dict:
    """处理东财 push2his 格式"""
    klines = data['data'].get('klines', [])
    if not klines:
        return data
    
    # 解析所有日期
    parsed = []
    for i, kl in enumerate(klines):
        parts = str(kl).split(',')
        if len(parts) >= 6:
            try:
                dt = datetime.strptime(parts[0], '%Y-%m-%d')
                parsed.append((i, dt, parts))
            except:
                pass
    
    if not parsed:
        return data
    
    # 掩码最新日期
    latest_idx, _, latest_parts = max(parsed, key=lambda x: x[1])
    # 只保留 open, high, low，删除/置空 close
    masked_line = f"{latest_parts[0]},{latest_parts[1]},{latest_parts[2]},{latest_parts[3]},,,{latest_parts[5]}"
    klines[latest_idx] = masked_line
    
    return data


def mask_latest_date_jsonl(file_path: Union[str, Path]) -> bool:
    """
    直接对 JSONL 文件进行反前瞻掩码处理。
    逐行读取，逐行掩码，逐行写回。
    
    Args:
        file_path: JSONL 文件路径
        
    Returns:
        True: 成功，False: 失败
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"文件不存在: {path}")
        return False
    
    temp_path = path.with_suffix('.jsonl.tmp')
    
    try:
        with open(path, 'r', encoding='utf-8') as fin, \
             open(temp_path, 'w', encoding='utf-8') as fout:
            
            line_count = 0
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    masked = mask_latest_date(data)
                    fout.write(json.dumps(masked, ensure_ascii=False) + '\n')
                    line_count += 1
                except json.JSONDecodeError as e:
                    logger.warning(f"跳过无效JSON行 {line_count}: {e}")
                    continue
        
        # 替换原文件
        temp_path.replace(path)
        logger.info(f"掩码完成，共处理 {line_count} 条记录")
        return True
        
    except Exception as e:
        logger.error(f"掩码失败: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False


# ==================== 验证函数 ====================

def validate_no_lookahead(data: Dict) -> Dict:
    """
    验证数据是否已正确掩码（无前瞻偏误）。
    
    Returns:
        {"valid": True/False, "latest_date": "...", "latest_bar": {...}, "issue": "..."}
    """
    result = {"valid": True, "latest_date": None, "latest_bar": {}, "issue": None}
    
    # 找 Time Series
    for key in ['Time Series Daily', 'Time Series (Daily)', 'daily']:
        if key in data and isinstance(data[key], dict):
            series = data[key]
            dates = []
            for d in series.keys():
                try:
                    dates.append((d, datetime.strptime(d[:10], '%Y-%m-%d')))
                except:
                    pass
            
            if dates:
                latest_date_str = max(dates, key=lambda x: x[1])[0]
                latest_bar = series.get(latest_date_str, {})
                
                result["latest_date"] = latest_date_str
                result["latest_bar"] = latest_bar
                
                # 检查最新日期是否有 sell price
                has_sell = '4. sell price' in latest_bar or '4. close' in latest_bar
                if has_sell:
                    result["valid"] = False
                    result["issue"] = f"最新日期 {latest_date_str} 存在卖出价字段，存在前瞻偏误"
                break
    
    # 检查 klines 列表
    if 'klines' in data and isinstance(data['klines'], list):
        klines = data['klines']
        valid_klines = []
        for kl in klines:
            if isinstance(kl, dict) and 'date' in kl:
                try:
                    dt = datetime.strptime(str(kl['date'])[:10], '%Y-%m-%d')
                    valid_klines.append((kl, dt))
                except:
                    pass
        
        if valid_klines:
            latest_kl, _ = max(valid_klines, key=lambda x: x[1])
            result["latest_date"] = str(latest_kl.get('date', ''))
            
            if latest_kl.get('_masked'):
                # 已掩码，检查 close 是否为空
                if latest_kl.get('close') is not None and latest_kl.get('close') != '':
                    result["valid"] = False
                    result["issue"] = f"最新日期 {latest_kl['date']} 的 close 未被掩码"
    
    return result


def validate_jsonl_file(file_path: Union[str, Path], max_lines: int = 100) -> Dict:
    """
    验证 JSONL 文件是否无前瞻偏误。
    
    Args:
        file_path: JSONL 文件路径
        max_lines: 最多检查前多少行（-1 表示全部）
        
    Returns:
        验证结果字典
    """
    path = Path(file_path)
    if not path.exists():
        return {"valid": False, "error": "文件不存在"}
    
    result = {
        "valid": True,
        "total_lines": 0,
        "checked_lines": 0,
        "issues": [],
        "latest_dates": []
    }
    
    try:
        with open(path, 'r', encoding='utf-8') as fin:
            for i, line in enumerate(fin):
                if max_lines > 0 and i >= max_lines:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                result["total_lines"] += 1
                
                try:
                    data = json.loads(line)
                    val = validate_no_lookahead(data)
                    
                    if not val["valid"]:
                        result["valid"] = False
                        result["issues"].append(val["issue"])
                    
                    if val["latest_date"]:
                        result["latest_dates"].append(val["latest_date"])
                    
                    result["checked_lines"] += 1
                    
                except json.JSONDecodeError:
                    result["issues"].append(f"行 {i+1}: 无效JSON")
                    result["valid"] = False
        
        return result
        
    except Exception as e:
        return {"valid": False, "error": str(e)}


# ==================== 批量工具 ====================

def batch_mask_directory(dir_path: Union[str, Path], pattern: str = "*.json") -> int:
    """
    批量处理目录下所有符合模式的 JSON 文件。
    
    Args:
        dir_path: 目录路径
        pattern: 文件匹配模式，如 "*.json" 或 "*.jsonl"
        
    Returns:
        成功处理的文件数量
    """
    path = Path(dir_path)
    if not path.exists():
        logger.error(f"目录不存在: {path}")
        return 0
    
    files = list(path.glob(pattern))
    success_count = 0
    
    for f in files:
        if f.suffix == '.jsonl':
            if mask_latest_date_jsonl(f):
                success_count += 1
        elif f.suffix == '.json':
            try:
                with open(f, 'r', encoding='utf-8') as fin:
                    data = json.load(fin)
                masked = mask_latest_date(data)
                with open(f, 'w', encoding='utf-8') as fout:
                    json.dump(masked, fout, ensure_ascii=False)
                success_count += 1
            except Exception as e:
                logger.warning(f"处理失败 {f.name}: {e}")
    
    logger.info(f"批量掩码完成，成功 {success_count}/{len(files)} 个文件")
    return success_count


# ==================== 回测引擎集成 ====================

def check_data_before_backtest(df) -> Dict:
    """
    在回测前检查数据是否有前瞻偏误问题。
    返回检查结果和建议。
    
    Args:
        df: pandas DataFrame，包含 'close' 列
        
    Returns:
        检查结果字典
    """
    result = {
        "has_lookahead": False,
        "latest_date": None,
        "today_close": None,
        "warning": None
    }
    
    if df is None or df.empty:
        result["warning"] = "数据为空"
        return result
    
    latest_date = df.index.max()
    today_close = df.iloc[-1]['close']
    
    result["latest_date"] = str(latest_date)[:10]
    result["today_close"] = today_close
    
    # 简单检查：如果最新收盘价明显高于前日，可能是当天盘中已有数据
    if len(df) >= 2:
        prev_close = df.iloc[-2]['close']
        change_pct = (today_close - prev_close) / prev_close * 100 if prev_close else 0
        if abs(change_pct) > 9.5:  # 涨跌停范围内算正常
            pass
        elif change_pct > 0 and today_close > prev_close * 1.02:
            result["has_lookahead"] = True
            result["warning"] = f"最新日期 {latest_date} 的收盘价可能包含盘中数据（非当日收盘），存在前瞻风险"
    
    return result


# ==================== CLI 入口 ====================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='反前瞻偏误工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # mask 子命令
    mask_parser = subparsers.add_parser('mask', help='掩码单个文件')
    mask_parser.add_argument('file', help='文件路径')
    
    # validate 子命令
    val_parser = subparsers.add_parser('validate', help='验证文件')
    val_parser.add_argument('file', help='文件路径')
    val_parser.add_argument('--max', type=int, default=100, help='最多检查行数')
    
    # batch 子命令
    batch_parser = subparsers.add_parser('batch', help='批量处理目录')
    batch_parser.add_argument('dir', help='目录路径')
    batch_parser.add_argument('--pattern', default='*.json', help='文件模式')
    
    args = parser.parse_args()
    
    if args.command == 'mask':
        ok = mask_latest_date_jsonl(args.file)
        print(f"掩码完成: {'成功' if ok else '失败'}")
    elif args.command == 'validate':
        result = validate_jsonl_file(args.file, args.max)
        print(f"验证结果: {'通过' if result['valid'] else '失败'}")
        if result.get('issues'):
            for iss in result['issues'][:5]:
                print(f"  - {iss}")
    elif args.command == 'batch':
        cnt = batch_mask_directory(args.dir, args.pattern)
        print(f"批量处理完成: {cnt} 个文件")
    else:
        parser.print_help()