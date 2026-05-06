# 智能学习系统（Plus 版）完整设计方案

> 基于 7 篇系列文章的系统化落地方案
> 基于 OpenClaw + 微信群/飞书 + Home Assistant 的家庭全科辅导系统
> 版本：v1.0 | 日期：2026-05-05

---

## 一、系统全景架构

### 1.1 核心设计理念

传统 AI 学习系统停在"讲题/给建议"，但真实问题不是 AI 不够聪明，而是**缺少从指令到执行的完整链路**。

系统从"给建议"升级为"推动执行"：
- 孩子：不需要动脑子想下一步，环境自动驱动
- 家长：不需要改底层代码，切计划 + 调旋钮即可
- 系统：数据持续沉淀，策略可回滚可审计

### 1.2 三层架构

```
┌──────────────────────────────────────────────────────────────┐
│                    策略层（家长组合计划）                        │
│  ┌───────────────────────────────────────────────────────┐   │
│  │ plan-builder Skill | 模板切换 | 四旋钮配置 | policies.json│  │
│  └───────────────────────────────────────────────────────┘   │
│  家长操作：/切换计划 | /设置 节奏=25/5 | 强度=低 | 升级=10    │
├──────────────────────────────────────────────────────────────┤
│                    执行层（智能家居联动）                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │study-mode│  │study-ack │  │escalation│  │daily/weekly- │  │
│  │ Skill    │  │ Skill    │  │ Skill    │  │report Skill  │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │
│  ↓ Home Assistant ↓                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │音响播报   │  │台灯切换   │  │Timer 推进 │                      │
│  │TTS 开场  │  │学习态/休息态│  │pomodoro  │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
├──────────────────────────────────────────────────────────────┤
│                    内容层（学习主干）                            │
│  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │homework-intake       │  │成员索引 | 权限路由            │  │
│  │Skill                │  │index.json | role → 目录        │  │
│  └──────────────────────┘  └──────────────────────────────┘  │
│  ↓ 拆解 → 双视图 → 落盘                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │inbox/    │  │parsed/   │  │done/     │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

### 1.3 数据流

```
微信群/飞书群消息
    │
    ▼
┌─────────────┐     ┌──────────────┐
│ openid 路由  │────▶│ member_id    │
│ index.json  │     │ role → 目录   │
└─────────────┘     └──────────────┘
    │                     │
    ▼                     ▼
┌─────────────┐     ┌──────────────┐
│ 作业拆解     │     │ 学习执行      │
│ homework-   │     │ study-mode   │
│ intake      │     │ study-ack    │
└─────────────┘     │ escalation   │
    │               └──────┬───────┘
    │                      │
    ▼                      ▼
┌─────────────┐     ┌──────────────┐
│ 落盘        │     │ Home Assistant│
│ inbox/      │     │ 音响+台灯+Timer│
│ parsed/     │     └──────┬───────┘
└──────┬──────┘            │
       │                   │
       ▼                   ▼
