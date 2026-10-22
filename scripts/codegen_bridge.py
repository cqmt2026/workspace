#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码生成桥接模块 v2.0 - 本地代码生成工作流

支持两种模式：
1. 模板模式（--no-llm）：从预置模板生成
2. LLM模式（默认）：调用agnes-2.5-flash生成

用法：
    python codegen_bridge.py "功能描述" --output path/to/script.py
    python codegen_bridge.py "数据清洗脚本" --type data_pipeline --no-llm
"""

import os
import sys
import ast
import json
import argparse
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
CODE_REVIEW_SCRIPT = BASE_DIR / "scripts" / "code_review.py"

# 编码规范
CODE_STANDARDS = """
# 编码铁律v2.0要求：
# 1. 边界全覆盖：空输入、None、空字符串、0值、负数必须处理
# 2. 错误处理分层：具体异常捕获，不裸except
# 3. 影响面检查：修改公共函数后grep所有调用点
# 4. 命名规范：函数用动词开头，常量UPPER_SNAKE
# 5. 文档字符串：每个函数必须有docstring
# 6. 类型提示：函数签名必须包含类型标注
"""

# === 模板定义 ===

TEMPLATE_SCRIPT = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{description}

用法：
    python {filename} [选项]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

BASE_DIR = Path(__file__).parent.parent


def validate_input(data: Any) -> bool:
    """验证输入数据"""
    if data is None:
        return False
    return True


def process_data(data: Any) -> Any:
    """处理数据"""
    if not validate_input(data):
        raise ValueError("输入数据无效")
    return data


def main():
    parser = argparse.ArgumentParser(description='{description}')
    parser.add_argument('--input', '-i', type=str, help='输入文件路径')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    args = parser.parse_args()
    
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = None
        
        result = process_data(data)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {args.output}")
    except FileNotFoundError as e:
        print(f"文件不存在: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
'''

TEMPLATE_API_CLIENT = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{description}

用法：
    python {filename} [端点] [参数]
"""

import os, sys, json, argparse
from typing import Optional, Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = os.getenv('API_BASE_URL', 'https://api.example.com')
TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))


class APIClient:
    """API客户端"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送GET请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误: {e}", file=sys.stderr)
            raise
        except requests.exceptions.Timeout:
            print("请求超时", file=sys.stderr)
            raise


def main():
    parser = argparse.ArgumentParser(description='{description}')
    parser.add_argument('endpoint', help='API端点')
    parser.add_argument('--param', '-p', action='append', help='查询参数')
    args = parser.parse_args()
    
    client = APIClient()
    params = {}
    if args.param:
        for p in args.param:
            if '=' in p:
                k, v = p.split('=', 1)
                params[k] = v
    
    try:
        result = client.get(args.endpoint, params=params if params else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
'''

TEMPLATE_SCHEDULER = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{description}

用法：
    python {filename} [--once] [--daemon]
"""

import os, sys, time, argparse, logging
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

INTERVAL = int(os.getenv('SCHEDULER_INTERVAL', '300'))


