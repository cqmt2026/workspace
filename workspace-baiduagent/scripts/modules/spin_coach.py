# -*- coding: utf-8 -*-
"""
SPIN/MEDDPICC销售教练
融合来源: agency-agents/sales/sales-discovery-coach.md
功能: 提问框架、需求挖掘、交易评分
"""

# SPIN提问框架
SPIN_FRAMEWORK = {
    'S_Situation': {
        'name': '现状问题',
        'description': '了解客户当前状况',
        'questions': [
            '您现在主要靠什么渠道获客？',
            '目前线上推广投入多少？',
            '团队有多少人负责销售？',
            '过去半年业绩增长如何？'
        ],
        'tip': '限制在2-3个问题，避免像审讯'
    },
    'P_Problem': {
        'name': '问题问题',
        'description': '挖掘痛点和不满',
        'questions': [
            '目前的获客方式有什么困扰？',
            '客户来源稳定吗？有没有波动？',
            '有没有遇到过客户被竞品抢走的情况？',
            '现在的推广效果满意吗？'
        ],
        'tip': '让客户说出具体困扰，不要假设'
    },
    'I_Implication': {
        'name': '影响问题',
        'description': '放大痛点，制造紧迫感',
        'questions': [
            '这个问题持续多久了？',
            '对业务增长有什么具体影响？',
            '如果这个问题不解决，半年后会怎样？',
            '竞争对手这样做，您这边压力有多大？'
        ],
        'tip': '这是最关键的部分，激活损失厌恶'
    },
    'N_NeedPayoff': {
        'name': '需求-收益问题',
        'description': '让客户自己说出解决方案的价值',
        'questions': [
            '如果能解决这个问题，对您意味着什么？',
            '您希望达到什么样的获客效果？',
            '如果每月能带来10个精准客户，对您有帮助吗？',
            '您理想中的获客方式是什么样的？'
        ],
        'tip': '让客户自己推销解决方案'
    }
}

# MEDDPICC评分框架
MEDDPICC_FRAMEWORK = {
    'M_Metrics': {
        'name': '量化指标',
        'description': '客户是否量化了解决问题的价值',
        'score': 0,
        'max_score': 1,
        'questions': ['您希望获得多少新增客户？', '一个客户的价值大概多少？']
    },
    'E_EconomicBuyer': {
        'name': '经济决策人',
        'description': '是否找到有预算决定权的人',
        'score': 0,
        'max_score': 1,
        'questions': ['这件事您能直接决定吗？', '需要跟谁确认？']
    },
    'D_DecisionCriteria': {
        'name': '决策标准',
        'description': '客户评估方案的依据',
        'score': 0,
        'max_score': 1,
        'questions': ['您选择供应商主要看什么？', '价格、效果、服务哪个更重要？']
    },
    'D_DecisionProcess': {
        'name': '决策流程',
        'description': '采购流程和审批链',
        'score': 0,
        'max_score': 1,
        'questions': ['采购流程是怎样的？', '需要哪些审批？', '大概多久能定？']
    },
    'P_PaperProcess': {
        'name': '流程文件',
        'description': '合同、法律、采购流程',
        'score': 0,
        'max_score': 1,
        'questions': ['合同流程复杂吗？', '需要走采购招标吗？']
    },
    'I_ImplicatedPain': {
        'name': '痛点关联',
        'description': '痛点是否与业务结果挂钩',
        'score': 0,
        'max_score': 1,
        'questions': ['这个问题对您的KPI有什么影响？', '如果不解决会损失多少？']
    },
    'C_Champion': {
        'name': '内部支持者',
        'description': '是否有内部 champion 推动',
        'score': 0,
        'max_score': 1,
        'questions': ['还有谁关心这个问题？', '谁会支持您做这个改变？']
    },
    'C_Competition': {
        'name': '竞争情况',
        'description': '是否有竞争对手也在接触',
        'score': 0,
        'max_score': 1,
        'questions': ['还有其他供应商接触吗？', '您主要对比哪几家？']
    }
}