┌──────────────────────────────────┐
│         数据沉淀                   │
│  reports/daily/   weekly/        │
│  trends/trends.csv                │
└──────────────────────────────────┘
```

---

## 二、完整目录结构

```
workspace/
├── skills/
│   ├── homework-intake/           # 作业拆解 Skill
│   │   └── SKILL.md
│   ├── study-mode/                # 学习执行 Skill
│   │   └── SKILL.md
│   ├── study-ack/                 # 确认机制 Skill
│   │   └── SKILL.md
│   ├── study-escalation/          # 升级机制 Skill
│   │   └── SKILL.md
│   ├── daily-report/              # 日报生成 Skill
│   │   └── SKILL.md
│   ├── weekly-report/             # 周报生成 Skill
│   │   └── SKILL.md
│   └── plan-builder/              # 组合计划 Skill
│       └── SKILL.md
├── data/
│   ├── family/
│   │   ├── members/
│   │   │   └── index.json         # 成员索引（核心底表）
│   │   └── shared/                # 家庭公共数据
│   ├── members/
│   │   ├── kid_1/                 # 孩子个人数据
│   │   │   ├── homework/
│   │   │   └── reports/
│   │   ├── parent_1/              # 家长个人数据
│   │   │   └── reports/
│   │   └── admin_1/               # 管理员个人数据
│   │       └── reports/
│   ├── homework/
│   │   ├── inbox/                 # 原始作业输入
│   │   ├── parsed/                # 拆解后计划
│   │   └── done/                  # 完成归档（预留）
│   ├── routines/
│   │   ├── state.json             # 状态机（核心运行数据）
│   │   ├── policies.json          # 当前生效策略配置
│   │   ├── plans/                 # 计划模板库
│   │   │   ├── light.json         # 轻量模板
│   │   │   ├── standard.json      # 标准模板
│   │   │   ├── sprint.json        # 冲刺模板
│   │   │   └── family_read.json   # 共读模板
│   │   └── logs/
│   │       └── policy_changes.log # 审计日志
│   ├── mistakes/                  # 错题/疑问（预留）
│   └── reports/
│       ├── daily/                 # 日报
│       ├── weekly/                # 周报
│       └── trends/
│           └── trends.csv         # 趋势数据源
├── routines/
│   └── state.json                 # （旧路径兼容，建议迁移到 data/routines/）
└── logs/
    └── actions.log                # 执行日志
```

---

## 三、各模块详细设计

### 3.1 成员索引（index.json）

**路径**：`data/family/members/index.json`

```json
{
  "family_id": "FAMILY_001",
  "members": [
    {
      "openid": "openid_admin_1",
      "member_id": "admin_1",
      "role": "admin",
      "display_name": "家长管理员",
      "linked_children": ["kid_1", "kid_2"],
      "created_at": "2026-05-05"
    },
    {
      "openid": "openid_parent_1",
      "member_id": "parent_1",
      "role": "parent",
      "display_name": "家长A",
      "linked_children": ["kid_1"],
      "created_at": "2026-05-05"
    },
    {
      "openid": "openid_kid_1",
      "member_id": "kid_1",
      "role": "kid",
      "display_name": "小明",
      "created_at": "2026-05-05"
    }
  ]
}
```

**关键设计点**：
- `member_id` 是系统内部身份，不直接用 openid 作为目录名
- `role` 必须显式记录，不靠目录名猜
- `linked_children` 定义家长与孩子关系，用于摘要隔离
- 所有识别只认 `openid`，昵称仅作 `display_name`

### 3.2 角色与权限矩阵

| 操作 | kid | parent | admin |
|------|-----|--------|-------|
| 发作业/提交疑问 | ✅ | ✅ | ✅ |
| 发起开始学习 | ✅ | ✅ | ✅ |
| 做开始/完成确认 | ✅ | ✅ | ✅ |
| 查看自己的日报 | ✅ | ✅ | ✅ |
| 查看关联孩子摘要 | — | ✅ | ✅ |
| 查看家庭汇总/趋势 | — | — | ✅ |
| 切换计划模板 | — | ✅ | ✅ |
| 调四旋钮 | — | ✅ | ✅ |
| 修改升级策略 | — | ✅ | ✅ |
| 管理成员绑定 | — | — | ✅ |
| 执行/确认类管理动作 | — | — | ✅ |

**原则**：执行权尽量下放，配置权尽量收紧

### 3.3 状态机（state.json）

**路径**：`data/routines/state.json`

```json
{
  "mode": "idle",
  "current_member_id": null,
  "session": {
    "started_at": null,
    "ack_start": false,
    "ack_start_at": null,
    "ack_done": false,
    "ack_done_at": null,
    "pomodoro_minutes": 25,
    "break_minutes": 5,
    "round": 0,
    "escalation_stage": 0,
    "last_nudge_at": null,
    "last_notify_at": null
  }
}
```

**状态流转**：

```
mode: idle                          →  系统空闲
    │ /开始学习
    ▼
