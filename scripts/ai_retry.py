#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""错题重试：改为调用当前主模型（deepseek-v4-flash）"""
from datetime import datetime
import sys

_now = datetime.now()
if _now.hour >= 23 or _now.hour < 6:
    print("[time] skip - outside 6-23")
    sys.exit(0)
del _now

import json
import urllib.request
import urllib.error
import re
import time
import os
import io

# 从 openclaw.json 读取当前主模型的 API key
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.openclaw', 'openclaw.json')
API_KEY = None
API_URL = None
MODEL_NAME = None

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    # 遍历所有 provider，找到第一个可用的
    providers = cfg.get('models', {}).get('providers', {})
    # 优先找 deepseek-v4-flash（当前主模型）
    for pname in ['sensenova', 'deepseek']:
        provider = providers.get(pname, {})
        key = provider.get('apiKey', '')
        base_url = provider.get('baseUrl', '')
        if key and base_url:
            API_KEY = key
            API_URL = base_url.rstrip('/') + '/v1/chat/completions'
            MODEL_NAME = 'deepseek-v4-flash' if 'sensenova' in pname or 'deepseek' in pname else 'MiniMax-M2.7'
            break

if not API_KEY or not API_URL:
    # 备用：从环境变量读取
    import os as _os
    API_KEY = _os.environ.get('DEEPSEEK_API_KEY', '') or _os.environ.get('OPENAI_API_KEY', '')
    if API_KEY:
        API_URL = 'https://api.deepseek.com/v1/chat/completions'
        MODEL_NAME = 'deepseek-chat'
    else:
        print('[aiRetry] 错误: 未找到可用的 API key，已跳过')
        sys.exit(0)

PENDING_FILE = r'C:\Users\Administrator\.openclaw\workspace\wrongbook\ai_pending.json'
RESULTS_FILE = r'C:\Users\Administrator\.openclaw\workspace\wrongbook\ai_results.json'

def call_llm(prompt, tokens=80):
    body = json.dumps({
        'model': MODEL_NAME,
        'max_tokens': tokens,
        'temperature': 0.3,
        'messages': [{'role': 'user', 'content': prompt}]
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + API_KEY
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        print(f'[aiRetry] HTTP error: {e.code} {e.reason}')
        return None
    except Exception as e:
        print(f'[aiRetry] API call failed: {e}')
        return None

def clean_text(text):
    if not text:
        return ''
    text = re.sub(r' response.*? response', '', text, flags=re.DOTALL)
    text = re.sub(r'\(|\)|\[|\]', '', text)
    text = re.sub(r'\{|\}', '', text)
    text = re.sub(r'\frac\{([^}]*)\}\{([^}]*)\}', r'\1/\2', text)
    text = re.sub(r'\text\{([^}]*)\}', r'\1', text)
    text = text.replace('+', '').replace('**', '')
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_answer(text):
    if not text:
        return ''
    patterns = [
        r'\[答案\]\s*[::]?\s*(\d+)',
        r'答案[::]\s*[::]?\s*(\d+)',
        r'答案[::]\s*[::]?\s*([^\n]+)'
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            raw = m.group(1).strip()
            num = re.search(r'(\d+)', raw)
            if num:
                return num.group(1)
            return raw
    return ''

def get_pending_questions():
    try:
        if not os.path.exists(PENDING_FILE):
            print(f'[aiRetry] Local file does not exist, creating empty list')
            os.makedirs(os.path.dirname(PENDING_FILE), exist_ok=True)
            with open(PENDING_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data:
            print(f'[aiRetry] Read {len(data)} pending questions from local file')
            return data
    except Exception as e:
        print(f'[aiRetry] Failed to read pending file: {e}')
    return []

def process_question(question, item_id=None):
    if not question or not question.strip():
        return None
    prompt = 'You are an elementary school math teacher. Please solve this problem:\n\nQuestion:\n' + question + '\n\nWrite out detailed solution steps step by step, then give the final answer. Format:\nSolution steps: Step 1... Step 2... Step 3...\nAnswer: number'
    result = call_llm(prompt)
    if not result:
        print(f'[aiRetry] API returned empty')
        return None
    clean = clean_text(result)
    answer = parse_answer(clean)
    if not answer:
        print(f'[aiRetry] No answer extracted, keep pending')
        return None
    steps = clean
    steps = re.sub(r'\[答案\].*', '', steps, flags=re.IGNORECASE)
    steps = re.sub(r'答案[::]\s*[.\s\S]*$', '', steps, flags=re.IGNORECASE)
    steps = re.sub(r'^[Solution steps:]\s*', '', steps, flags=re.IGNORECASE)
    return {
        'answer': answer,
        'analysis': steps or 'Detailed solution steps',
        'id': item_id
    }

def save_result(result_item):
    try:
        results = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
        results.append(result_item)
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'[aiRetry] Result saved: answer={result_item["answer"]}')
    except Exception as e:
        print(f'[aiRetry] Failed to save result: {e}')

def remove_from_pending(item):
    try:
        if not os.path.exists(PENDING_FILE):
            return
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            pending = json.load(f)
        pending = [p for p in pending if p != item]
        with open(PENDING_FILE, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False)
        print(f'[aiRetry] Removed from pending list')
    except Exception as e:
        print(f'[aiRetry] Failed to update pending list: {e}')

def main():
    print('[aiRetry] ========== Wrong Question AI Retry Task Started ==========')
    print(f'[aiRetry] Time: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'[aiRetry] Model: {MODEL_NAME}')
    pending = get_pending_questions()
    if not pending:
        print('[aiRetry] No pending questions')
        print('[aiRetry] ========== Task End ==========')
        return
    print(f'[aiRetry] Total pending questions: {len(pending)}')
    to_process = pending[:5]
    processed = 0
    for item in to_process:
        question = item.get('question', '') or item.get('aiPendingQuestion', '')
        item_id = item.get('_id', '') or item.get('id', '')
        if not question:
            remove_from_pending(item)
            continue
        print(f'[aiRetry] Processing question [{question[:30]}...]')
        result = process_question(question, item_id)
        if result:
            save_result(result)
            remove_from_pending(item)
            processed += 1
            print(f'[aiRetry] Success, answer: {result["answer"]}')
        else:
            print(f'[aiRetry] Failed')
        time.sleep(2)
    print(f'[aiRetry] ========== Task Complete ==========')
    print(f'[aiRetry] Processed: {processed}/{len(to_process)}')

if __name__ == '__main__':
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()