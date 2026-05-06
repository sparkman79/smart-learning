---
name: study-ack
description: 学习确认机制：开始确认 + 完成确认，阻止升级链路重复触发
user-invocable: true
---

## 指令
- `/确认 已开始` - 孩子确认已开始学习
- `/确认 已完成` - 孩子确认已完成学习

## 身份与权限
- **kid**：只能确认自己的学习
- **parent/admin**：可确认他人学习状态

## 数据源
- `data/routines/state.json` - 状态机唯一数据源
- `data/routines/policies.json` - 策略配置（升级链路开关）

## 行为

### 1. 开始确认（ack_start）
```
当孩子回复"已开始"或发送/确认 已开始时：
1. 读取 state.json，确认 mode=learning
2. 更新 session.ack_start=true, session.ack_start_at=当前时间
3. 阻止 escalation 链路继续推送
4. 群内播报：收到，开始加油！
```

**state.json 更新**：
```json
{
  "mode": "learning",
  "session": {
    "ack_start": true,
    "ack_start_at": "2026-05-05T19:30:00+08:00"
  }
}
```

### 2. 完成确认（ack_done）
```
当孩子回复"已完成"或发送/确认 已完成时：
1. 读取 state.json，确认 mode=learning
2. 更新 session.ack_done=true, session.ack_done_at=当前时间
3. 计算实际学习时长
4. 停止 escalation 链路
5. 触发结束学习流程
```

**state.json 更新**：
```json
{
  "mode": "learning",
  "session": {
    "ack_done": true,
    "ack_done_at": "2026-05-05T20:30:00+08:00"
  }
}
```

### 3. 升级链路停止逻辑
```
escalation 每分钟检查：
1. 读取 state.json
2. 检查 session.ack_start 和 session.ack_done
3. 如果任一为 true，停止推送提醒
```

## 输出
- **群内**：确认回复 + 简短鼓励
- **文件**：更新 state.json

## 注意事项
- 确认是"软性"的，不强制孩子回复
- 未确认时，escalation 链路按策略推送提醒
- 多孩子场景下，确保 member_id 路由正确
- 确认时间用于计算实际学习时长
