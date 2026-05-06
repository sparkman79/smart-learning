#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书 Bot 适配器
将飞书消息转换为 OpenClaw 内部格式，并路由到对应 Skill
"""

import json
import logging
import os
import sys
import hashlib
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# 配置日志 → 写入文件，不输出到 stdout（否则污染 HTTP 响应）
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(LOG_DIR, 'feishu_server.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [feishu] %(levelname)s %(message)s'
))

logger = logging.getLogger('feishu-adapter')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

logger.info(f'日志已重定向到文件: {log_file}')

# 路径配置：__file__ 在 feishu/ 目录下，dirname 直接拿到 feishu/ 目录
FEISHU_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(FEISHU_DIR)  # smart_learning/
CONFIG_FILE = os.path.join(FEISHU_DIR, 'config.json')
STATE_DIR = os.path.join(BASE_DIR, 'data', 'routines')
STATE_FILE = os.path.join(STATE_DIR, 'state.json')
MEMBER_FILE = os.path.join(BASE_DIR, 'data', 'family', 'members', 'index.json')

# 打印路径用于调试
logger.info(f'FEISHU_DIR={FEISHU_DIR}')
logger.info(f'BASE_DIR={BASE_DIR}')
logger.info(f'CONFIG_FILE={CONFIG_FILE}')

FEISHU_URL = 'https://open.feishu.cn/open-apis/bot/v2'


def load_config():
    """加载飞书配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_state():
    """加载 state.json"""
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_state(state):
    """保存 state.json"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_members():
    """加载成员索引"""
    if not os.path.exists(MEMBER_FILE):
        return {}
    with open(MEMBER_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_app_access_token(config):
    """获取 App Access Token"""
    import requests
    url = 'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal'
    data = {
        'app_id': config['app_id'],
        'app_secret': config['app_secret']
    }
    r = requests.post(url, json=data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        if result.get('code') == 0:
            return result.get('app_access_token')
    logger.error(f'获取 Token 失败: {r.text}')
    return None


def verify_signature(config, body):
    """验证飞书事件签名"""
    token = config.get('verify_token', '')
    if not token:
        return True  # 开发阶段可跳过验证
    
    body_str = json.dumps(body) if isinstance(body, dict) else body
    ts = body.get('header', {}).get('timestamp', 0)
    sign_str = f"{token}{ts}"
    sign = hashlib.sha256(sign_str.encode('utf-8')).hexdigest()
    
    header_sign = body.get('header', {}).get('signature', '')
    return sign == header_sign


def parse_feishu_message(body):
    """解析飞书消息体为 OpenClaw 内部格式"""
    event = body.get('event', {})
    message = event.get('message', {})
    sender = event.get('sender', {})
    
    # 提取 sender open_id
    sender_id = sender.get('sender_id', {})
    sender_open_id = sender_id.get('open_id', '')
    
    # 提取消息内容
    content = message.get('content', '{}')
    try:
        content_data = json.loads(content) if isinstance(content, str) else content
    except json.JSONDecodeError:
        content_data = {'text': content}
    
    text = content_data.get('text', '') if isinstance(content_data, dict) else str(content_data)
    
    # 内部格式
    internal = {
        'sender_open_id': sender_open_id,
        'chat_id': message.get('chat_id', ''),
        'message_type': message.get('message_type', 'text'),
        'message_id': message.get('message_id', ''),
        'content': text.strip(),
        'timestamp': event.get('create_time', ''),
        'source': 'feishu'
    }
    
    return internal


def identify_command(text):
    """识别指令，返回 (command, args)"""
    commands = {
        '/作业': 'homework_intake',
        '/开始学习': 'study_start',
        '/确认': 'study_ack',
        '/结束学习': 'study_end',
        '/日报': 'daily_report',
        '/周报': 'weekly_report',
        '/切换计划': 'plan_switch',
        '/设置': 'plan_set',
        '/趋势': 'trend_view',
        '/注册': 'member_register',
        '/列表': 'member_list'
    }
    
    for prefix, cmd in commands.items():
        if text.startswith(prefix):
            args = text[len(prefix):].strip() if len(text) > len(prefix) else ''
            return cmd, args
    
    return 'unknown', text


def find_member_by_feishu(config, open_id):
    """通过飞书 open_id 查找成员"""
    members = load_members()
    
    for mid, info in members.get('members', {}).items():
        feishu_id = info.get('open_ids', {}).get('feishu', '')
        if feishu_id == open_id:
            return {
                'member_id': mid,
                'role': info.get('role', 'unknown'),
                'name': info.get('name', ''),
                'channel': 'feishu'
            }
    
    return None


def send_feishu_message(chat_id, text, config):
    """发送飞书消息到群/私聊"""
    import requests
    
    token = get_app_access_token(config)
    if not token:
        logger.error('无法获取 Token，消息发送失败')
        return False
    
    url = f'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 尝试从 chat_id 提取 tenant_id（如果是 tenant_chat_id）
    data = {
        'receive_id': chat_id,
        'msg_type': 'text',
        'content': json.dumps({'text': text})
    }
    
    r = requests.post(url, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        if result.get('code') == 0:
            logger.info(f'飞书消息发送成功: chat_id={chat_id[:20]}...')
            return True
    
    logger.error(f'飞书消息发送失败: {r.text}')
    return False


def send_feishu_reply(chat_id, text, config):
    """发送回复（飞书富文本）"""
    # 简单文本
    send_feishu_message(chat_id, text, config)
    
    # TODO: 后续可接入富文本卡片
    logger.info(f'飞书回复: {text[:100]}...')


class FeishuWebhookHandler(BaseHTTPRequestHandler):
    """飞书 Webhook 处理器"""
    
    # 覆写日志输出：默认会写 stderr，可能污染响应流
    def log_message(self, format, *args):
        logger.info(format % args)
    
    def do_POST(self):
        """处理 POST 请求（全局异常保护）"""
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path != '/feishu/webhook':
                self.send_response(404)
                self.end_headers()
                return
            
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body_raw = self.rfile.read(content_length)
            body = json.loads(body_raw)
            
            # 处理飞书应用验证（POST 方式，跳过签名验证）
            # 飞书发送 challenge 验证时，可能发送 'challenge' 或 'encrypt' 字段
            challenge = body.get('challenge', '')
            encrypt = body.get('encrypt', '')
            event_type = body.get('type', '')
            if challenge or encrypt or event_type == 'pb_verify':
                self._handle_verify(body, config={'verify_token': ''})
                return
            
            # 验证签名
            config = load_config()
            if not verify_signature(config, body):
                logger.warning('飞书事件签名验证失败')
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'code': 403, 'msg': 'Invalid signature'}).encode())
                return
            
            # 处理事件类型
            event_type = body.get('event', {}).get('type', '')
            
            if event_type == 'im.message.receive_v1':
                self._handle_message(body, config)
            else:
                logger.info(f'忽略事件类型: {event_type}')
            
            # 必须返回 200 + 合法 JSON
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'code': 0}).encode())
        
        except Exception as e:
            # 任何异常都要返回合法 JSON，不能让飞书收到空响应
            logger.error(f'do_POST 异常: {e}', exc_info=True)
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'code': 500,
                    'msg': f'Server error: {str(e)}'
                }).encode())
            except Exception:
                pass
    
    def _handle_message(self, body, config):
        """处理收到的消息"""
        internal = parse_feishu_message(body)
        chat_id = internal['chat_id']
        text = internal['content']
        sender_id = internal['sender_open_id']
        
        if not text:
            logger.warning('收到空消息')
            return
        
        logger.info(f'收到飞书消息: sender={sender_id[:20]}... text="{text[:50]}"')
        
        try:
            # 查找成员
            member = find_member_by_feishu(config, sender_id)
            
            if not member:
                send_feishu_reply(chat_id, '请先发送 /注册 完成注册', config)
                return
            
            logger.info(f'成员匹配: member_id={member["member_id"]}, role={member["role"]}, name={member["name"]}')
            
            # 识别指令
            cmd, args = identify_command(text)
            logger.info(f'指令: {cmd}, 参数: {args}')
            
            # 路由到对应处理函数
            handlers = {
                'homework_intake': handle_homework,
                'study_start': handle_study_start,
                'study_ack': handle_study_ack,
                'study_end': handle_study_end,
                'daily_report': handle_daily_report,
                'weekly_report': handle_weekly_report,
                'plan_switch': handle_plan_switch,
                'plan_set': handle_plan_set,
                'trend_view': handle_trend_view,
                'member_register': handle_member_register,
                'member_list': handle_member_list
            }
            
            handler = handlers.get(cmd)
            if handler:
                reply = handler(member, args, config, chat_id)
                send_feishu_reply(chat_id, reply, config)
            else:
                send_feishu_reply(chat_id, f'未知指令: {text}\n支持指令: /作业 /开始学习 /确认 /结束学习 /日报 /周报 /切换计划 /设置 /趋势 /注册 /列表', config)
        
        except Exception as e:
            logger.error(f'_handle_message 异常: {e}', exc_info=True)
            try:
                send_feishu_reply(chat_id, f'⚠️ 处理消息时出错，请稍后重试', config)
            except Exception:
                pass
    
    def _handle_verify(self, body, config):
        """处理飞书应用验证（POST 回调验证）"""
        challenge = body.get('challenge', '')
        encrypt = body.get('encrypt', '')
        
        if encrypt:
            # 飞书加密模式：原样返回 encrypt
            logger.info(f'飞书应用验证(POST, 加密模式): encrypt={encrypt[:20]}...')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'encrypt': encrypt}).encode())
        elif challenge:
            # 普通模式：返回 challenge
            logger.info(f'飞书应用验证(POST): challenge={challenge}')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'challenge': challenge}).encode())
        else:
            # pb_verify 事件
            logger.info(f'飞书应用验证(POST): type=pb_verify (无 challenge/encrypt)')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'challenge': ''}).encode())
        return
    
    def do_GET(self):
        """处理 GET 请求（健康检查 + 飞书 GET 回调验证）"""
        if self.path == '/feishu/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'channel': 'feishu'}).encode())
            return
        
        # 飞书 GET 回调验证（配置回调地址时触发）
        parsed = urlparse(self.path)
        if parsed.path == '/feishu/webhook':
            import urllib.parse
            params = urllib.parse.parse_qs(parsed.query)
            challenge = params.get('challenge', [''])[0]
            if challenge:
                logger.info(f'飞书应用验证(GET): challenge={challenge}')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'challenge': challenge}).encode())
                return
        
        self.send_response(404)
        self.end_headers()


# ============ 指令处理函数 ============

def handle_homework(member, args, config, chat_id):
    """处理作业指令"""
    if not args:
        return '请发送作业内容，例如：\n/作业 数学口算30分钟 英语背单词20个'
    # 路由到 homework-intake Skill
    return f'收到作业指令：{args}\n已发送到学习系统处理中...'


def handle_study_start(member, args, config, chat_id):
    """处理开始学习指令"""
    if member['role'] == 'kid':
        state = load_state()
        state['mode'] = 'learning'
        state['current_member_id'] = member['member_id']
        state['session'] = {
            'started_at': 'now',
            'ack_start': False,
            'ack_done': False,
            'round': 1,
            'escalation_stage': 0
        }
        save_state(state)
        return f'开始学习模式 📚\n成员：{member["name"]}\n计划：{config.get("default_plan", "standard")}'
    return '仅孩子可以执行此操作'


def handle_study_ack(member, args, config, chat_id):
    """处理确认指令"""
    state = load_state()
    if not args:
        return '请指定确认类型：\n/确认 已开始\n/确认 已完成'
    
    if args == '已开始':
        if state.get('session', {}).get('ack_start'):
            return '已确认开始，无需重复'
        state['session']['ack_start'] = True
        state['session']['ack_start_at'] = 'now'
        state['session']['escalation_stage'] = 0
        save_state(state)
        return '✅ 已开始！学习升级通知已停止。\n继续加油！'
    
    if args == '已完成':
        state['session']['ack_done'] = True
        state['session']['ack_done_at'] = 'now'
        state['mode'] = 'completed'
        save_state(state)
        return '✅ 学习完成！\n日报将在今晚 23:00 自动生成。'
    
    return '未知确认类型，请使用 /确认 已开始 或 /确认 已完成'


def handle_study_end(member, args, config, chat_id):
    """处理结束学习指令"""
    state = load_state()
    if state.get('current_member_id') != member['member_id']:
        return f'当前学习的不是您（{state.get("current_member_id")}），无法结束'
    
    state['mode'] = 'idle'
    state['current_member_id'] = None
    # 保留 round（已完成的学习轮次），重置其他 session 字段
    old_round = state['session'].get('round', 0)
    old_pomo = state['session'].get('pomodoro_minutes', 25)
    old_break = state['session'].get('break_minutes', 5)
    state['session'] = {
        'started_at': None,
        'ack_start': None,
        'ack_start_at': None,
        'ack_done': None,
        'ack_done_at': None,
        'pomodoro_minutes': old_pomo,
        'break_minutes': old_break,
        'round': old_round,
        'escalation_stage': 0,
        'last_nudge_at': None,
        'last_notify_at': None
    }
    save_state(state)
    return '学习已结束 🏁\n辛苦了！'


def handle_daily_report(member, args, config, chat_id):
    """处理日报查看"""
    report_dir = os.path.join(STATE_DIR.replace('routines', 'reports'), 'daily')
    today = '2026-05-06'  # TODO: 动态获取
    report_file = os.path.join(report_dir, f'{today}_{member["member_id"]}_daily.md')
    
    if os.path.exists(report_file):
        with open(report_file, 'r', encoding='utf-8') as f:
            return f.read()
    return f'今日日报尚未生成，今晚 23:00 自动生成。\n也可以手动发送 /日报 查看'


def handle_weekly_report(member, args, config, chat_id):
    """处理周报查看"""
    return '周报功能开发中，敬请期待 📊'


def handle_plan_switch(member, args, config, chat_id):
    """处理切换计划指令"""
    if member['role'] not in ('parent', 'admin'):
        return '仅家长/管理员可以切换学习计划'
    
    plan_map = {
        '轻量': 'light',
        'standard': 'standard',
        '冲刺': 'sprint',
        '家庭阅读': 'family_read'
    }
    
    plan = plan_map.get(args, args)
    if plan not in plan_map.values():
        return f'未知计划，可用计划：轻量 / standard / 冲刺 / 家庭阅读'
    
    # 更新 policies.json 并应用 plan 的 policy_patch
    policies_file = os.path.join(STATE_DIR, 'policies.json')
    with open(policies_file, 'r', encoding='utf-8') as f:
        policies = json.load(f)
    
    policies['current_plan'] = plan
    
    # 加载 plan 模板并应用 policy_patch
    plan_file = os.path.join(STATE_DIR, 'plans', f'{plan}.json')
    if os.path.exists(plan_file):
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        policy_patch = plan_data.get('policy_patch')
        if policy_patch and isinstance(policy_patch, dict):
            for k, v in policy_patch.items():
                policies[k] = v
    
    with open(policies_file, 'w', encoding='utf-8') as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)
    
    # 记录策略变更
    log_file = os.path.join(STATE_DIR, 'logs', 'policy_changes.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'{member["member_id"]} 切换计划 → {plan}\n')
    
    return f'✅ 计划已切换：{plan}\n下次学习将使用新计划'


def handle_plan_set(member, args, config, chat_id):
    """处理策略设置指令"""
    if member['role'] not in ('parent', 'admin'):
        return '仅家长/管理员可以修改学习策略'
    
    if not args or '=' not in args:
        return '格式：/设置 节奏=25/5\n可用设置：节奏、休息类型、计划'
    
    key, value = args.split('=', 1)
    
    policies_file = os.path.join(STATE_DIR, 'policies.json')
    with open(policies_file, 'r', encoding='utf-8') as f:
        policies = json.load(f)
    
    if key == '节奏':
        try:
            work, rest = value.split('/')
            policies['pomodoro_minutes'] = int(work)
            policies['break_minutes'] = int(rest)
        except ValueError:
            return '节奏格式错误，请使用：25/5'
    
    with open(policies_file, 'w', encoding='utf-8') as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)
    
    return f'✅ 策略已更新：{key}={value}'


def handle_trend_view(member, args, config, chat_id):
    """处理趋势查看指令"""
    weeks = args.split()[0] if args else '4'
    return f'📊 查看 {weeks} 周趋势...（功能开发中）'


def handle_member_register(member, args, config, chat_id):
    """处理成员注册指令"""
    return '飞书用户注册功能开发中...\n请等待管理员绑定确认'


def handle_member_list(member, args, config, chat_id):
    """处理成员列表指令"""
    members = load_members()
    result = f'👥 家庭成员列表（{len(members.get("members", {}))}人）\n\n'
    
    for mid, info in members.get('members', {}).items():
        role_text = {'admin': '👑 管理员', 'parent': '👨‍👩‍👧 家长', 'kid': '👶 孩子'}.get(info.get('role', ''), '❓')
        result += f'{mid}: {info.get("name", "")} - {role_text}\n'
    
    return result


# ============ 主程序 ============

if __name__ == '__main__':
    port = int(os.environ.get('FEISHU_PORT', 9900))
    server = HTTPServer(('0.0.0.0', port), FeishuWebhookHandler)
    logger.info(f'飞书 Webhook 服务器启动: http://0.0.0.0:{port}/feishu/webhook')
    logger.info(f'健康检查: http://0.0.0.0:{port}/feishu/health')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('服务器关闭')
        server.shutdown()
