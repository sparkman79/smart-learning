# 智能学习系统资料 4：执行层 — 接入音响/台灯/Timer 学习节奏

## 来源
- 标题：用 OpenClaw 给孩子搭一套全科辅导系统（Plus版④）
- 作者：苹果落地
- 来源：人间折腾录
- 日期：2026 年 4 月 16 日

---

## 一、本篇目标

群里一句"开始学习"，家里设备**真的动起来**。

**验收点**：

| 触发 | 预期 |
|------|------|
| 群发"开始学习"/"开始阅读" | 音响播报开场、台灯切学习态、timer 启动 |
| timer 到点 | 自动进休息，再自动继续下一轮 |
| 群发"结束学习" | 灯光恢复日常态、音响提示收尾、timer 停止 |

> 交付不是"系统回复了开始学习"，而是现实世界的设备状态真的变化。

---

## 二、技术栈

| 组件 | 职责 |
|------|------|
| Home Assistant | Scripts、Timer、Automations |
| OpenClaw Skill `study-mode` | 接群指令、调 HA、写状态机 |
| 音响 `media_player.xxx` | 播报 |
| 台灯 `light.xxx` | 状态指示 |
| `data/routines/state.json` | 状态文件（核心） |

> OpenClaw 负责触发和状态，设备动作尽量交给 HA。

---

## 三、HA 最小执行层

### 1️⃣ Timer：timer.study_pomodoro

**UI 创建**：Helpers → Timer → 名称 `study_pomodoro` → 默认时长 `00:25:00`

**YAML**：
```yaml
timer:
  study_pomodoro:
    duration: "00:25:00"
```

> 新手先只建一个学习 timer。休息 5 分钟先用 automation 的 delay 实现。

---

### 2️⃣ 三个核心脚本

#### script.study_start — 进入学习态

```yaml
script:
  study_start:
    alias: "Study Start"
    mode: restart
    fields:
      message:
        description: "播报文本（可选）"
        example: "开始学习，本轮 25 分钟。"
    sequence:
      - service: light.turn_on
        target:
          entity_id: light.study_lamp
        data:
          brightness_pct: 90
          color_temp: 250
      - service: tts.google_translate_say
        target:
          entity_id: media_player.xiaoai_speaker
        data:
          message: "{{ message | default('开始学习，本轮 25 分钟。') }}"
      - service: timer.start
        target:
          entity_id: timer.study_pomodoro
        data:
          duration: "00:25:00"
```

**三件事一次完成**：灯切换 → 音响播报 → timer 启动

---

#### script.study_break — 休息态

```yaml
script:
  study_break:
    alias: "Study Break"
    mode: restart
    sequence:
      - service: light.turn_on
        target:
          entity_id: light.study_lamp
        data:
          brightness_pct: 40
          color_temp: 400
      - service: tts.google_translate_say
        target:
          entity_id: media_player.xiaoai_speaker
        data:
          message: "休息 5 分钟，喝水走动，护眼看远处 20 秒。"
```

> 重点不是设备越多越好，而是**状态切换要明显**。

---

#### script.study_end — 恢复环境

```yaml
script:
  study_end:
    alias: "Study End"
    mode: restart
    sequence:
      - service: light.turn_on
        target:
          entity_id: light.study_lamp
        data:
          brightness_pct: 60
          color_temp: 350
      - service: tts.google_translate_say
        target:
          entity_id: media_player.xiaoai_speaker
        data:
          message: "学习结束。请用 30 秒说一句今天学到的，或在群里回复：已完成。"
      - service: timer.cancel
        target:
          entity_id: timer.study_pomodoro
```

---

## 四、Automation：timer 到点自动推进

**关键**：不是手动点脚本，而是 timer 自动推节奏。

```yaml
automation:
  - alias: "Study Pomodoro Finished -> Break -> Continue"
    mode: single
    trigger:
      - platform: event
        event_type: timer.finished
        event_data:
          entity_id: timer.study_pomodoro
    action:
      - service: script.study_break
      - delay: "00:05:00"
      - service: script.study_start
        data:
          message: "休息结束，继续下一轮 25 分钟。"
```

**第一版节奏闭环**：开始 → 25 分钟 → 休息 → 继续下一轮

> 先不处理"做几轮后自动结束"，那是后面状态机和策略层的事。

---

## 五、OpenClaw：study-mode Skill

**职责**：识别指令 → 找成员 → 调 HA → 写状态

### 1️⃣ 状态文件 data/routines/state.json

