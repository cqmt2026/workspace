# -*- coding: utf-8 -*-
"""
Pipeline: 三步串联主流程
========================
板块RPS筛选 → 资金流入验证 → 动量确认

输出候选股列表，每只附上：
  - 所属板块 + 板块RPS
  - 资金流向（主力净流入）
  - 动量指标（MA/涨幅/量比）
  - 建议止损位

不修改现有系统。
"""
import sys, json, os
from datetime import date
sys.stdout.reconfigure(encoding='utf-8')

from step1_sector_filter import run as step1_run
from step2_volume_price import verify_candidates as verify_money
from step3_momentum_confirm import check_momentum

def run_pipeline(rps_threshold=70, top_n=20, verbose=True):
    """执行完整三步流程"""
    if verbose:
        print("=" * 60)
        print("三步筛选流程")
        print("板块RPS → 资金流入 → 动量确认")
        print("=" * 60)
    
    # Step 1: 板块RPS筛选
    step1 = step1_run(rps_threshold=rps_threshold, top_sectors=top_n, verbose=verbose)
    if not step1 or not step1['candidates']:
        if verbose: print("[Pipeline] Step1 无候选")
        return []
    
    candidates = step1['candidates'][:200]  # 最多查200只（RPS排序的前200）
    if verbose:
        print(f"\n[Pipeline] Step1: {step1['total_unique']}只候选 -> Step2")
    
    # Step 2: 量价资金强度验证（替代东财API资金流）
    passed2, _ = verify_money(candidates, verbose=verbose)
    if not passed2:
        if verbose: print("[Pipeline] Step2 无候选")
        return []
    
    if verbose:
        print(f"\n[Pipeline] Step2: {len(passed2)}只通过 -> Step3")
    
    # Step 3: 动量确认
    passed3, _ = check_momentum(passed2, verbose=verbose)
    
    if verbose:
        print(f"\n[Pipeline] Step3: {len(passed3)}只最终候选")
    
    # 格式化输出
    result = []
    for c in passed3:
        vp = c.get('vp_data', {})
        result.append({
            'code': c['code'],
            'name': c.get('name', '?'),
            'sector': c.get('sector', '?'),
            'sector_rps': c.get('sector_rps', 0),
            'chg_pct': vp.get('chg_pct', 0),
            'vol_ratio': vp.get('vol_ratio', 0),
            'ma5': vp.get('ma5', 0),
            'ma10': vp.get('ma10', 0),
            'ma20': vp.get('ma20', 0),
            'reason': f"板块RPS{c.get('sector_rps',0):.0f}+MA多头+放量{vp.get('vol_ratio',0):.2f}+涨幅{vp.get('chg_pct',0):+.1f}%"
        })
    
    if verbose and result:
        print("\n" + "=" * 60)
        print("最终候选股")
        print("=" * 60)
        print(f"{'名称':10s} {'代码':10s} {'板块':15s} {'RPS':>5} {'涨幅':>7} {'量比':>5}")
        print("-" * 52)
        for c in result:
            name = c['name'][:8]
            code = c['code'][-6:]
            sector = c['sector'][:12]
            rps = c['sector_rps']
            chg = c['chg_pct']
            vr = c['vol_ratio']
            print(f"{name:10s} {code:10s} {sector:15s} {rps:5.0f} {chg:>+6.1f}% {vr:>5.2f}")
    
    # 保存结果
    today = date.today().isoformat()
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'out_data', 'experimental')
    os.makedirs(out_dir, exist_ok=True)
    
    out_file = os.path.join(out_dir, f'pipeline_result_{today}.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': today,
            'rps_threshold': rps_threshold,
            'total_candidates': len(result),
            'candidates': result,
        }, f, ensure_ascii=False, indent=2)
    
    if verbose:
        print(f"\n[Pipeline] 结果已保存: {out_file}")
    
    # 自动记录到推荐追踪系统
    if result:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
            from recommendation_tracker import init_tracker, record_recommendation, save_tracker, TRACK_FILE
            # 确保tracker文件存在
            tracker_path = os.path.join(os.path.dirname(__file__), '..', TRACK_FILE)
            if not os.path.exists(tracker_path):
                os.makedirs(os.path.dirname(tracker_path), exist_ok=True)
                init_tracker()
            for c in result:
                record_recommendation(
                    source='pipeline_v1',
                    code=c['code'],
                    name=c['name'],
                    price=c.get('close', c.get('ma5', None)),
                    reason=c['reason']
                )
            if verbose:
                print(f"[Pipeline] {len(result)}只候选已记录到推荐追踪系统")
        except Exception as e:
            if verbose:
                print(f"[Pipeline] 推荐记录失败: {e}")
    
    return result

if __name__ == '__main__':
    result = run_pipeline()
    print(f"\n[Pipeline] 完成: {len(result)}只最终候选")