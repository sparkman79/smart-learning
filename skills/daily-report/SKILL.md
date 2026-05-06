---
name: daily-report
description: 生成日报：聚合今日学习数据，输出摘要并追加到 trends.csv
user-invocable: true
---

## 指令
- `/日报` - 生成今日学习日报
- `/日报 日期=YYYY-MM-DD` - 生成指定日期日报（可选）

## 身份与权限
- **kid**：只能看自己日报
- **parent**：可看自己 + linked_children 的日报
- **admin**：可看家庭汇总日报

## 数据源
- `data/homework/parsed/` - 今日作业计划
- `data/routines/state.json` - 今日学习状态
- `data/reports/daily/` - 日报落盘目录

## 行为

### 1. 生成日报
```
读取今日数据：
1. 今日作业：parsed/ 下今日文件
2. 学习时间：state.json 中 session.started_at, session.ack_done_at
3. 番茄轮次：state.json 中 session.round
4. 确认情况：session.ack_start, session.ack_done
5. 升级记录：escalation_stage 变化
```

**日报模板**：
```markdown
# 日报 {YYYY-MM-DD}（{member_id}）

## 学习概览
- 学习时长：{XX} 分钟
- 番茄轮次：{XX} 轮
- 完成任务：{完成/总数}
- 开始确认：{时间}
- 完成确认：{时间}

## 今日作业
1. 数学口算 40 题 ✅
2. 英语背单词 10 个 ✅

## 备注
{如有升级提醒，记录原因}
```

### 2. 追加趋势数据
```
向 trends.csv 追加一行：
日期，member_id，学习时长，番茄轮次，完成数，总数，完成度
2026-05-05,kid_1,45,3,5,6,83.3
```

### 3. 落盘
```
文件：data/reports/daily/YYYY-MM-DD_{member_id}_daily.md
```

## 输出
- **群内**：日报摘要（简短）
- **文件**：日报文件 + trends.csv 追加

## 注意事项
- 日报不是流水账，重点是数据汇总
- 多孩子不串台：文件名带 member_id
- trends.csv 用于周报聚合
- 家长代查要显式指定 target
