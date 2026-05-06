# Phase 2: Home Assistant 设备配置验证清单

## 准备工作

### 1. 确认你的设备实体 ID

在 HA 中查看实际实体 ID（不是 friendly_name）：

**方法 A：HA 界面**
1. 进入 `设置 → 设备与服务 → 实体`
2. 找到你的台灯，复制 entity_id（如 `light.living_room_lamp`）
3. 找到你的音响，复制 entity_id（如 `media_player.xiaomi_speaker`）
4. 确认 TTS 服务是否可用（检查是否有 `tts.*` 服务）

**方法 B：HA 开发者工具**
1. 进入 `工具 → 开发者工具 → 服务`
2. 搜索 `light.turn_on`，看能否列出你的台灯
3. 搜索 `tts.*_say`，看有哪些 TTS 服务可用

### 2. 你的实体 ID 是什么？

请回复以下信息，我会生成定制化的 config.yaml：

```
台灯实体 ID: ?
音响实体 ID: ?
TTS 服务: ?（如 tts.google_translate_say, tts.xiaomi_say_tts 等）
HA 版本: ?（2024.x / 2025.x / 2026.x）
```

---

## 如果暂时不知道实体 ID

可以先用 HA 的**测试模式**（不需要真实设备也能验证逻辑）：

### 测试脚本（虚拟设备）

```yaml
# 用输入选择器替代真实灯
input_boolean:
  study_lamp_on:
    name: "学习台灯"
    initial: off

# 用通知替代真实音响
# notification 服务默认可用，不需要额外配置

script:
  study_start_test:
    alias: "Study Start (Test)"
    mode: restart
    sequence:
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.study_lamp_on
      - service: persistent_notification.create
        data:
          title: "学习开始"
          message: "本轮 25 分钟。"
      - service: timer.start
        target:
          entity_id: timer.study_pomodoro
      - service: persistent_notification.create
        data:
          title: "学习提醒"
          message: "台灯已打开、计时已启动"

  study_break_test:
    alias: "Study Break (Test)"
    mode: restart
    sequence:
      - service: persistent_notification.create
        data:
          title: "休息提醒"
          message: "休息 5 分钟，喝水走动，护眼看远处 20 秒。"

  study_end_test:
    alias: "Study End (Test)"
    mode: restart
    sequence:
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.study_lamp_on
      - service: persistent_notification.create
        data:
          title: "学习结束"
          message: "灯光已恢复，计时已停止。"
      - service: timer.cancel
        target:
          entity_id: timer.study_pomodoro
```

这个测试版不需要任何真实设备，直接用 HA 的通知面板就能验证整套逻辑是否跑通。

---

## 验证步骤（设备就绪后）

### Step 1: HA 侧自检
1. 在 HA 中手动执行 `script.study_start`
2. 检查：台灯是否切换 → 音响是否播报 → Timer 是否启动
3. 建议先改 duration 为 10 秒快速测试

### Step 2: OpenClaw 侧验证
1. 确保 `HA_URL` 和 `HA_TOKEN` 配置正确
2. 在群里发 `/开始学习`
3. 检查：state.json → mode=study，HA 执行脚本

### Step 3: 完整链路验证
1. 发 `/开始学习` → 检查三件套（灯+音+timer）
2. 等 timer 结束 → 检查休息脚本是否触发
3. 发 `/结束学习` → 检查收尾流程
4. 检查 `state.json` 是否正确记录

---

## 常见问题排查

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 音响不播报 | TTS 服务未启用或实体 ID 错误 | 在开发者工具单独测试 TTS |
| 灯不切换 | 实体 ID 错误 | 检查 entity_id 是否拼写正确 |
| 401/403 | HA_TOKEN 过期或错误 | 重新生成 long-lived access token |
| 网络不通 | OpenClaw 和 HA 不在同网段 | 确认 IP 和端口互通 |
| timer 不触发 | automation 配置有误 | 检查 trigger 的 entity_id |
