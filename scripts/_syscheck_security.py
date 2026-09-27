# -*- coding: utf-8 -*-
"""① 安全策略检查：密钥硬编码扫描、敏感文件暴露、Git忽略规则"""
import os, re, sys

WS = r"C:\Users\Administrator\.openclaw\workspace"
EXCLUDE = ["node_modules", ".git", "backup", ".venv", "site-packages", "__pycache__",
           "node_modules\\", "vendor\\", ".agents", "cache"]
SKIP_EXT = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3", ".wav", ".zip",
            ".exe", ".dll", ".pdf", ".woff", ".woff2", ".ttf", ".db", ".sqlite"}

KEY_PAT = re.compile(r'(api[_-]?key|apikey|secret|passwd|password|client_secret|access_token|refresh_token|authorization|MX_APIKEY)\s*[:=]\s*["\']?[^"\'\s]{8,}', re.I)
KEY_LONG = re.compile(r'(sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16,})')

def scan():
    secrets = []
    files_scanned = 0
    for root, dirs, files in os.walk(WS):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_EXT or ext not in (".py", ".js", ".json", ".txt", ".md", ".sh", ".toml", ".ini", ".cfg"):
                continue
            if f.endswith((".lock.json", ".min.js")):
                continue
            p = os.path.join(root, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                files_scanned += 1
                for m in KEY_PAT.finditer(content):
                    # skip benign examples
                    line_start = content.rfind("\n", 0, m.start()) + 1
                    line = content[m.start():][:80].replace("\n", " ")
                    secrets.append((p, m.group(1), line))
                for m in KEY_LONG.finditer(content):
                    if "xxx" not in m.group() and "XXXX" not in m.group():
                        secrets.append((p, "long-key", m.group()[:30]))
            except Exception:
                pass
    return files_scanned, secrets

if __name__ == "__main__":
    fs, sec = scan()
    print(f"[扫描文件数] {fs}")
    print(f"[命中密钥模式] {len(sec)}")
    seen = set()
    for p, k, line in sec:
        key = (p, k)
        if key in seen:
            continue
        seen.add(key)
        rel = os.path.relpath(p, WS)
        print(f"  - {rel} | {k} | {line}")
    # 敏感文件暴露
    print("\n[敏感文件检查]")
    for r, ds, fl in os.walk(WS):
        r = r.replace(WS, ".")
        for f in fl:
            if f in (".env", ".env.local", ".env.production", "secrets.json", "credentials.json", "id_rsa", "id_ed25519", "token.json", ".npmrc", ".pypirc"):
                print(f"  ⚠ 暴露: {r}/{f}")
print("DONE")