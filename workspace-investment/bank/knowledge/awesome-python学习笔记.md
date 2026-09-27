# awesome-python 学习笔记

**来源**: https://github.com/vinta/awesome-python
**学习时间**: 2026-05-01 22:18
**Star数**: #10 most-starred repo on GitHub

---

## 核心分类总览

| 分类 | 说明 |
|------|------|
| AI & ML | AI/Agent/LLM/深度学习/ML/NLP/CV |
| Web开发 | 框架/API/服务器/模板/认证 |
| Database | ORM/驱动/缓存/搜索 |
| Data Science | 分析/可视化/科学计算 |
| DevOps | 任务队列/消息/日志 |
| CLI & GUI | 命令行工具/图形界面 |
| Security | 加密/渗透测试/Web安全 |
| Python Language | 实现/函数式/异步/时间 |
| Python Toolchain | 环境/包管理/分发 |

---

## AI & ML

### AI and Agents

**Agent框架**:
| 框架 | 特点 |
|-------|------|
| langchain | LLM应用组合 |
| autogen | Microsoft开源的多Agent框架 |
| crewai | 角色扮演自主Agent |
| dspy | 斯坦福的编程而非提示框架 |
| pydantic-ai | 结构化输出的Agent框架 |
| openai-agents | OpenAI官方框架 |

**LLM推理/训练**:
| 库 | 用途 |
|----|------|
| vllm | 高吞吐LLM推理引擎 |
| transformers | HuggingFace预训练模型 |
| llama-index | LLM应用数据框架 |
| diffusers | 扩散模型（图像/音频/视频）|
| openai-whisper | 语音识别 |
| instructor | 从LLM提取结构化数据 |

### Deep Learning

| 框架 | 特点 |
|-------|------|
| pytorch | 动态图+GPU加速 |
| tensorflow | Google出品，生态最全 |
| keras | 高层API，支持JAX/TF/PyTorch后端 |
| jax | 自动微分+JIT编译 |
| pytorch-lightning | 快速训练/部署 |

### Machine Learning

| 库 | 用途 |
|----|------|
| scikit-learn | 最流行，文档最全 |
| xgboost | 分布式梯度提升 |
| lightgbm | 高性能梯度提升 |
| catboost | Yandex出品 |
| mindsdb | SQL接口的ML |
| timesfm | Google时序预测 |

### NLP

**通用**:
- spacy - 工业级NLP
- nltk - 学术级NLP平台
- stanza - 斯坦福60+语言

**中文**:
- jieba - 最流行分词库
- funNLP - 中文NLP合集

### Computer Vision

| 库 | 用途 |
|----|------|
| opencv | 工业级CV |
| kornia | 可微分CV |
| easyocr | 40+语言OCR |

---

## Web Development

### Web Frameworks

**同步框架**:
| 框架 | 特点 |
|-------|------|
| django | 全栈最流行 |
| flask | 微型框架 |
| pyramid | 小而美 |
| bottle | 单文件无依赖 |

**异步框架**:
| 框架 | 特点 |
|-------|------|
| starlette | 轻量ASGI框架 |
| fastapi | 自动OpenAPI+类型提示 |
| litestar | 生产级ASGI |
| tornado | WebSocket+异步 |

### Web APIs

| 库 | 特点 |
|----|------|
| fastapi | 现代异步API |
| django-rest-framework | Django生态 |
| django-ninja | Django+Pydantic |
| strawberry | GraphQL库 |

### Web Servers

**ASGI**:
- uvicorn - 最流行ASGI服务器
- hypercorn - HTTP/2+ASGI
- granian - Rust runtime高性能

**WSGI**:
- gunicorn - 预fork模式
- uwsgi - C语言高性能

---

## Database

### ORM

| 库 | 特点 |
|----|------|
| sqlalchemy | 最灵活 |
| django-orm | Django内置 |
| alembic | 数据库迁移 |

### 缓存

| 库 | 特点 |
|----|------|
| redis-py | Redis客户端 |
| django-redis | Django缓存 |

---

## Data Science

| 库 | 用途 |
|----|------|
| pandas | 数据分析 |
| numpy | 数值计算 |
| scipy | 科学计算 |
| matplotlib | 可视化 |
| polars | 高性能DataFrame |

---

## DevOps

### 任务队列

| 库 | 特点 |
|----|------|
| celery | 分布式任务队列 |
| dramatiq | 简单可靠 |
| huey | 轻量级 |

---

## Security

| 库 | 用途 |
|----|------|
| cryptography | 加密库 |
| pyjwt | JWT实现 |
| bcrypt | 密码哈希 |
| safety | 依赖安全检查 |

---

## 关键发现

### 1. Agent框架爆发
- langchain/autogen/crewai三足鼎立
- dspy代表"编程而非提示"新范式

### 2. 异步成为主流
- FastAPI/Starlette/Litestar都是异步
- uvicorn/hypercorn异步服务器

### 3. 类型提示无处不在
- FastAPI/Pydantic/Strawberry全靠类型
- 斯坦福Stanza支持60+语言

### 4. 中文NLP生态
- jieba + funNLP + 各种中文预训练模型

---

## 下一步建议

1. **Agent开发**: langchain + instructor组合
2. **LLM应用**: vllm部署 + transformers微调
3. **异步API**: FastAPI + uvicorn + Pydantic
4. **数据管道**: pandas + polars + pyarrow

---

_学习自 awesome-python vinta/awesome-python_