mode: study, round=1, stage=0       →  学习进行中，未确认
    │ 超 no_ack_minutes 未确认
    ▼
mode: study, stage=1                →  触发轻提醒
    │ 超 second_notice_minutes 仍未确认
    ▼
mode: study, stage=2                →  通知家长
    │ /确认 已开始
    ▼
ack_start=true, stage=0             →  已确认，升级停止
    │ ...继续学习...
    │ /确认 已完成
    ▼
ack_done=true, stage=0              →  完成确认
    │ /结束学习
    ▼
mode: idle, 清空 session            →  回到空闲
```

### 3.4 策略配置（policies.json）

**路径**：`data/routines/policies.json` — 当前生效配置

```json
{
  "pomodoro_minutes": 25,
  "break_minutes": 5,
  "reminder_intensity": "medium",
  "ack": {
    "start_required": true,
    "complete_required": true
  },
  "escalation": {
    "no_ack_minutes": 5,
    "second_notice_minutes": 10,
    "max_stage": 2
  },
  "night": {
    "enabled": true,
    "start": "22:00",
    "end": "06:00",
    "silent_speaker": true,
    "light_only": true
  },
  "current_plan": "standard"
}
```

**设计原则**：
- 模板（plans/*.json）是候选配置
- `policies.json` 是运行中的真实配置
- 模板通过 policy_patch 覆盖 policies.json
- **只改 JSON 文件，不改 HA 设备层 YAML**

### 3.5 四套计划模板

**轻量计划**（light.json）— 状态一般、先求愿意开始

| 参数 | 值 |
|------|---|
| 番茄钟 | 15 分钟 |
| 休息 | 5 分钟 |
| 强度 | low |
| 升级 | 关闭（max_stage=0）|
| 夜间 | 静默 |

**标准计划**（standard.json）— 日常主力

| 参数 | 值 |
|------|---|
| 番茄钟 | 25 分钟 |
| 休息 | 5 分钟 |
| 强度 | medium |
| 升级 | 5min 轻提醒 → 10min 家长通知 |
| 夜间 | 静默 |

**冲刺计划**（sprint.json）— 考试前、任务集中

| 参数 | 值 |
|------|---|
| 番茄钟 | 30 分钟 |
| 休息 | 5 分钟 |
| 强度 | high |
| 升级 | 3min 轻提醒 → 6min 家长通知 |
| 夜间 | 不静默 |

**共读计划**（family_read.json）— 周末亲子阅读

| 参数 | 值 |
|------|---|
| 番茄钟 | 20 分钟 |
| 休息 | 5 分钟 |
| 强度 | low |
| 升级 | 关闭（max_stage=0）|
| 夜间 | 静默 |

### 3.6 homework-intake 作业拆解

**输入协议**（两种）：

```
常规输入：
/作业 语文：…… 数学：…… 英语：…… 可用时间：60分钟 状态：一般

极简输入：
/作业 数学口算40题，应用题3题，英语背单词10个
```

**拆解硬约束**：
- 单任务 **5-20 分钟**（超出就拆，不足就并）
- 默认排序：先易后难 或 先交付后订正
- 不追求复杂推理，先控制格式、路径、粒度

**双视图输出**：

**孩子版**（6-10 行短句可执行）：
```
✅ 学习计划（预计 55 分钟）

第1关：数学口算（20分钟）
休息：5分钟
第2关：应用题（15分钟）
休息：5分钟
第3关：英语背单词（10分钟）

完成后回复"已完成"
```

**家长版**（含估时+顺序+检查点≤3）：
```
📋 学习计划总览

科目：数学（35分钟）+ 英语（10分钟）
总估时：45分钟 | 余量：15分钟

