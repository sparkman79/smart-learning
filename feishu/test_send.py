#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书消息发送测试"""
import json
import requests
import time
import os

BASE = r'C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning'
CONFIG_FILE = os.path.join(BASE, 'feishu', 'config.json')

print("=" * 50)
print("飞书消息发送测试")
print("=" * 50)

# 1. 加载配置
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 2. 获取 Token
r1 = requests.post(
    'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal',
    json={'app_id': config['app_id'], 'app_secret': config['app_secret']},
    timeout=10
)
tdata = r1.json()
token = tdata.get('app_access_token', '')
print(f"1. Token 获取: {'成功' if token else '失败'}")

if not token:
    print("错误: 无法获取 Token，测试终止")
    exit(1)

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# 3. 获取机器人信息
r2 = requests.get('https://open.feishu.cn/open-apis/bot/v3/info', headers=headers, timeout=10)
bot_data = r2.json()
bot_open_id = bot_data.get('bot', {}).get('open_id', '')
print(f"2. 机器人 open_id: {bot_open_id[:20] if bot_open_id else '获取失败'}")

# 4. 获取群聊列表
r3 = requests.get('https://open.feishu.cn/open-apis/im/v1/chats',
    params={'page_size': 10}, headers=headers, timeout=10)
chat_data = r3.json()

if chat_data.get('code') == 0:
    chats = chat_data.get('data', {}).get('items', [])
    if chats:
        for i, c in enumerate(chats[:5]):
            print(f"3-{i}. 群聊: {c.get('name', '?')} (chat_id: {c.get('chat_id', '?')[:20]}...)")
        
        chat_id = chats[0]['chat_id']
        
        # 5. 发送测试消息
        test_msg = '🤖 智能学习系统飞书自动测试\n/日报'
        r4 = requests.post(
            'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
            headers=headers,
            json={
                'receive_id': chat_id,
                'msg_type': 'text',
                'content': json.dumps({'text': test_msg})
            },
            timeout=10
        )
        send_result = r4.json()
        
        if send_result.get('code') == 0:
            print(f"\n4. 消息发送: 成功")
            print(f"   内容: {test_msg}")
            print(f"   发送到群: {chats[0].get('name', '?')}")
        else:
            print(f"\n4. 消息发送: 失败")
            print(f"   错误: {r4.text[:300]}")
    else:
        print("3. 未找到任何群聊")
else:
    print(f"3. 获取群聊失败: {chat_data.get('msg', chat_data.get('message', '未知错误'))}")

print("\n" + "=" * 50)
