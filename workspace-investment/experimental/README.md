# 实验性新系统 - 结果反推设计
#
# 核心逻辑：买入后上涨 = 板块共振 + 资金流入 + 动量确认
# 
# 目录说明：
#   step1_sector_filter.py   - 板块RPS筛选（从RPS>70板块中选股）
#   step2_money_flow.py      - 资金流入验证
#   step3_momentum_confirm.py - 动量确认
#   pipeline.py              - 三步串联主流程
#   test_backtest.py         - 回测验证
#   test_live.py             - 实盘测试（只输出不交易）
#
# 设计原则：
#   1. 每一步可独立测试
#   2. 每一步可追踪胜率
#   3. 测试通过前不修改现有系统