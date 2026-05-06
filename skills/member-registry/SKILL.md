---
name: member-registry
description: 家庭成员自助注册：kid 自助注册 + parent/admin 绑定确认，支持多孩子家庭
user-invocable: true
---

## 指令
- `/注册` - 自助注册新成员
- `/绑定 {openid}` - 家长绑定孩子
- `/成员列表` - 查看所有成员（admin/parent）

## 身份与权限
- **admin**：可管理所有成员，绑定/解绑
- **parent**：可绑定自己的 children
- **kid**：可自助注册

## 数据源
- `data/family/members/index.json` - 成员索引
- `data/family/members/pending.json` - 待确认注册
- `data/family/contacts.json` - 联系人列表

## 行为

### 1. 自助注册流程
```
kid 发送 /注册：
1. 检查是否已在 index.json 中
2. 如未注册，写入 pending.json
3. 通知 parent/admin 确认
4. parent 发送 /绑定 {openid} 完成注册
```

**pending.json 示例**：
```json
{
  "pending": [
    {
      "openid": "新 openid",
      "requested_at": "2026-05-06T08:00:00+08:00",
      "status": "pending"
    }
  ]
}
```

### 2. 家长绑定
```
parent 发送 /绑定 {openid}：
1. 读取 pending.json，确认 openid 存在
2. 从 index.json 读取 parent 的 member_id
3. 将新成员写入 index.json，role=kid
4. 将 parent 的 linked_children 加入新成员
5. 清除 pending.json 中的记录
```

**index.json 更新**：
```json
{
  "family_id": "FAMILY_001",
  "members": [
    {
      "openid": "parent_openid",
      "member_id": "parent_1",
      "role": "parent",
      "display_name": "妈妈",
      "linked_children": ["kid_1", "kid_2"]
    },
    {
      "openid": "kid_openid",
      "member_id": "kid_2",
      "role": "kid",
      "display_name": "弟弟",
      "created_at": "2026-05-06"
    }
  ]
}
```

### 3. 成员列表
```
admin/parent 发送 /成员列表：
输出家庭所有成员：
- member_id
- role
- display_name
- linked_children（仅 parent/admin）
```

## 输出
- **群内**：注册提示 + 绑定确认
- **文件**：更新 index.json + pending.json

## 注意事项
- 注册是"软性"的，需家长确认
- 绑定后才能使用系统功能
- 多孩子场景下，linked_children 确保权限正确
- 解绑需 admin 权限
