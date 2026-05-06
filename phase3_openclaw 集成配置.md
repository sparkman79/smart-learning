# Phase 3: OpenClaw 定时任务集成配置

## 配置步骤

### 1. 添加学习系统定时任务

编辑 `cron/jobs.json`，在 `jobs` 数组末尾添加以下两条任务：

#### 任务 A：学习升级检查（每分钟执行）

```json
{
  "id": "study_escalation",
  "name": "学习升级检查",
  "schedule": "*/1 * * * *",
  "description": "每分钟检查学习会话状态，未确认时触发升级提醒",
  "enabled": true,
  "script": "skills/study-escalation/run.sh",
  "payload": {
    "workspace": "{{WORKSPACE}}/smart_learning",
    "state_file": "data/routines/state.json",
    "policies_file": "data/routines/policies.json"
  },
  "delivery": {
    "type": "chat",
    "channels": ["openclaw-weixin"],
    "condition": "escalation_triggered"
  }
}
```

#### 任务 B：日报自动生成（23:00 执行）

```json
{
  "id": "daily_learning_report",
  "name": "每日学习日报生成",
  "schedule": "0 23 * * *",
  "description": "每晚 23:00 自动生成今日学习日报，推送到家长群",
  "enabled": true,
  "script": "skills/daily-report/run.sh",
  "payload": {
    "workspace": "{{WORKSPACE}}/smart_learning",
    "report_dir": "data/reports/daily",
    "trends_file": "data/reports/trends/trends.csv"
  },
  "delivery": {
    "type": "chat",
    "channels": ["openclaw-weixin"],
    "target": "parent_group"
  }
}
```

### 2. 环境变量配置

在 OpenClaw 环境变量中添加以下配置：

```bash
# 学习系统工作区
SMART_LEARNING_WORKSPACE=/path/to/workspace/smart_learning

# HA 配置（可选，HA 设备就绪后启用）
# HA_URL=http://<ha-ip>:8123
# HA_TOKEN=<long-lived-access-token>

# 微信/飞书通知配置（按需启用）
# WEIXIN_TOKEN=<your-weixin-token>
# FEISHU_WEBHOOK=<your-feishu-webhook>
```

### 3. Skill 可执行脚本

每个 Skill 需要创建一个简单的启动脚本：

#### `skills/homework-intake/run.sh`
```bash
#!/bin/bash
cd "${SMART_LEARNING_WORKSPACE}"
python -c "
import json, sys
from datetime import datetime
import os

# 从 stdin 读取作业内容
content = sys.stdin.read().strip()
member_id = '${SMART_LEARNING_MEMBER_ID:-kid_1}'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# 创建 inbox 文件
inbox_dir = 'data/homework/inbox'
os.makedirs(inbox_dir, exist_ok=True)
filename = f'{member_id}_{timestamp}.txt'
with open(f'{inbox_dir}/{filename}', 'w', encoding='utf-8') as f:
    f.write(content)

# 输出状态
print(json.dumps({
    'status': 'received',
    'filename': filename,
    'member_id': member_id
}))
"
```

#### `skills/study-mode/run.sh`
```bash
#!/bin/bash
cd "${SMART_LEARNING_WORKSPACE}"
python -c "
import json
from datetime import datetime

state_file = 'data/routines/state.json'
policies_file = 'data/routines/policies.json'

with open(state_file, 'r') as f:
    state = json.load(f)

with open(policies_file, 'r') as f:
    policies = json.load(f)

# 更新状态
state['mode'] = 'study'
state['current_member_id'] = '${SMART_LEARNING_MEMBER_ID:-kid_1}'
state['session']['started_at'] = datetime.now().isoformat()
state['session']['last_notify_at'] = datetime.now().isoformat()

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

# 触发 HA 脚本（如果配置了）
import urllib.request
ha_url = '${HA_URL:-}'
ha_token = '${HA_TOKEN:-}'
if ha_url and ha_token:
    req = urllib.request.Request(
        f'{ha_url}/api/services/script/turn_on',
        headers={
            'Authorization': f'Bearer {ha_token}',
            'Content-Type': 'application/json'
        },
        data=b'{}'
    )
    try:
        urllib.request.urlopen(req)
    except:
        pass

print(json.dumps({
    'status': 'study_started',
    'mode': state['mode'],
    'member_id': state['current_member_id']
}))
"
```

## 验证清单

- [ ] `study_escalation` 任务已添加到 `cron/jobs.json`
- [ ] `daily_learning_report` 任务已添加到 `cron/jobs.json`
- [ ] 所有 Skill 的 `run.sh` 脚本已创建并可执行
- [ ] 环境变量配置完成
- [ ] 手动测试 `/开始学习` 触发 study-mode
- [ ] 手动测试 `/结束学习` 触发日报生成
- [ ] 检查 `data/routines/state.json` 状态更新正常
- [ ] 检查 `data/reports/daily/` 日报文件生成

## 注意事项

1. **Study-escalation 频率高**：每分钟执行，注意控制输出量，只在触发升级时才推送
2. **日报生成时间**：23:00 生成，包含当天所有学习记录
3. **HA 配置可选**：环境变量留空时，study-mode 会跳过设备联动，只更新状态机
4. **权限控制**：确保 kid_1 不能修改 policies.json 和 state.json