检查点：
1. 口算是否完成并订正
2. 应用题是否全部完成
3. 英语是否完成背诵打卡
```

**群输出策略**：短输出 + 可展开
```
已生成今日学习计划，预计 55 分钟。
先做第1关：数学口算。
完成后按顺序进入下一关。
家长回复 /展开家长版 查看检查点。
```

### 3.7 文件命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 原始输入 | `YYYY-MM-DD_member_id_homework.md` | `2026-05-05_kid_1_homework.md` |
| 拆解计划 | `YYYY-MM-DD_member_id_scope.md` | `2026-05-05_kid_1_数学_plan.md` |
| 日报 | `YYYY-MM-DD_member_id_daily.md` | `2026-05-05_kid_1_daily.md` |
| 周报 | `YYYY-Www_member_id_weekly.md` | `2026-W19_kid_1_weekly.md` |

> 文件名必须包含：**日期 + member_id**，多孩子场景不能省

### 3.8 日报/周报模板

**日报模板**：
```markdown
# 日报 2026-05-05（kid_1）

## 今日完成
- [x] 数学口算40题（20分钟）
- [x] 应用题3题（15分钟）

## 今日卡点（只写1个）
- 卡点：应用题第2题理解困难
- 可能原因：未掌握解题步骤

## 明日1个重点（只写1个）
- 明日重点：复习应用题解题步骤

## 数据摘要
- 学习时长：35分钟
- 番茄钟轮次：1
- 任务完成度：2/2
- 新增错题/疑问：1
```

**周报模板**：
```markdown
# 周报 2026-W19（kid_1）

## 本周概览
- 总学习时长：180分钟
- 番茄钟总轮次：6
- 完成任务数：15/18

## 完成度趋势（对比上周）
- 时长：↑ +20分钟
- 轮次：↑ +1
- 完成度：↑ 83%→88%

## 薄弱点趋势（Top 3）
1. 应用题理解困难（出现3次）
2. 英语单词拼写（出现2次）
3. 数学粗心计算错误（出现2次）

## 下周只抓1个重点
- 重点：应用题解题步骤训练
- 建议策略：每天额外加1道应用题专项练习
```

**趋势 CSV**：
```csv
date,member_id,minutes,rounds,homework_done,homework_total,questions_new,mistakes_new,top_blocker,plan_name
2026-05-05,kid_1,35,1,2,2,0,1,应用题理解,standard
```

---

## 四、完整执行链路

### 4.1 完整链路全景

```
Step 1: 接作业（homework-intake）
    孩子/家长发 /作业 ...
    → 拆解任务（5-20 分钟粒度）
    → 输出双视图（孩子版短/家长版展开）
    → 落盘 inbox/ + parsed/
    ↓
Step 2: 开始学习（study-mode）
    群里发 /开始学习
    → OpenClaw: openid → member_id → 查 policies.json
    → 更新 state.json: mode=study, round=1
    → 调 HA: script.study_start
    → 设备: 台灯切学习态 + 音响播报 + timer 启动
    → 群内: 短确认 "✅ 已进入学习模式"
    ↓
Step 3: 节奏推进（HA Automation）
    timer.finished → script.study_break（灯光+播报休息）
    → delay 5分钟
    → script.study_start（灯光+播报继续）
    → round++
    → 自动循环...
    ↓
Step 4: 确认机制（study-ack）
    孩子发 /确认 已开始 → ack_start=true, stage=0, 停止升级
    孩子发 /确认 已完成 → ack_done=true
    ↓
Step 5: 结束学习（study-mode）
    群里发 /结束学习
    → OpenClaw: state.json → mode=idle
    → 调 HA: script.study_end
    → 设备: 灯光恢复 + 音响收尾 + timer 取消
    ↓
Step 6: 日报沉淀（daily-report）
    手动 /日报 或 自动触发
    → 读取 state.json + parsed/ + mistakes/
    → 生成日报 → 落盘 reports/daily/
    → 追加 trends.csv
    ↓
Step 7: 策略调整（plan-builder）
    家长 /切换计划 轻量 | /设置 节奏=20/5
    → 写入 policies.json
    → 立刻影响执行层（不重启 HA）