def task_function() -> bool:
    """执行定时任务"""
    logger.info("执行定时任务...")
    try:
        # TODO: 实现具体任务逻辑
        logger.info("任务执行完成")
        return True
    except Exception as e:
        logger.error(f"任务失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='{description}')
    parser.add_argument('--once', '-o', action='store_true', help='只执行一次')
    parser.add_argument('--daemon', '-d', action='store_true', help='守护进程')
    args = parser.parse_args()
    
    if args.once:
        task_function()
    else:
        logger.info(f"启动定时任务，间隔{INTERVAL}秒")
        while True:
            try:
                task_function()
                time.sleep(INTERVAL)
            except KeyboardInterrupt:
                logger.info("退出")
                break
            except Exception as e:
                logger.error(f"错误: {e}")
                time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
'''

TEMPLATE_DATA_PIPELINE = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{description}

用法：
    python {filename} --input input.csv --output output.json
"""

import os, sys, argparse
from pathlib import Path
from typing import Optional
import pandas as pd


class DataPipeline:
    """数据处理流水线"""
    
    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None
        self.data = None
        self.stats = {}
    
    def load(self) -> pd.DataFrame:
        """加载数据"""
        if not self.input_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.input_path}")
        
        suffix = self.input_path.suffix.lower()
        if suffix == '.csv':
            self.data = pd.read_csv(self.input_path, encoding='utf-8')
        elif suffix == '.json':
            self.data = pd.read_json(self.input_path)
        else:
            self.data = pd.read_csv(self.input_path, encoding='utf-8')
        
        self.stats['rows'] = len(self.data)
        self.stats['columns'] = list(self.data.columns)
        return self.data
    
    def clean(self) -> pd.DataFrame:
        """数据清洗"""
        if self.data is None:
            raise RuntimeError("请先加载数据")
        initial = len(self.data)
        self.data = self.data.dropna().drop_duplicates()
        self.stats['cleaned_rows'] = initial - len(self.data)
        return self.data
    
    def export(self) -> Path:
        """导出数据"""
        if self.data is None:
            raise RuntimeError("没有数据可导出")
        
        output_path = self.output_path or self.input_path.with_suffix('.cleaned.csv')
        output_path = Path(output_path)
        self.data.to_csv(output_path, index=False, encoding='utf-8')
        self.stats['output_path'] = str(output_path)
        return output_path


def main():
    parser = argparse.ArgumentParser(description='{description}')
    parser.add_argument('--input', '-i', required=True, help='输入文件')
    parser.add_argument('--output', '-o', help='输出文件')
    parser.add_argument('--clean', action='store_true', help='执行清洗')
    args = parser.parse_args()
    
    pipeline = DataPipeline(args.input, args.output)
    pipeline.load()
    print(f"加载: {pipeline.stats['rows']}行, {len(pipeline.stats['columns'])}列")
    
    if args.clean:
        pipeline.clean()
        print(f"清洗: 清理{pipeline.stats.get('cleaned_rows', 0)}行")
    
    output = pipeline.export()
    print(f"导出: {output}")


if __name__ == '__main__':
    main()
'''

TEMPLATE_ML_MODEL = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{description}

用法：
    python {filename} --train data.csv --output model.pkl
"""

import os, sys, argparse
from pathlib import Path
from typing import Optional, Dict
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib


class MLModel:
    """机器学习模型"""
    
    def __init__(self):
        self.model = None
        self.history = {}
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """训练模型"""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        self.history = {'accuracy': accuracy, 'test_size': len(y_test)}
        return self.history
    
    def save(self, filepath: str):
        """保存模型"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({'model': self.model, 'history': self.history}, filepath)
        print(f"模型已保存: {filepath}")


def main():
    parser = argparse.ArgumentParser(description='{description}')
    parser.add_argument('--train', '-t', help='训练数据')
    parser.add_argument('--output', '-o', help='输出路径')
    args = parser.parse_args()
    
    if args.train:
        df = pd.read_csv(args.train)
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
        
        model = MLModel()
        result = model.train(X, y)
        print(f"训练完成，准确率: {result['accuracy']:.4f}")
        
        if args.output:
            model.save(args.output)


if __name__ == '__main__':
    main()
'''

TEMPLATE_WEB_SCRAPER = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{description}

用法：
    python {filename} --url https://example.com --output result.json
"""

import os, sys, json, argparse, time
from pathlib import Path
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup


class WebScraper:
    """Web爬虫"""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    def fetch(self, url: str) -> Optional[Dict]:
        """获取页面"""
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            result = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'links': [a['href'] for a in soup.find_all('a', href=True)],
                'status': resp.status_code
            }
            time.sleep(self.delay)
            return result
        except Exception as e:
            print(f"请求失败 {url}: {e}", file=sys.stderr)
            return None


def main():
    parser = argparse.ArgumentParser(description='{description}')
    parser.add_argument('--url', '-u', help='URL')
    parser.add_argument('--output', '-o', required=True, help='输出文件')
    args = parser.parse_args()
    
    scraper = WebScraper()
    
    if args.url:
        print(f"爬取: {args.url}")
        result = scraper.fetch(args.url)
        if result:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"保存到: {output_path}")


if __name__ == '__main__':
    main()
'''

# 模板字典
TEMPLATES = {
    "script": TEMPLATE_SCRIPT,
    "api_client": TEMPLATE_API_CLIENT,
    "scheduler": TEMPLATE_SCHEDULER,
    "data_pipeline": TEMPLATE_DATA_PIPELINE,
    "ml_model": TEMPLATE_ML_MODEL,
    "web_scraper": TEMPLATE_WEB_SCRAPER,
}


def build_prompt(description: str, template_type: str = "script") -> str:
    """构建LLM代码生成prompt（优化版）"""
    template = TEMPLATES.get(template_type, TEMPLATE_SCRIPT)
    filename = f"{description.replace(' ', '_').lower()}.py"
    
    # 根据模板类型调整prompt
    if template_type == "data_pipeline":
        extra_guidance = """
## 数据处理特别要求
1. 必须处理文件不存在的情况
2. 必须处理JSON/CSV解析错误
3. 必须验证数据格式
4. 必须提供清晰的进度输出
5. 使用pandas处理数据，但添加必要的导入检查
"""
    elif template_type == "api_client":
        extra_guidance = """
## API客户端特别要求
1. 必须包含重试机制（最多3次）
2. 必须设置超时时间（默认30秒）
3. 必须处理HTTP错误（4xx/5xx）
4. 必须使用Session复用连接
5. 不要硬编码API密钥，使用环境变量
"""
    elif template_type == "scheduler":
        extra_guidance = """
## 定时任务特别要求
1. 必须处理KeyboardInterrupt
2. 必须记录执行日志
3. 必须支持--once和--daemon模式
4. 必须处理异常避免任务中断
5. 间隔时间可通过环境变量配置
"""
    else:
        extra_guidance = ""
    
    return f"""你是一位专业的Python工程师，擅长编写高质量、可维护的代码。

## 需求描述
{description}

## 代码风格参考
{template[:800]}

## 编码规范（必须遵守）
{CODE_STANDARDS}
{extra_guidance}
## 输出要求
1. 只输出Python代码，不要任何解释文字
2. 代码必须是完整可运行的，不要省略部分
3. 使用标准库，避免第三方依赖（除非必要）
4. 代码风格遵循PEP 8规范
5. 所有函数必须有docstring
6. 使用类型提示

请生成代码：
"""


def call_llm(prompt: str) -> str:
    """调用LLM生成代码（使用OpenClaw模型，优化版）"""
    import subprocess
    
    try:
        # 使用openclaw chat命令调用模型
        result = subprocess.run(
            ["openclaw", "chat", "--message", prompt, "--model", "agnes-25/agnes-2.5-flash"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            # 提取代码部分（移除markdown标记和解释文字）
            output = re.sub(r'```python\s*', '', output)
            output = re.sub(r'```\s*', '', output)
            # 移除开头的非代码文本
            lines = output.split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                # 检测代码开始
                if not in_code:
                    if line.startswith('#') or line.startswith('"""') or line.startswith("'''") or \
                       line.startswith('import') or line.startswith('from') or line.strip().startswith('def '):
                        in_code = True
                        code_lines.append(line)
                    elif line.strip() == '':
                        continue  # 跳过空行
                    else:
                        continue  # 跳过解释性文字
                else:
                    code_lines.append(line)
            output = '\n'.join(code_lines)
            return output
        else:
            logger.warning(f"LLM调用失败: {result.stderr[:200]}")
            return ""
    except FileNotFoundError:
        logger.warning("openclaw命令不可用，使用模板生成")
        return ""
    except Exception as e:
        logger.warning(f"LLM调用异常: {e}")
        return ""


def post_process_code(code: str) -> str:
    """后处理代码（优化版）"""
    code = re.sub(r'```python\s*', '', code)
    code = re.sub(r'```\s*', '', code)
    
    # 标准化换行符
    code = code.replace('\r\n', '\n')
    
    # 检查并添加必要的import
    imports_to_add = []
    if 'json' in code and 'import json' not in code:
        imports_to_add.append('import json')
    if 'Path' in code and 'from pathlib import Path' not in code:
        imports_to_add.append('from pathlib import Path')
    if 'argparse' in code and 'import argparse' not in code:
        imports_to_add.append('import argparse')
    if 'logging' in code and 'import logging' not in code:
        imports_to_add.append('import logging')
    if 'sys' in code and 'import sys' not in code:
        imports_to_add.append('import sys')
    if 'os' in code and 'import os' not in code:
        imports_to_add.append('import os')
    if 're' in code and 'import re' not in code:
        imports_to_add.append('import re')
    if 'typing' in code and 'from typing import' not in code:
        imports_to_add.append('from typing import Optional, List, Dict, Any')
    
    if imports_to_add:
        # 找到第一个import语句的位置
        import_match = re.search(r'^import|^from', code, re.MULTILINE)
        if import_match:
            insert_pos = import_match.start()
        else:
            # 如果没有import，在文件头添加
            insert_pos = 0
        imports_text = '\n'.join(imports_to_add) + '\n'
        code = code[:insert_pos] + imports_text + code[insert_pos:]
    
    # 移除多余的空白行
    code = re.sub(r'\n{3,}', '\n\n', code)
    
    return code.strip()


def validate_syntax(code: str) -> tuple:
    """验证代码语法"""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def run_code_review(filepath: str) -> dict:
    """运行代码审查"""
    if not CODE_REVIEW_SCRIPT.exists():
        return {"status": "SKIP", "message": "code_review.py不存在"}
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(CODE_REVIEW_SCRIPT), filepath],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except:
                return {"status": "OK", "message": "审查完成"}
        else:
            return {"status": "ERROR", "message": result.stderr[:200]}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def generate_code(description: str, output_path: Optional[str] = None, 
                  template_type: str = "script", use_llm: bool = True) -> str:
    """生成代码
    
    Args:
        description: 功能描述
        output_path: 输出文件路径
        template_type: 模板类型
        use_llm: True=使用LLM生成，False=使用模板
        
    Returns:
        str: 生成的代码或文件路径
    """
    template = TEMPLATES.get(template_type, TEMPLATE_SCRIPT)
    filename = f"{description.replace(' ', '_').lower()}.py"
    
    if use_llm:
        logger.info("使用LLM生成代码...")
        prompt = build_prompt(description, template_type)
        code = call_llm(prompt)
        
        if code and code.strip():
            logger.info("LLM生成完成")
        else:
            logger.warning("LLM生成失败，回退到模板")
            code = template.replace('{description}', description).replace('{filename}', filename)
    else:
        logger.info("使用模板生成代码...")
        code = template.replace('{description}', description).replace('{filename}', filename)
    
    code = post_process_code(code)
    is_valid, error = validate_syntax(code)
    if not is_valid:
        logger.error(f"语法验证失败: {error}")
        raise ValueError(f"生成的代码语法错误: {error}")
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code, encoding='utf-8')
        logger.info(f"代码已保存到: {output_file}")
        review_result = run_code_review(str(output_file))
        logger.info(f"代码审查结果: {review_result}")
        return str(output_file)
    
    return code


def main():
    parser = argparse.ArgumentParser(
        description="代码生成桥接工具 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python codegen_bridge.py "数据清洗脚本" -o scripts/cleaner.py
  python codegen_bridge.py "API客户端" --type api_client
  python codegen_bridge.py "定时任务" --no-llm
        """
    )
    parser.add_argument("description", help="功能描述")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--type", "-t", 
                        choices=["script", "api_client", "scheduler", "data_pipeline", "ml_model", "web_scraper"],
                        default="script", help="代码模板类型")
    parser.add_argument("--no-llm", action="store_true", help="不使用LLM，直接使用模板")
    parser.add_argument("--validate-only", action="store_true", help="只验证代码")
    
    args = parser.parse_args()
    
    if args.validate_only and args.output:
        if Path(args.output).exists():
            code = Path(args.output).read_text(encoding='utf-8')
            is_valid, error = validate_syntax(code)
            if is_valid:
                print(f"语法验证通过: {args.output}")
            else:
                print(f"语法验证失败: {error}")
                sys.exit(1)
        else:
            print(f"文件不存在: {args.output}")
            sys.exit(1)
    else:
        try:
            result = generate_code(args.description, args.output, args.type, not args.no_llm)
            if args.output:
                print(f"代码已生成: {result}")
            else:
                print(result)
        except Exception as e:
            print(f"代码生成失败: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
