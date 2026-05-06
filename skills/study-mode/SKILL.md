---
name: study-mode
description: 管理学习模式：开始/结束学习，联动 Home Assistant（音响播报 + 台灯状态 + Timer 推进）
user-invocable: true
---

## 指令
- `/开始学习` - 启动学习模式
- `/结束学习` - 结束学习模式
- `/学习状态` - 查询当前学习状态

## 身份与权限
- 所有人可触发开始/结束
- 家长可强制结束他人学习

## 数据源
- `data/routines/state.json` - 状态机唯一数据源
- `data/routines/policies.json` - 策略配置
- `data/routines/plans/` - 学习计划模板
- `data/homework/parsed/` - 今日作业计划

## 行为

### 1. 开始学习流程
```
1. 读取 state.json，确认当前不在学习中
2. 读取今日作业计划（parsed）
3. 读取策略配置（policies.json）
4. 更新 state.json：mode=learning, current_member_id, started_at
5. 调用 HA API 触发执行链路
6. 群内播报：学习开始 + 第一关信息
```

**HA 联动**：
```yaml
# 执行脚本
script.study_start:
  data:
    member_id: kid_1
    first_task: 数学口算 40 题
    pomodoro: 25 分钟

# 音响播报
media_player.play_media:
  entity_id: media_player.study_speaker
  media_content_id: "学习开始！第一关：数学口算 40 题，请开始！"
  media_content_type: text

# 台灯状态
light.turn_on:
  entity_id: light.study_lamp
  rgb_color: [0, 128, 255]  # 蓝色 = 学习中

# Timer 启动
timer.start:
  entity_id: timer.study_pomodoro
  duration: "PT25M"  # 25 分钟
```

### 2. 结束学习流程
```
1. 读取 state.json，确认学习中
2. 计算学习时长
3. 调用 HA 停止 Timer、重置台灯
4. 更新 state.json：mode=idle, session.completed
5. 群内播报：学习结束 + 时长统计
6. 触发日报生成（如到日报时间）
```

**HA 联动**：
```yaml
# 停止 Timer
timer.stop:
  entity_id: timer.study_pomodoro

# 重置台灯（绿色 = 完成）
light.turn_on:
  entity_id: light.study_lamp
  rgb_color: [0, 255, 0]

# 音响播报
media_player.play_media:
  entity_id: media_player.study_speaker
  media_content_id: "学习结束！本次学习 XX 分钟，休息一下吧！"
  media_content_type: text

# 重置台灯（白色 = 空闲）
light.turn_on:
  entity_id: light.study_lamp
  rgb_color: [255, 255, 255]
```

### 3. 学习状态查询
```
查询 state.json，返回：
- 当前模式（idle/learning/break）
- 当前成员
- 已学习时长
- 当前任务
- 番茄钟轮次
```

## 输出
- **群内**：学习开始/结束播报 + 任务信息
- **文件**：更新 state.json
- **HA**：触发设备联动

## 注意事项
- 状态机驱动，state.json 是唯一数据源
- 番茄钟时长从策略配置读取
- 学习中途 interruption 要妥善处理
- 多孩子场景下，确保 member_id 路由正确
