# 智能学习系统（Plus 版）

> 基于飞书机器人 + OpenClaw 的家庭全科辅导系统

## 系统架构（3 层）

```
策略层（家长组合计划 / 四旋钮调参）
    ↓
执行层（作业拆解 + 学习模式 + 升级提醒）
    ↓
数据沉淀（日报 + 周报 + 趋势回看）
```

### 策略层
- 四套计划模板：轻量 / 标准 / 冲刺 / 共读
- 四旋钮：番茄钟时长、休息时长、升级强度、夜间模式
- 家长专属权限，孩子不可修改

### 执行层
- 作业输入 → 自动拆解为 5-20 分钟颗粒任务
- 双视图：孩子版（简洁）+ 家长版（含检查点）
- 状态机驱动：idle → learning → break → completed
- 阶段化升级提醒：未确认 → 轻提醒 → 严肃提醒 → 家长通知

### 数据沉淀
- 日报：每日自动生成，含任务完成率 + 评分
- 周报：每周汇总，对比上周涨跌
- 趋势：trends.csv 沉淀，支持多周回看

## 快速开始

### 1. 配置飞书机器人

复制配置模板并填入真实值：
```bash
cp feishu/config.json.example feishu/config.json
# 编辑 config.json，填入 app_id / app_secret / verify_token
```

### 2. 配置成员索引

编辑 `data/family/members/index.json`，填入实际飞书 open_id：

```json
{
  "family_id": "FAMILY_001",
  "members": {
    "kid_1": {
      "name": "小明",
      "role": "kid",
      "open_ids": { "feishu": "ou_xxxxxxxxxxxx" }
    }
  }
}
```

### 3. 启动飞书 Webhook 服务

```bash
pip install -r requirements.txt
python feishu/adapter.py
```

### 4. 配置定时任务

在 `cron/jobs.json` 中添加升级检查任务：
```json
{
  "id": "study_escalation",
  "name": "学习升级检查",
  "schedule": "*/1 * * * *",
  "skill": "study-escalation",
  "enabled": true
}
```

## 指令速查

| 指令 | 触发者 | 功能 |
|------|--------|------|
| `/作业` | 所有人 | 提交作业 |
| `/开始学习` | 所有人 | 启动学习模式 |
| `/确认 已开始` | 孩子 | 确认开始 |
| `/确认 已完成` | 孩子 | 确认完成 |
| `/结束学习` | 所有人 | 结束学习 |
| `/日报` | 家长 | 生成日报 |
| `/周报` | 家长 | 生成周报 |
| `/切换计划 轻量` | 家长 | 切换计划 |
| `/设置 节奏=25/5` | 家长 | 调整策略 |

## 目录结构

```
smart-learning/
├── feishu/              # 飞书 Bot 适配器
│   ├── adapter.py       # 消息路由 + 指令处理
│   ├── config.json      # 飞书配置（不提交）
│   └── config.json.example
├── skills/              # OpenClaw Skills（8 个）
│   ├── homework-intake/ # 作业拆解 + 双视图
│   ├── study-mode/      # 学习模式管理
│   ├── study-ack/       # 确认机制
│   ├── study-escalation/# 升级提醒
│   ├── plan-builder/    # 计划模板管理
│   ├── member-registry/ # 成员注册
│   ├── daily-report/    # 日报生成
│   └── weekly-report/   # 周报 + 趋势
├── data/
│   ├── family/          # 成员索引
│   ├── homework/        # 作业数据（inbox → parsed）
│   ├── routines/        # 状态机 + 策略
│   └── reports/         # 日报 + 周报 + 趋势
├── tests/               # 集成测试 + 端到端测试
├── archive_20260505/    # 历史参考文档
└── requirements.txt     # Python 依赖
```

## 四套计划模板

| 模板 | 番茄钟 | 升级 | 适用场景 |
|------|--------|------|---------|
| 轻量 | 15min | 关闭 | 情绪友好、先求开始 |
| 标准 | 25min | 5/10min | 日常主力 |
| 冲刺 | 30min | 3/6min | 考试前 |
| 共读 | 20min | 关闭 | 周末亲子 |

## 注意事项

1. 所有识别只认 open_id，不认昵称
2. 文件名必须含 member_id，多孩子不串台
3. 权限基于 role，kid 不能改策略
4. 只改 policies.json，不改系统配置
5. 升级判断顺序：mode → ack_start → elapsed → stage
6. **config.json 包含密钥，切勿提交到 Git**