```

### 4.2 升级链路

```
开始学习
    │
    ▼
mode=study, ack_start=false, stage=0
    │
    ├─ 孩子确认"已开始"
    │   → ack_start=true, stage=0, 停止升级 ✅
    │
    └─ 超时未确认（per policies.json）
        │
        ├─ 超 no_ack_minutes（如 5 分钟）
        │   → stage=1 → 触发 script.study_soft_nudge
        │   （白天：灯光+语音轻提醒 / 夜间：仅灯光提示）
        │
        └─ 超 second_notice_minutes（如 10 分钟）
            → stage=2 → 通知家长（摘要）
            （谁 + 状态 + 建议，不长篇解释）
```

### 4.3 夜间策略

```
policies.json 中配置：
  night:
    enabled: true
    start: "22:00"
    end: "06:00"
    silent_speaker: true
    light_only: true

夜间触发时：
  ✗ 不播报音响
  ✓ 灯光闪烁提示
  ✓ 家长通知仍保留
```

---

## 五、Home Assistant 设备配置

### 5.1 Timer

```yaml
timer:
  study_pomodoro:
    duration: "00:25:00"  # 可从 policies.json 参数化
```

### 5.2 核心脚本

**study_start**：
```yaml
script:
  study_start:
    alias: "Study Start"
    mode: restart
    sequence:
      - service: light.turn_on
        target: { entity_id: light.study_lamp }
        data: { brightness_pct: 90, color_temp: 250 }
      - service: tts.google_translate_say
        target: { entity_id: media_player.xiaoai_speaker }
        data: { message: "开始学习，本轮25分钟。" }
      - service: timer.start
        target: { entity_id: timer.study_pomodoro }
        data: { duration: "00:25:00" }
```

**study_break**：
```yaml
study_break:
  alias: "Study Break"
  mode: restart
  sequence:
    - service: light.turn_on
      target: { entity_id: light.study_lamp }
      data: { brightness_pct: 40, color_temp: 400 }
    - service: tts.google_translate_say
      target: { entity_id: media_player.xiaoai_speaker }
      data: { message: "休息5分钟，喝水走动，护眼看远处20秒。" }
```

**study_end**：
```yaml
study_end:
  alias: "Study End"
  mode: restart
  sequence:
    - service: light.turn_on
      target: { entity_id: light.study_lamp }
      data: { brightness_pct: 60, color_temp: 350 }
    - service: tts.google_translate_say
      target: { entity_id: media_player.xiaoai_speaker }
      data: { message: "学习结束。请在群里回复：已完成。" }
    - service: timer.cancel
      target: { entity_id: timer.study_pomodoro }
```

**study_soft_nudge**（轻提醒）：
```yaml
study_soft_nudge:
  alias: "Study Soft Nudge"
  mode: restart
  sequence:
    - service: light.turn_on
      target: { entity_id: light.study_lamp }
      data: { brightness_pct: 70 }
    - service: tts.google_translate_say
      target: { entity_id: media_player.xiaoai_speaker }
      data: { message: "提醒一下：现在开始第一关。" }
```

**study_night_silent_nudge**（夜间静默）：
```yaml
study_night_silent_nudge:
  alias: "Study Night Silent Nudge"
  mode: restart
  sequence:
    - service: light.turn_on
      target: { entity_id: light.study_lamp }
      data: { brightness_pct: 50, color_temp: 400 }
    - delay: "00:00:01"
    - service: light.turn_off
      target: { entity_id: light.study_lamp }
    - delay: "00:00:01"
    - service: light.turn_on
      target: { entity_id: light.study_lamp }
      data: { brightness_pct: 50, color_temp: 400 }
```

### 5.3 Automation（节奏推进）

```yaml
automation:
  - alias: "Study Pomodoro -> Break -> Continue"
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
          message: "休息结束，继续下一轮25分钟。"
