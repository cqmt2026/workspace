# HEARTBEAT.md - 百都工作系统 Cron任务

**最后更新**: 2026-08-26

---

## 📅 每日节奏

| 时间 | 任务 | 说明 |
|------|------|------|
| 09:00 | Baidu-早间计划 | 生成今日拨打清单Top10，推送话术提醒 |
| 09:30-12:00 | 上午拨打 | 目标8-10通（行业数据破冰→SPIN四问→算账→促单） |
| 14:00-17:00 | 下午拨打 | 目标8-10通 |
| 17:00 | 录入CRM | 记录通话结果+痛点+预算+决策人+下一步 |
| 17:30 | Baidu-日报生成 | 汇总今日数据写入memory/logs/ |

## 📅 周节奏

| 时间 | 任务 | 说明 |
|------|------|------|
| 周三14:00 | Baidu-周复盘 | 数据分析+话术迭代+下周调整 |
| 周日20:00 | Baidu-周报 | 统计+行业对比+成交进度，推送主人 |

## 📅 月节奏

| 时间 | 任务 | 说明 |
|------|------|------|
| 每月1日 09:00 | Baidu-月度汇总 | 业绩统计+行业排名+目标池刷新+产品知识补充 |

---

## Cron任务详情

### Baidu-早间计划
```yaml
name: Baidu-早间计划
schedule:
  kind: cron
  expr: "0 9 * * *"
  tz: Asia/Shanghai
payload:
  kind: agentTurn
  message: |
    生成今日拨打清单：
    1. 读取 assets/中小客户目标池_2026-08-26.md
    2. 按行业优先级排序，取Top10未联系/需跟进的客户
    3. 为每个客户匹配对应行业的开场白话术
    4. 输出格式：序号 | 企业 | 行业 | 电话 | 话术摘要
```

### Baidu-日报生成
```yaml
name: Baidu-日报生成
schedule:
  kind: cron
  expr: "30 17 * * *"
  tz: Asia/Shanghai
payload:
  kind: agentTurn
  message: |
    汇总今日销售数据：
    1. 读取 memory/logs/ 下的今日日志
    2. 统计：拨打数/接通数/有效率/意向数/成交数
    3. 对比昨日数据，标记变化
    4. 输出日报并写入 memory/logs/daily_YYYYMMDD.md
```

### Baidu-周复盘
```yaml
name: Baidu-周复盘
schedule:
  kind: cron
  expr: "0 14 * * 3"
  tz: Asia/Shanghai
payload:
  kind: agentTurn
  message: |
    执行周复盘：
    1. 汇总本周4个日报数据
    2. 计算：总拨打/总接通/总意向/总成交/转化率
    3. 按行业对比转化率
    4. 分析有效/无效话术
    5. 输出下周改进建议
```

---

_由小度维护_