def get_spin_questions(pain_point):
    """
    根据痛点生成SPIN提问序列
    """
    questions = []
    
    # S: 现状
    questions.append({
        'type': 'S',
        'question': f'您目前是怎么做{pain_point}的？',
        'purpose': '了解现状'
    })
    
    # P: 问题
    questions.append({
        'type': 'P',
        'question': f'这种方式有什么不满意的地方吗？',
        'purpose': '挖掘痛点'
    })
    
    # I: 影响
    questions.append({
        'type': 'I',
        'question': f'这个问题给您带来什么实际损失？',
        'purpose': '放大影响'
    })
    
    # N: 需求
    questions.append({
        'type': 'N',
        'question': f'如果能解决这个问题，对您有什么帮助？',
        'purpose': '确认价值'
    })
    
    return questions

def calculate_meddpicc_score(customer_data):
    """
    计算MEDDPICC评分
    """
    total_score = 0
    max_score = len(MEDDPICC_FRAMEWORK)
    details = []
    
    # 根据客户数据评分（简化版）
    if customer_data.get('budget_confirmed'):
        MEDDPICC_FRAMEWORK['M_Metrics']['score'] = 1
    if customer_data.get('decision_maker'):
        MEDDPICC_FRAMEWORK['E_EconomicBuyer']['score'] = 1
    if customer_data.get('decision_criteria'):
        MEDDPICC_FRAMEWORK['D_DecisionCriteria']['score'] = 1
    if customer_data.get('timeline'):
        MEDDPICC_FRAMEWORK['D_DecisionProcess']['score'] = 1
    if customer_data.get('contract_ready'):
        MEDDPICC_FRAMEWORK['P_PaperProcess']['score'] = 1
    if customer_data.get('pain_quantified'):
        MEDDPICC_FRAMEWORK['I_ImplicatedPain']['score'] = 1
    if customer_data.get('champion'):
        MEDDPICC_FRAMEWORK['C_Champion']['score'] = 1
    if customer_data.get('competition'):
        MEDDPICC_FRAMEWORK['C_Competition']['score'] = 1
    
    for key, field in MEDDPICC_FRAMEWORK.items():
        total_score += field['score']
        if field['score'] == 0:
            details.append(f"⚠️ {field['name']}: 未确认")
        else:
            details.append(f"✅ {field['name']}: 已确认")
    
    health_level = '健康' if total_score >= 6 else ('需关注' if total_score >= 4 else '高风险')
    
    return {
        'total_score': total_score,
        'max_score': max_score,
        'health_level': health_level,
        'details': details
    }

def generate_discovery_script(industry, pain_point):
    """
    生成完整开场白+SPIN话术
    """
    script = f"""
# 🎯 {industry}行业SPIN销售话术

## 开场白（30秒）
"您好，我是百都科技小度。我们正在做{industry}行业的获客调研，发现一个现象——很多{industry}企业在百度上几乎没有曝光，但客户找供应商第一站就是百度搜索。

想跟您确认下，你们现在主要靠什么渠道获客？"

## SPIN提问序列

### S - 现状
{get_spin_questions(pain_point)[0]['question']}

### P - 问题
{get_spin_questions(pain_point)[1]['question']}

### I - 影响
{get_spin_questions(pain_point)[2]['question']}

### N - 需求
{get_spin_questions(pain_point)[3]['question']}

## 关键提示
- 每个阶段控制在2-3个问题
- 多用开放式问题（什么/如何/为什么）
- 避免连续追问，给客户思考空间
- 记录客户原话，后续用作异议处理素材
"""
    return script

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("SPIN/MEDDPICC 销售教练")
    print("=" * 60)
    
    # 示例：口腔行业
    industry = '口腔'
    pain_point = '获客'
    
    script = generate_discovery_script(industry, pain_point)
    print(script)
    
    # MEDDPICC评分示例
    sample_data = {
        'budget_confirmed': True,
        'decision_maker': True,
        'decision_criteria': False,
        'timeline': True,
        'contract_ready': False,
        'pain_quantified': True,
        'champion': False,
        'competition': True
    }
    
    score = calculate_meddpicc_score(sample_data)
    print("\n" + "=" * 60)
    print("📊 MEDDPICC 交易健康评分")
    print("=" * 60)
    print(f"总分: {score['total_score']}/{score['max_score']}")
    print(f"健康度: {score['health_level']}")
    print("\n详细:")
    for detail in score['details']:
        print(f"  {detail}")