```

---

## 六、实施路线图

### Phase 1：基础跑通（1-2 天）

**目标**：让系统能跑通最小闭环

| 任务 | 交付物 |
|------|--------|
| 创建目录结构 | 所有目录就绪 |
| 编写 index.json | 成员索引建立 |
| 编写 homework-intake Skill | 作业拆解+双视图 |
| 编写 study-mode Skill | 开始/结束触发 |
| HA 配置 Timer + 3 个脚本 | 设备可联动 |
| 编写 Automation | 节奏自动推进 |
| 验证测试 | 完整链路跑通 |

### Phase 2：可靠性补齐（1 天）

**目标**：处理"没人回应"场景

| 任务 | 交付物 |
|------|--------|
| 编写 study-ack Skill | 确认机制 |
| 编写 study-escalation Skill | 升级机制 + 定时检查 |
| 配置 policies.json | 策略参数化 |
| 编写夜间提醒脚本 | 静默策略 |
| 配置定时任务 | 每分钟执行 study-escalation |

### Phase 3：数据沉淀（1 天）

**目标**：建立系统长期记忆

| 任务 | 交付物 |
|------|--------|
| 编写 daily-report Skill | 日报生成 |
| 编写 weekly-report Skill | 周报 + 趋势查询 |
| 创建 trends.csv | 趋势数据源 |
| 配置日报自动触发 | /结束学习 后自动触发 |
| 验证数据流 | 数据沉淀完整 |

### Phase 4：策略可配置（1 天）

**目标**：家长可控、策略可回滚

| 任务 | 交付物 |
|------|--------|
| 创建计划模板库 | 4 套模板 JSON |
| 编写 plan-builder Skill | 模板切换 + 四旋钮 |
| 接入策略到执行层 | study-mode/escalation 读 policies.json |
| 配置审计日志 | policy_changes.log |
| 权限收紧测试 | kid 不能改策略 |

### Phase 5：优化完善（持续）

| 任务 | 交付物 |
|------|--------|
| 成员注册流程 | member-registry Skill（可选）|
| 错题管理 | data/mistakes/ 结构 |
| 周报趋势图表 | 可选数据可视化 |
| 性能优化 | 批量查询、缓存 |
| 多家庭支持 | family_id 隔离 |

---

## 七、风险与注意事项

### 7.1 已知风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 通道拿不到 openid | 身份体系完全无法建立 | 先做 1 分钟自检：打印事件日志确认字段名 |
| 腾讯 API 数据延迟 | 行情监控不准确 | 已确认是腾讯侧问题，不影响核心学习链路 |
| HA 与 OpenClaw 网络不通 | 设备联动失败 | 确认 IP/端口互通，HA_TOKEN 有效 |
| 夜间跨天逻辑错误 | 该静默时播报 | 使用 date 命令做跨天判断，测试 22:00-06:00 边界 |
| policy_changes.log 权限 | 审计丢失 | 确认 OpenClaw 有 logs/ 目录写权限 |
| 多孩子串台 | 数据归属混乱 | 文件名必须带 member_id，权限基于 role 校验 |

### 7.2 常见陷阱

1. **用昵称当主键** → 演示能跑，实战一定出问题。只认 openid。
2. **先改 HA YAML 再加策略** → 违反"策略层只改 JSON"原则，导致每次调整都要改设备配置。
3. **升级逻辑先算时间再判断 ack** → 顺序错误会导致已确认仍提醒。正确顺序：mode → ack_start → elapsed → stage。
4. **日报追求全自动** → 先手动 `/日报` 验证数据源，稳定后再接自动触发。
5. **孩子能改策略** → 权限没收紧，系统边界立刻混乱。

### 7.3 环境变量配置

```bash
# Home Assistant 配置
HA_URL=http://<ha-ip>:8123
HA_TOKEN=<long-lived-token>

