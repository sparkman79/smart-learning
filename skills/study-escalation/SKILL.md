---
name: study-escalation
description: 学习升级提醒：定时检查未确认/超时学习，阶段化推送提醒，触发 HA 设备联动
user-invocable: false  # 仅由 cron 任务自动触发
---

## 调度
- **触发方式**：OpenClaw cron 任务，每分钟执行
- **配置**：`cron/jobs.json` 中 `study_escalation` 任务

## 数据源
- `data/routines/state.json` - 状态机唯一数据源
- `data/routines/policies.json` - 策略配置（升级阶段、间隔）
- Home Assistant API - 设备联动

## 行为

### 1. 每分钟检查流程
```
1. 读取 state.json
2. 检查：mode == learning ?
3. 检查：session.ack_start == true ?
4. 检查：session.ack_done == true ?
5. 如果任一为 true，跳过（用户已确认）
6. 计算 elapsed_min = 当前时间 - session.started_at
7. 根据 elapsed_min 确定 escalation_stage
8. 检查 last_nudge_at，确认冷却时间
9. 推送提醒 + 触发 HA 设备
```

### 2. 升级阶段设计
| 阶段 | 超时分钟 | 提醒方式 | HA 联动 |
|------|---------|---------|---------|
| Stage 0 | 0 | 无（刚开始） | 无 |
| Stage 1 | 5-10 | 群内轻提醒 | 台灯闪烁（黄色） |
| Stage 2 | 15-20 | 群内严肃提醒 | 台灯常亮（黄色）+ 音响播报 |
| Stage 3 | 25-30 | 家长通知 | 台灯闪烁（红色）+ 音响播报 + 推送家长 |

**策略可配置**：
```json
{
  "escalation": {
    "enabled": true,
    "stages": [
      { "stage": 1, "elapsed_min": 5, "nudge": "light_yellow_blink" },
      { "stage": 2, "elapsed_min": 15, "nudge": "light_yellow_solid + notify" },
      { "stage": 3, "elapsed_min": 25, "nudge": "light_red_blink + parent_notify" }
    ]
  }
}
```

### 3. HA 设备联动

**台灯状态**：
```yaml
# 黄色闪烁（轻度提醒）
script.study_soft_nudge:
  data:
    action: "blink"
    color: [255, 255, 0]  # 黄色

# 红色闪烁（严重提醒 + 家长通知）
script.study_night_silent_nudge:
  data:
    action: "blink"
    color: [255, 0, 0]  # 红色
```

**音响播报**：
```yaml
media_player.play_media:
  entity_id: media_player.study_speaker
  media_content_id: "注意时间哦，已经学习 XX 分钟了！"
  media_content_type: text
```

### 4. 冷却时间控制
```
- last_nudge_at 记录上次推送时间
- 同一阶段内，冷却时间 >= 5 分钟
- 阶段升级后，冷却时间重置
```

## 输出
- **群内**：阶段化提醒（根据 stage）
- **HA**：台灯状态 + 音响播报
- **文件**：更新 state.json（last_nudge_at, escalation_stage）

## 注意事项
- 升级判断顺序：mode → ack_start → elapsed → stage
- 孩子确认（ack）后，立即停止推送
- 冷却时间避免消息轰炸
- 家长通知仅在 stage 3 触发
- 夜间模式（22:00-07:00）关闭音响，仅台灯提醒
