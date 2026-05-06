# Phase 7 - 飞书接入方案

## 概述

将智能学习系统接入飞书（Lark），替代/补充微信通道。

---

## 一、飞书 Bot 配置

### 1.1 创建企业自建应用

1. 登录 [飞书开放平台](https://open.feishu.cn/) → 开发者后台
2. 创建企业自建应用 → 添加"机器人"能力
3. 获取 **App ID** 和 **App Secret**
4. 配置事件订阅

### 1.2 权限申请

| 权限 | 用途 | 必需 |
|------|------|------|
| im.message.receive_v1 | 接收消息 | ✅ |
| im:chat | 获取群信息 | ✅ |
| im:message:send_as_bot | 发送消息 | ✅ |
| im:chat:readonly | 读取群列表 | 可选 |

### 1.3 事件订阅配置

事件地址（Webhook URL）：
```
https://<your-domain>/feishu/webhook
```

订阅事件：
- ✅ im.message.receive_v1（接收消息）

---

## 二、消息格式转换

### 2.1 飞书 → OpenClaw 内部指令

**飞书消息体（收到时）：**
```json
{
  "event": {
    "sender": {
      "sender_id": { "open_id": "ou_xxxxx" },
      "sender_type": "user"
    },
    "message": {
      "message_id": "om_xxxxx",
      "chat_id": "oc_xxxxx",
      "message_type": "text",
      "content": "{\"text\": \"你好\"}"
    },
    "create_time": "1715000000000"
  }
}
```

**转换为 OpenClaw 内部格式：**
```python
# 内部指令格式
{
    "sender_open_id": "ou_xxxxx",
    "chat_id": "oc_xxxxx",
    "message_type": "text",
    "content": {"text": "你好"},
    "timestamp": 1715000000000,
    "source": "feishu"
}
```

### 2.2 指令识别规则

| 飞书消息 | 识别 | 触发 Skill |
|----------|------|-----------|
| `/作业` + 文本 | 开始作业录入 | homework-intake |
| `/开始学习` | 开始学习模式 | study-mode |
| `/确认 已开始` | 确认开始 | study-ack |
| `/确认 已完成` | 确认完成 | study-ack |
| `/结束学习` | 结束学习 | study-mode |
| `/日报` | 查看日报 | daily-report |
| `/周报` | 查看周报 | weekly-report |
| `/切换计划 轻量` | 切换计划 | plan-builder |
| `/设置 节奏=25/5` | 修改策略 | plan-builder |
| `/趋势 4 周` | 查看趋势 | weekly-report |
| `/注册` | 成员注册 | member-registry |
| `/列表` | 成员列表 | member-registry |

### 2.3 飞书回复适配

**文本消息（普通回复）：**
```json
{
    "msg_type": "text",
    "content": {"text": "回复内容"}
}
```

**富文本消息（报告/表格）：**
```json
{
    "msg_type": "post",
    "content": {
        "post": {
            "zh_cn": {
                "title": "日报标题",
                "content": [
                    [{"tag": "text", "text": "内容..."}],
                    [{"tag": "text", "text": "内容..."}]
                ]
            }
        }
    }
}
```

---

## 三、架构设计

### 3.1 消息路由

```
飞书消息 → 事件回调 → 指令识别 → Skill 匹配 → 执行 → 飞书回复
                                    ↓
                              member_registry
                              (openid ↔ 飞书 open_id 映射)
```

### 3.2 身份映射

| 微信 OpenID | 飞书 OpenID | 角色 |
|-------------|-------------|------|
| oWechat_xxx | oFeishu_xxx | kid_1 |
| oWechat_yyy | oFeishu_yyy | parent_1 |

映射表更新 `data/family/members/index.json` 增加飞书字段：
```json
{
  "member_id": "kid_1",
  "role": "kid",
  "name": "小明",
  "open_ids": {
    "weixin": "oWechat_xxx",
    "feishu": "oFeishu_xxx"
  }
}
```

### 3.3 多通道支持

```python
# 消息处理器伪代码
def handle_message(source, payload):
    # 1. 解析内部格式
    msg = parse_message(source, payload)
    
    # 2. 识别 sender 身份
    member = lookup_member(source, msg.sender_open_id)
    
    # 3. 识别指令
    command = detect_command(msg.content)
    
    # 4. 权限检查
    if not check_permission(member.role, command.skill):
        return send_feishu_reply("你没有权限执行此操作")
    
    # 5. 执行 Skill
    result = execute_skill(command.skill, member, msg.content)
    
    # 6. 回复（按通道适配格式）
    return send_reply(source, result)
```

---

## 四、实现步骤

### 阶段 4a：基础接入

1. 创建飞书应用，获取 App ID / Secret
2. 配置事件订阅（im.message.receive_v1）
3. 实现消息接收和指令识别
4. 实现简单文本回复

### 阶段 4b：Skill 集成

1. 接入 homework-intake（作业录入）
2. 接入 study-mode（学习模式）
3. 接入 study-ack（确认机制）
4. 接入 plan-builder（策略切换）

### 阶段 4c：报告适配

1. 日报适配飞书富文本格式
2. 周报适配飞书富文本格式
3. 学习进度卡片样式

### 阶段 4d：成员管理

1. 飞书用户注册
2. 管理员绑定确认
3. 多通道身份映射

---

## 五、环境变量配置

```bash
# 飞书 Bot 配置
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxx
FEISHU_VERIFY_TOKEN=xxxxxxx
FEISHU_ENCRYPT_KEY=xxxxxxx  # 可选

# Webhook 地址
FEISHU_WEBHOOK_URL=https://<your-domain>/feishu/webhook
```

---

## 六、与微信的对比

| 特性 | 微信 | 飞书 |
|------|------|------|
| 消息格式 | 文本/图片 | 文本/富文本/卡片 |
| 指令触发 | /前缀 | /前缀 |
| 权限控制 | OpenID 路由 | OpenID 路由 |
| 报告输出 | 纯文本 | 富文本/卡片 |
| 家长控制 | ✅ | ✅ |
| 多人场景 | 群聊 | 群聊 + 私聊 |

**飞书优势：** 富文本、卡片消息、更友好的报告展示。
**微信优势：** 家长/孩子日常使用更便捷。

---

## 六、凭证验证

| 项目 | 状态 | 说明 |
|------|------|------|
| App ID | ✅ cli_a943861621615ccd | 已配置 |
| App Secret | ✅ 已验证 | Token 获取成功 |
| App Access Token | ✅ t-g10456a8ZKOTMIJ6MX... | 可用，有效期 2 小时 |
| adapter.py | ✅ 已创建 | 消息路由 + 指令处理 |
| config.json | ✅ 已创建 | 凭证存储 |
| test_adapter.py | ✅ 已创建 | 单元测试（15/15 通过） |
| start.bat | ✅ 已创建 | 一键启动脚本 |

## 七、待完成

| 步骤 | 说明 | 状态 |
|------|------|------|
| 1. 配置事件订阅 | 飞书开放平台 → 事件订阅 → im.message.receive_v1 | ⏳ 等待配置 |
| 2. 配置回调地址 | 指向 `http://<公网IP>:9900/feishu/webhook` | ⏳ 等待网络 |
| 3. 添加应用 | 将 Bot 添加到群聊 | ⏳ 等待配置 |
| 4. 端口暴露 | 9900 端口公网可达 | ⏳ 等待配置 |

## 八、使用飞书消息

| 飞书消息 | 效果 |
|----------|------|
| `/作业 数学口算30分钟` | 开始作业录入 |
| `/开始学习` | 启动学习模式 |
| `/确认 已开始` | 确认开始，停止升级 |
| `/确认 已完成` | 确认完成 |
| `/结束学习` | 结束学习 |
| `/日报` | 查看日报 |
| `/切换计划 冲刺` | 家长切换计划 |
| `/列表` | 查看家庭成员 |

## 九、启动方式

**方式 A：命令行**
```bash
cd smart_learning/feishu
python adapter.py
# 服务启动在 http://0.0.0.0:9900/feishu/webhook
```

**方式 B：双击启动**
```
双击 start.bat
```

## 十、下一步

1. **事件订阅配置**：在飞书开放平台配置事件回调 URL
2. **网络配置**：确保 9900 端口可从公网访问（或内网穿透）
3. **群聊添加**：将 Bot 添加到学习群
4. **完整测试**：飞书消息端到端测试
