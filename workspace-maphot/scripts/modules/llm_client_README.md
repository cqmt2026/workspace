# -*- coding: utf-8 -*-
"""
LLM接入说明 - 脚本生成模块

当前状态：LLM客户端框架就绪，但OpenClaw Gateway不暴露REST chat API

工作流程：
1. 运行 python 脚本生成_v3.py --auto --test
2. 脚本会生成提示词到 data/scripts/_pending_prompt.txt
3. 主系统读取该文件，用DeepSeek V4生成脚本
4. 主系统将结果写入 data/scripts/_generated_script.json
5. 下次运行脚本生成_v3.py会自动读取结果

示例：
  # 第1步：生成提示词
  python scripts/脚本生成_v3.py --auto --test
  
  # 第2步：主系统读取 _pending_prompt.txt，生成JSON脚本
  # 将结果保存到 data/scripts/_generated_script.json
  
  # 第3步：重新运行，自动读取LLM结果
  python scripts/脚本生成_v3.py --auto --test

当OpenClaw暴露LLM REST API后，替换llm_client.py中的MainSystemLLMClient即可。
"""