# LLM 配置（如果要用 AI 做作业理解增强）
LLM_API_KEY=<your-key>
LLM_MODEL=<model-name>
```

---

## 八、指令速查表

| 指令 | 触发者 | 功能 |
|------|--------|------|
| `/作业` | kid/parent/admin | 提交作业，触发拆解 |
| `/展开家长版` | parent/admin | 展开查看家长版计划 |
| `/开始学习` | kid/parent/admin | 触发学习模式（音响+台灯+timer）|
| `/结束学习` | kid/parent/admin | 结束学习，恢复环境 |
| `/确认 已开始` | kid | 确认开始学习，停止升级 |
| `/确认 已完成` | kid | 确认完成学习 |
| `/升级检查` | admin | 手动触发升级检查（调试用）|
| `/日报` | parent/admin | 生成当日日报 |
| `/周报` | parent/admin | 生成当周周报 |
| `/趋势 4周` | admin | 查看近期趋势 |
| `/切换计划 轻量/标准/冲刺/共读` | parent/admin | 切换计划模板 |
| `/设置 节奏=25/5` | parent/admin | 调整节奏 |
| `/设置 强度=低/中/高` | parent/admin | 调整提醒强度 |
| `/设置 升级=关闭/10/5` | parent/admin | 调整升级阈值 |
| `/设置 夜间=静默/低音量/仅通知` | parent/admin | 调整夜间策略 |
| `/当前策略` | parent/admin | 查看当前生效策略 |

---

## 九、验收清单

### 9.1 基础验收

- [ ] 三个不同角色发消息，数据分别落入各自目录，不串台
- [ ] 孩子发作业，系统能拆成 5-20 分钟粒度任务
- [ ] 群内输出孩子版短计划，家长可展开家长版
- [ ] inbox/ 和 parsed/ 下均有对应落盘文件
- [ ] 文件名包含日期和 member_id

### 9.2 执行层验收

- [ ] /开始学习 → 音响播报 + 台灯切换 + timer 启动
- [ ] timer 到点 → 自动休息 → delay → 继续下一轮
- [ ] /结束学习 → 灯光恢复 + 音响收尾 + timer 取消
- [ ] state.json 正确反映当前状态
- [ ] 先验 HA（手动触发脚本），再验 OpenClaw

### 9.3 升级机制验收

- [ ] 不确认 → 超阈值 → 触发轻提醒（stage=1）
- [ ] 仍未确认 → 超阈值 → 通知家长（stage=2）
- [ ] 确认后 → stage=0，升级停止
- [ ] 夜间不播报音响，仅灯光提示
- [ ] study-escalation 每分钟执行

### 9.4 数据沉淀验收

- [ ] /日报 → 生成日报文件 + 群内摘要
- [ ] /周报 → 生成周报文件 + 趋势对比
- [ ] /趋势 4 周 → 输出历史数据汇总
- [ ] trends.csv 有对应数据行
- [ ] 多孩子报告不串台

### 9.5 策略配置验收

- [ ] /切换计划 → policies.json 正确合并
- [ ] /设置 旋钮 → 参数正确更新
- [ ] 策略修改后，下次学习立即生效
- [ ] kid 执行策略指令被拒绝
- [ ] policy_changes.log 有审计记录

---

## 十、系统核心指标总结

| 维度 | 关键指标 |
|------|---------|
| **数据完整性** | 所有落盘文件名含 member_id，权限基于 role |
| **执行可靠性** | mode → ack → elapsed → stage 判断顺序不可逆 |
| **策略可配置** | 模板 patch 覆盖，不改 HA YAML，热更新 |
| **隐私边界** | kid 只看自己 / parent 看关联 / admin 看家庭 |
| **回滚能力** | 每次策略变更记录到 policy_changes.log |
| **夜间友好** | 22:00-06:00 自动静默，仅灯光 + 家长通知 |

---

> **系统设计哲学**：先把最小闭环跑通，再逐步扩展。不追求一步到位，不堆砌功能。
> 核心链路：**识别人 → 识任务 → 推动执行 → 处理没人回应 → 沉淀记忆 → 家长可控**
