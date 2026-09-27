# -*- coding: utf-8 -*-
"""光伏获客系统 Dashboard HTTP Server"""
import sys, os, json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sqlite3
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

DATA_FILE = BASE / "data" / "output" / "dashboard_data.json"
DB_PATH = BASE / "data" / "pv.db"

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/docs/dashboard.html'
        elif self.path == '/api/data':
            self.send_json(self.load_data())
        else:
            return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/fill':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            result = self.fill_data(body)
            self.send_json(result)
        else:
            self.send_json({"success": False, "error": "Not found"})

    def load_data(self):
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text(encoding='utf-8'))
        # Fallback: generate on the fly
        from core.dashboard_api import get_dashboard_data
        return get_dashboard_data()

    def fill_data(self, body):
        """回填播放/互动数据"""
        content_id = body.get('content_id')
        plays = body.get('plays', 0)
        clicks = body.get('clicks', 0)
        leads = body.get('leads_generated', 0)
        
        if not content_id:
            return {"success": False, "error": "content_id required"}
        
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("""
                UPDATE content_items 
                SET plays=?, clicks=?, leads_generated=? 
                WHERE content_id=?
            """, (plays, clicks, leads, content_id))
            conn.commit()
            conn.close()
            
            if cur.rowcount > 0:
                # 重新生成dashboard数据
                from core.dashboard_api import get_dashboard_data
                data = get_dashboard_data()
                DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
                return {"success": True, "message": f"已更新 {content_id}"}
            else:
                return {"success": False, "error": f"未找到内容ID: {content_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        pass  # 静默日志

if __name__ == "__main__":
    # 先生成初始数据
    if not DATA_FILE.exists():
        from core.dashboard_api import get_dashboard_data
        data = get_dashboard_data()
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    port = 8765
    server = HTTPServer(('127.0.0.1', port), Handler)
    print(f"Dashboard running at http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