```json
{
  "mode": "idle",
  "current_member_id": null,
  "session": {
    "started_at": null,
    "pomodoro_minutes": 25,
    "break_minutes": 5,
    "round": 0
  }
}
```

**记录四类信息**：当前模式、当前学习者、开始时间、轮次

---

### 2️⃣ SKILL.md 核心规则

```markdown
## 指令
- /开始学习
- /开始阅读
- /结束学习
- /结束

## 行为规则
1) 识别 sender_openid → member_id/role（用 index.json）
2) 写入/更新 state.json：
   - 开始：mode=study, current_member_id, started_at, round=1
   - 结束：mode=idle, 清空 current_member_id
3) 调用 Home Assistant 脚本：
   - 开始：POST script.study_start（传 message）
   - 结束：POST script.study_end

## HA 调用
POST /api/services/script/turn_on
Headers: Authorization: Bearer ${HA_TOKEN}
Body: {
  "entity_id": "script.study_start",
  "variables": {"message": "开始学习，本轮 25 分钟。"}
}

## 输出策略
- kid：短输出 ≤6 行
- parent/admin：允许提示当前状态和如何结束
```

**两个注意点**：
1. HA_TOKEN 和 HA_URL 配成环境变量，不要写死
2. 如果 HA 不支持 variables，message 固定写在脚本里也行

---

## 六、执行链路全景

### 🚀 开始学习

```
群指令 /开始学习
    ↓
OpenClaw（三件事）
    ├── 根据 openid 识别成员
    ├── 更新 state.json（mode=study）
    └── 调用 script.study_start
    ↓
Home Assistant（三件事）
    ├── 台灯切学习态
    ├── 音响播报开场
    └── timer 启动
```

### 🔄 节奏推进

```
timer.finished 事件
    ↓
automation 触发
    ├── script.study_break（灯光 + 播报休息）
    ├── delay 5 分钟
    └── script.study_start（继续下一轮）
```

### ⏹ 结束学习

```
群指令 /结束学习
    ↓
OpenClaw
    ├── state.json → mode=idle
    └── 调用 script.study_end
    ↓
Home Assistant
    ├── 灯光恢复日常态
    ├── 音响播报收尾
    └── timer.cancel
```

---

## 七、验收步骤

### Step A：HA 侧自检（先验 HA，再验 OpenClaw）

手动执行 `script.study_start`，检查：
- ✅ 台灯是否切到学习态
- ✅ 音响是否播报
- ✅ timer 是否启动

> 测试时把 duration 临时改成 10 秒，快速验证 automation 触发：
> `duration: "00:00:10"`

### Step B：OpenClaw 触发

群发 `/开始学习`，检查：
- ✅ 音响播报、灯变化、timer 启动
- ✅ OpenClaw 群内短确认
- ✅ state.json → mode=study

### Step C：结束流程

群发 `/结束学习`，检查：
- ✅ 灯光恢复日常态
- ✅ 音响提示收尾
- ✅ timer 被 cancel
- ✅ state.json → mode=idle

---

## 八、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 音响不播报 | TTS 未启用 / media_player 错误 | 先在 HA 开发者工具手动调用 TTS 测通 |
| 灯不支持 color_temp | 设备字段差异 | 只传设备支持的字段，先跑通"能切状态" |
| timer.finished 不触发 | trigger 写法或 entity_id 错误 | 检查 event_type + entity_id，看 HA Trace |
| OpenClaw 调 HA 返回 401/403 | TOKEN 错误/过期，URL 不通 | 检查 HA_TOKEN，确认 IP 和端口互通 |

---

## 九、小结

**本篇完成后，学习系统第一次真正具备了执行能力。**

> "开始学习"不再是一句提醒，而是一条真实的设备联动链路：

```
群指令 → OpenClaw 路由 → Home Assistant 执行 → 音响播报 + 台灯切换 + timer 推进 → 收尾恢复
```

**这一层打通后，后面所有功能才有落点**：

| 下游功能 | 依赖此层什么 |
|----------|------------|
| 未确认升级 | 读 state.json |
| 家长组合计划 | 改节奏参数 |
| 日报周报 | 知道学习何时开始和结束 |

**核心价值**：把系统从"能给计划"推进到"能推动执行"。

---

## 后续预告

下一篇：确认与升级机制
- 开始后孩子没确认，系统怎么提醒
- 提醒后仍未响应，何时通知家长
- 夜间静默策略如何接入
- state.json 扩展为可升级的状态机
