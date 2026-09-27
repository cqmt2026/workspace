"""
微信小程序知识库定时更新脚本
功能：
1. 尝试抓取微信官方更新日志
2. 检查知识库是否缺少重要章节
3. 汇总结果写入日志
"""
import io
import os
import sys
from datetime import datetime

# 确保 UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-weixin'
KNOWLEDGE_BASE = os.path.join(WORKSPACE, 'knowledge')


def check_doc_completeness():
    """检查知识库完整性"""
    required_files = {
        '01-最新特性/A1-2024-2025新增API.md': '方向A核心文档',
        '02-组件深度/B1-自定义组件内部机制.md': 'Canvas/node()核心',
        '02-组件深度/B2-Behavior复用.md': 'Behavior复用',
        '02-组件深度/B5-生命周期.md': '生命周期',
        '03-踩坑记录/C1-高频踩坑整理.md': '高频踩坑',
        '03-踩坑记录/C3-云开发踩坑.md': '云开发踩坑',
        '04-性能优化/D1-长列表优化.md': '长列表优化',
    }

    missing = []
    for rel_path, desc in required_files.items():
        full_path = os.path.join(KNOWLEDGE_BASE, rel_path)
        if not os.path.exists(full_path):
            missing.append(f'  ❌ {rel_path} ({desc})')
        else:
            size = os.path.getsize(full_path)
            print(f'  ✅ {rel_path} ({desc}) - {size}B')

    return missing


def log_result(missing, note=''):
    """写入日志"""
    log_dir = os.path.join(WORKSPACE, 'memory', 'L1-日志')
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{today}.md')

    content = f"""# L1日志 - {today}

## 知识库自动检查
时间: {datetime.now().strftime('%H:%M:%S')}

### 完整性检查
"""
    if missing:
        content += '\n'.join(missing) + '\n'
    else:
        content += '  ✅ 所有核心文档完整\n'

    if note:
        content += f'\n### 备注\n{note}\n'

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(content + '\n\n')

    return log_file


def fetch_wechat_updates():
    """
    尝试抓取微信官方更新日志
    由于外部搜索受限，主要依赖 web_fetch
    """
    try:
        from scripts.cn_io import web_fetch_with_fallback
    except ImportError:
        web_fetch_with_fallback = None

    sources = [
        'https://developers.weixin.qq.com/miniprogram/dev/framework/release.html',
    ]

    results = []
    for url in sources:
        try:
            # 直接用 urllib
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            r = urllib.request.urlopen(req, timeout=8)
            html = r.read().decode('utf-8', errors='ignore')
            if r.status == 200 and len(html) > 1000:
                results.append(f'  ✅ {url} - {len(html)}B')
            else:
                results.append(f'  ⚠️ {url} - 内容过短({len(html)}B)')
        except Exception as e:
            results.append(f'  ❌ {url} - {e}')

    return results


def main():
    print('[知识库定时检查] 开始...')

    # 1. 检查完整性
    missing = check_doc_completeness()

    # 2. 尝试抓取更新
    try:
        updates = fetch_wechat_updates()
        note = '微信官方更新日志：\n' + '\n'.join(updates)
    except Exception as e:
        note = f'抓取失败：{e}，请手动检查微信官方文档'

    # 3. 写日志
    log_file = log_result(missing, note)

    print(f'[完成] 日志写入: {log_file}')
    if missing:
        print(f'[警告] 缺少 {len(missing)} 个文档')
        for m in missing:
            print(m)
    else:
        print('[正常] 所有核心文档完整')


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()