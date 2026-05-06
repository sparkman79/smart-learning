# 智能学习系统（Plus 版）

> 基于 OpenClaw + 微信群/飞书 + Home Assistant 的家庭全科辅导系统

## 系统架构

```
策略层（家长组合计划）
    ↓
执行层（智能家居联动）
    ↓
内容层（作业拆解 + 双视图）
    ↓
数据沉淀（日报 + 周报 + 趋势）
```

## 快速开始

### 1. 配置环境变量

```bash
# Home Assistant
HA_URL=http://<ha-ip>:8123
HA_TOKEN=<long-lived-token>

# LLM（可选，增强作业理解）
LLM_API_KEY=<your-key>
LLM_MODEL=<model-name>
```

### 2. 配置成员索引

编辑 `data/family/members/index.json`，填入实际 openid：

```json
{
  "family_id": "FAMILY_001",
  "members": [
    {
      "openid": "你的微信openid",
      "member_id": "kid_1",
      "role": "kid",
      "display_name": "孩子昵称",
      "created_at": "2026-05-05"
    }
  ]
}
```

### 3. 配置 Home Assistant

参考 `homeassistant/config.yaml` 配置：
- Timer: `timer.study_pomodoro`
- Scripts: `study_start`, `study_break`, `study_end`, `study_soft_nudge`, `study_night_silent_nudge`
- Automation: timer 完成 → 休息 → 继续

### 4. 配置 OpenClaw 定时任务

在 `cron/jobs.json` 中添加：

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
smart_learning/
├── skills/              # OpenClaw Skills
├── data/
│   ├── family/          # 成员索引
│   ├── homework/        # 作业数据
│   ├── routines/        # 状态机 + 策略
│   └── reports/         # 日报 + 周报 + 趋势
└── homeassistant/       # HA 配置（待创建）
```

## 四套计划模板

| 模板 | 番茄钟 | 升级 | 适用场景 |
|------|--------|------|---------|
| 轻量 | 15min | 关闭 | 情绪友好、先求开始 |
| 标准 | 25min | 5/10min | 日常主力 |
| 冲刺 | 30min | 3/6min | 考试前 |
| 共读 | 20min | 关闭 | 周末亲子 |

## 实施阶段

- **Phase 1**：基础跑通（目录 + index.json + 核心 Skills）
- **Phase 2**：HA 设备配置（Timer + Scripts + Automation）
- **Phase 3**：定时任务 + 升级机制
- **Phase 4**：数据沉淀（日报/周报）
- **Phase 5**：策略可配置（模板 + 四旋钮）

## 注意事项

1. 所有识别只认 openid，不认昵称
2. 文件名必须含 member_id，多孩子不串台
3. 权限基于 role，kid 不能改策略
4. 只改 policies.json，不改 HA YAML
5. 升级判断顺序：mode → ack_start → elapsed → stage
