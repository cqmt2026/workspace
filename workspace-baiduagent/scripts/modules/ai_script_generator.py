# -*- coding: utf-8 -*-
"""
AI话术生成器 - 借鉴Prospex AI Content Engine
功能：根据客户信息和行业，自动生成个性化开场白和行业洞察
使用系统已配置的API（SenseNova/Agnes/DeepSeek等）
"""
import sys, os, json, requests
sys.stdout.reconfigure(encoding='utf-8')

# ========== 使用系统已配置的API ==========
# 优先级：环境变量 > openclaw.json配置 > 默认值

# 尝试从环境变量获取（如果主人配置了自定义API）
CUSTOM_API_KEY = os.environ.get('AI_API_KEY', '')
CUSTOM_BASE_URL = os.environ.get('AI_BASE_URL', '')
CUSTOM_MODEL = os.environ.get('AI_MODEL', '')

# 系统默认配置（来自openclaw.json）
SYSTEM_API_CONFIGS = [
    {
        'name': 'agnes',
        'base_url': 'https://api.agnes-ai.cn/v1',
        'api_key': 'sk-UF8sfmCy2RowNGNXh9N7K264RmdV3TGQXz28Ig5Mez6KpN9e',
        'model': 'agnes-2.5-flash',
    },
    {
        'name': 'sensenova',
        'base_url': 'https://token.sensenova.cn/v1',
        'api_key': 'sk-8lDOAPNe1yEz4TjrUVZvVT11nQakA7Q9',
        'model': 'deepseek-ai/deepseek-v4-flash',
    },
    {
        'name': 'deepseek',
        'base_url': 'https://integrate.api.nvidia.com/v1',
        'api_key': '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',
        'model': 'deepseek-ai/deepseek-v4-flash',
    },
]

# 选择API配置（优先自定义，其次系统默认）
if CUSTOM_API_KEY:
    API_CONFIG = {
        'base_url': CUSTOM_BASE_URL or 'https://api.openai.com/v1',
        'api_key': CUSTOM_API_KEY,
        'model': CUSTOM_MODEL or 'gpt-4o-mini',
    }
else:
    # 使用SenseNova（当前主用）
    API_CONFIG = SYSTEM_API_CONFIGS[0]

AI_BASE_URL = API_CONFIG['base_url']
AI_API_KEY = API_CONFIG['api_key']
AI_MODEL = API_CONFIG['model']

print(f"[AI生成器] 使用API: {API_CONFIG['name'] if 'name' in API_CONFIG else 'custom'}", file=sys.stderr)

def generate_opening_script(company_name, industry, business_desc, pain_point):
    """
    生成个性化开场白
    :param company_name: 公司名称
    :param industry: 行业
    :param business_desc: 业务描述
    :param pain_point: 痛点
    :return: 开场白文本
    """
    if not AI_API_KEY:
        return None, "未配置AI_API_KEY"
    
    prompt = f"""你是一位经验丰富的销售顾问，正在为百都科技（百度代理商）准备电话开场白。

客户信息：
- 公司名称：{company_name}
- 行业：{industry}
- 业务描述：{business_desc}
- 痛点：{pain_point}

请生成一段30秒内的开场白，要求：
1. 第一句说出对方生意（证明做了功课）
2. 第二句抛行业洞察（制造好奇）
3. 第三句问获客方式（SPIN提问）
4. 语气自然，像顾问不像推销
5. 不超过100字

只输出开场白文本，不要解释。"""
    
    try:
        import requests
        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': AI_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7
        }
        
        response = requests.post(f'{AI_BASE_URL}/chat/completions', 
                                headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        script = result['choices'][0]['message']['content']
        return script, None
        
    except Exception as e:
        return None, str(e)

def generate_industry_insight(industry, keywords):
    """
    生成行业洞察（一句话）
    :param industry: 行业
    :param keywords: 关键词列表
    :return: 行业洞察文本
    """
    if not AI_API_KEY:
        return None, "未配置AI_API_KEY"
    
    prompt = f"""你是一位行业分析专家。

行业：{industry}
关键词：{', '.join(keywords[:5])}

请生成一句话行业洞察，格式：
"你们行业在百度搜索量月增XX%，但本地厂家曝光不足XX%，获客成本行业最低。"

只输出这句话，不要解释。"""
    
    try:
        import requests
        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': AI_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.5
        }
        
        response = requests.post(f'{AI_BASE_URL}/chat/completions', 
                                headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        insight = result['choices'][0]['message']['content']
        return insight, None
        
    except Exception as e:
        return None, str(e)

def generate_selection_reason(company_name, industry, icp_score):
    """
    生成选择理由（为什么选这个客户）
    :param company_name: 公司名称
    :param industry: 行业
    :param icp_score: ICP评分（0-10）
    :return: 选择理由
    """
    if not AI_API_KEY:
        return None, "未配置AI_API_KEY"
    
    prompt = f"""你是一位销售策略专家。

公司：{company_name}
行业：{industry}
ICP匹配度：{icp_score}/10

请用一句话说明为什么这家公司值得拨打，格式：
"该公司ICP匹配度高（{icp_score}分），原因是XXX，建议优先联系。"

只输出这句话，不要解释。"""
    
    try:
        import requests
        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': AI_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.5
        }
        
        response = requests.post(f'{AI_BASE_URL}/chat/completions', 
                                headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        reason = result['choices'][0]['message']['content']
        return reason, None
        
    except Exception as e:
        return None, str(e)

def batch_generate(company_list):
    """
    批量生成开场白和洞察
    :param company_list: 公司列表 [{'name': '', 'industry': '', 'desc': '', 'pain': ''}]
    :return: 生成结果列表
    """
    results = []
    for i, company in enumerate(company_list, 1):
        print(f"\n[{i}/{len(company_list)}] 生成 {company['name']}...")
        
        script, err1 = generate_opening_script(
            company.get('name', ''),
            company.get('industry', ''),
            company.get('desc', ''),
            company.get('pain', '')
        )
        
        insight, err2 = generate_industry_insight(
            company.get('industry', ''),
            company.get('keywords', [])
        )
        
        results.append({
            'name': company['name'],
            'industry': company.get('industry', ''),
            'script': script,
            'insight': insight,
            'error': err1 or err2
        })
        
        if script:
            print(f"  ✅ 开场白: {script[:50]}...")
        if insight:
            print(f"  ✅ 洞察: {insight[:50]}...")
        if err1 or err2:
            print(f"  ⚠️ 错误: {err1 or err2}")
    
    return results

if __name__ == '__main__':
    # 测试
    test_companies = [
        {
            'name': '重庆XX机械制造有限公司',
            'industry': '机械制造',
            'desc': '专精特新企业，做起重设备',
            'pain': '客户被竞品抢走',
            'keywords': ['起重设备', '起重机', '机械制造']
        }
    ]
    
    print("测试AI话术生成器...")
    results = batch_generate(test_companies)
    
    if results and results[0]['script']:
        print(f"\n生成的开场白:")
        print(results[0]['script'])
