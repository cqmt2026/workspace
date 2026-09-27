"""
session_extract.py - 从 OpenClaw session 文件自动提取对话事实
读取最新 session JSONL → 提取 user/assistant 对话 → 写入 Supermemory

用法:
    python session_extract.py                    # 提取今日所有 session
    python session_extract.py --continuous        # 持续监控，每60秒检查新内容
    python session_extract.py --session FILE    # 提取指定 session 文件
"""
import os
import sys
import json
import sqlite3
import uuid
import time
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path
import io

SESSION_DIR = r"C:\Users\Administrator\.openclaw\agents\main\sessions"
DB_PATH = os.path.join(os.path.expanduser("~"), ".supermemory", "memory.db")
API_KEY_FILE = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json")
STATE_FILE = os.path.join(os.path.dirname(__file__), ".session_extract_last.json")

SKIP_PATTERNS = [
    'HEARTBEAT_OK', 'NO_REPLY', 'HEARTBEAT:', '[heartbeat',
    'HEARTBEAT_POLL', '[OpenClaw heartbeat', 'HEARTBEAT'
]

def is_skip(text):
    if not text: return True
    upper = text.upper()
    return any(p.upper() in upper for p in SKIP_PATTERNS)

from llm_config import get_llm_config

def extract_facts(text):
    """调用当前主模型 API 提取原子事实"""
    prompt = (
        "你是一个事实提取器。\n"
        "输入一段对话文本，直接输出其中的原子事实，每行一条，不能解释，不能编号，不能思考标签。\n"
        "规则：\n"
        "1. 每行只输出一个事实，用中文陈述句\n"
        "2. 不要出现'用户说'、'文本提到'等元叙述\n"
        "3. 不要输出解释或说明\n\n"
        f"对话文本：{text}\n\n事实："
    )
    try:
        key, api_url, model_name = get_llm_config()
        if not key or not api_url:
            print("[session_extract] 错误: 未找到可用的 LLM API 配置")
            return []
        resp = requests.post(
            api_url,
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': model_name, 'messages': [{'role': 'user', 'content': prompt}],
                  'max_tokens': 600, 'temperature': 0},
            timeout=30
        )
        resp.raise_for_status()
        raw = resp.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"[session_extract] LLM error: {e}")
        return []

    content = re.sub(r'<[^>]{1,30}>', '', raw).strip()
    facts = []
    for line in content.split('\n'):
        line = line.strip().rstrip('。').strip()
        if not line or len(line) < 6:
            continue
        lower = line.lower()
        skip_words = ['the user', 'but what', 'option ', 'alternatively', 'thus output',
                       'let\'s think', 'actually', 'in summary', 'here is', 'here are',
                       'the text', 'the following', 'so we', 'therefore', 'however',
                       'for example', 'note:', 'summary:', 'atomic fact', 'what is']
        if any(lower.startswith(w) for w in skip_words):
            continue
        facts.append(line)
    return facts[:20]

def write_memory(content, session_key, agent_id='main'):
    """直接写 Supermemory SQLite"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    date_str = now[:10]
    chunk_id = str(uuid.uuid4())
    memory_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO source_chunks (id, content, session_key, agent_id, document_date, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (chunk_id, content, session_key, agent_id, date_str, now)
    )
    cur.execute(
        "INSERT INTO memories (id, content, category, confidence, document_date, event_date, "
        "source_session, source_agent, source_chunk_id, version, is_current, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (memory_id, content, 'fact', 0.9, date_str, date_str, session_key, agent_id, chunk_id, 1, True, now, now)
    )
    conn.commit()
    conn.close()

def read_session_file(filepath):
    """读取 session JSONL，返回对话列表"""
    messages = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get('type') == 'message':
                        msg = obj.get('message', {})
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        if role in ('user', 'assistant') and content:
                            if isinstance(content, list):
                                # text parts only
                                text = ' '.join(
                                    c.get('text', '') for c in content
                                    if isinstance(c, dict) and c.get('type') == 'text'
                                )
                            else:
                                text = str(content)
                            if text and not is_skip(text):
                                messages.append({'role': role, 'content': text[:2000]})
                except (json.JSONDecodeError, KeyError):
                    continue
    except Exception as e:
        print(f"[session_extract] read error: {e}")
    return messages

def get_latest_session():
    """获取最新 session 文件"""
    files = list(Path(SESSION_DIR).glob("*.jsonl"))
    files = [f for f in files if "lock" not in f.name and "trajectory" not in f.name]
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)

def format_conversation(messages):
    """把消息列表格式化成对话文本"""
    lines = []
    for m in messages:
        role = "用户" if m['role'] == 'user' else "AI"
        lines.append(f"{role}：{m['content']}")
    return '\n'.join(lines)

def load_last_processed():
    """读取上次处理位置"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_last_processed(state):
    """保存处理位置"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False)

def process_latest_session():
    """处理最新 session 的新增内容"""
    latest = get_latest_session()
    if not latest:
        print("[session_extract] no session found")
        return 0

    state = load_last_processed()
    last_pos = state.get(latest.name, 0)
    file_size = latest.stat().st_size

    if file_size <= last_pos:
        # 没有新内容
        return 0

    messages = read_session_file(latest)
    if not messages:
        return 0

    # 只处理新增的消息（从 last_pos 位置之后）
    new_messages = messages  # 简化：取所有消息，由 fact_extract 做去重
    if not new_messages:
        return 0

    text = format_conversation(new_messages)
    if not text.strip():
        return 0

    facts = extract_facts(text)
    count = 0
    for fact in facts:
        write_memory(fact, latest.stem, 'main')
        count += 1

    # 保存状态
    state[latest.name] = file_size
    save_last_processed(state)

    print(f"[session_extract] {latest.name}: {len(new_messages)} msgs -> {count} facts")
    return count

def main():
    if '--continuous' in sys.argv:
        print("[session_extract] Running in continuous mode (Ctrl+C to stop)")
        interval = 60
        try:
            while True:
                n = process_latest_session()
                if n > 0:
                    print(f"[session_extract] +{n} facts written")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("[session_extract] stopped")
    elif '--session' in sys.argv:
        idx = sys.argv.index('--session')
        filepath = sys.argv[idx + 1]
        messages = read_session_file(filepath)
        text = format_conversation(messages)
        facts = extract_facts(text)
        count = 0
        for fact in facts:
            write_memory(fact, Path(filepath).stem, 'main')
            count += 1
        print(f"[session_extract] {count} facts from {Path(filepath).name}")
        return count
    else:
        return process_latest_session()

if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    n = main()
    sys.exit(0 if n is None or n >= 0 else 1)