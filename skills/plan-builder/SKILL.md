---
name: plan-builder
description: 学习计划模板管理：切换计划模板，四旋钮策略调参，家长专属权限
user-invocable: true
---

## 指令
- `/切换计划 轻量` - 切换到轻量计划
- `/切换计划 标准` - 切换到标准计划
- `/切换计划 冲刺` - 切换到冲刺计划
- `/切换计划 共读` - 切换到共读计划
- `/设置 节奏=25/5` - 调整番茄钟节奏
- `/设置 升级=开启/关闭` - 调整升级提醒
- `/设置 夜间=开启/关闭` - 调整夜间模式

## 身份与权限
- **parent/admin**：可修改策略
- **kid**：❌ 禁止修改策略

## 数据源
- `data/routines/plans/` - 四套计划模板
- `data/routines/policies.json` - 当前策略配置

## 行为

### 1. 切换计划模板
```
支持 4 套模板：
- 轻量：15 分钟番茄钟，关闭升级
- 标准：25 分钟番茄钟，5/10 分钟升级
- 冲刺：30 分钟番茄钟，3/6 分钟升级
- 共读：20 分钟番茄钟，关闭升级（亲子模式）
```

**模板示例（standard.json）**：
```json
{
  "name": "标准计划",
  "pomodoro": {
    "work": 25,
    "break": 5
  },
  "escalation": {
    "enabled": true,
    "stages": [
      { "stage": 1, "elapsed_min": 5 },
      { "stage": 2, "elapsed_min": 10 }
    ]
  }
}
```

### 2. 四旋钮调参
```
家长可通过对话调整：
- 节奏旋钮：番茄钟工作/休息时长（如 25/5, 30/10）
- 升级旋钮：升级提醒开关 + 阶段间隔
- 夜间旋钮：夜间模式开关 + 安静时段
- 计划旋钮：切换计划模板
```

### 3. 策略合并
```
plan-builder 将模板的 policy_patch 合并覆盖至 policies.json
保留未冲突字段，支持灵活调参
```

**policies.json 更新**：
```json
{
  "pomodoro": { "work": 25, "break": 5 },
  "escalation": { "enabled": true, "stages": [...] },
  "night_mode": { "enabled": false, "start": "22:00", "end": "07:00" }
}
```

## 输出
- **群内**：策略变更确认 + 新策略摘要
- **文件**：更新 policies.json
- **日志**：记录变更到 policy_changes.log

## 注意事项
- kid 禁止修改策略，需检查 role
- 策略变更记录日志，便于追溯
- 模板切换后，当前学习会话不受影响（下次开始生效）
- 四旋钮调参实时生效
