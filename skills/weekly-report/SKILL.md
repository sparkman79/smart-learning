---
name: weekly-report
description: 生成周报与趋势回看：weekly 报告落盘到 reports/weekly，并支持 /趋势 4 周查询
user-invocable: true
---

## 指令
- `/周报` - 生成本周学习周报
- `/周报 周=YYYY-Www` - 生成指定周周报（可选）
- `/趋势 4 周` - 查看最近 4 周趋势

## 身份与权限
- **kid**：只能看自己周报
- **parent**：可看自己 + linked_children 的周报
- **admin**：可看家庭汇总周报

## 数据源
- `data/reports/daily/` - 日报文件
- `data/reports/trends/trends.csv` - 趋势数据
- `data/mistakes/` - 错题库（可选增强）

## 行为

### 1. 生成周报
```
读取本周所有日报文件，聚合计算：
1. 总学习时长
2. 番茄钟总轮次
3. 完成任务数（完成/总数）
4. 对比上周的涨跌变化
5. Top 3 卡点/错因（如有）
```

**周报模板**：
```markdown
# 周报 {YYYY-Www}（{member_id}）

## 本周概览
- 总学习时长：{XX} 分钟
- 番茄钟总轮次：{XX}
- 完成任务数：{完成/总数}

## 完成度趋势（对比上周）
- 时长：↑/↓（{变化值} 分钟）
- 轮次：↑/↓（{变化值}）
- 完成度：↑/↓（{变化值}%）

## 薄弱点趋势（Top 3）
1) {Top 卡点/错因}
2) {Top 卡点/错因}
3) {Top 卡点/错因}

## 下周只抓 1 个重点
- 重点：{最关键的一个改进方向}
- 建议策略：{具体建议}
```

### 2. 查询趋势
```
读取 trends.csv，输出最近 4 周的关键指标：
```
📈 近 4 周趋势
第 1 周：{XX} 分钟 | {XX} 轮 | {XX%} 完成
第 2 周：{XX} 分钟 | {XX} 轮 | {XX%} 完成
第 3 周：{XX} 分钟 | {XX} 轮 | {XX%} 完成
第 4 周：{XX} 分钟 | {XX} 轮 | {XX%} 完成
```

### 3. 落盘
```
文件：data/reports/weekly/YYYY-Www_{member_id}_weekly.md
```

## 输出
- **群内**：周报摘要 + "文件已生成"
- **文件**：`data/reports/weekly/YYYY-Www_{member_id}_weekly.md`

## 注意事项
- 周报不是重复日报，重点是变化和趋势
- 多孩子报告不串台：文件名必须带 member_id
- 家长代查要显式指定 target
- trends.csv 数据不足时，输出已有数据
