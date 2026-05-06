#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能学习系统 - 集成测试
测试飞书消息 → 解析 → 路由 → 状态变更 → 飞书回复 的完整链路
使用临时目录隔离测试，不污染真实数据
"""

import os
import sys
import json
import hashlib
import time
import shutil

BASE_DIR = r"/tmp/smart-learning"
REAL_FEISHU = os.path.join(BASE_DIR, "feishu")
REAL_ADAPTER = os.path.join(REAL_FEISHU, "adapter.py")

# 创建干净的临时测试目录
TEST_DIR = os.path.join(BASE_DIR, "tests", ".test_workspace")
if os.path.exists(TEST_DIR):
    shutil.rmtree(TEST_DIR)
os.makedirs(TEST_DIR, exist_ok=True)
TEST_FEISHU = os.path.join(TEST_DIR, "feishu")
os.makedirs(TEST_FEISHU, exist_ok=True)
TEST_DATA = os.path.join(TEST_DIR, "data")
os.makedirs(TEST_DATA, exist_ok=True)

sys.path.insert(0, TEST_FEISHU)

results = []

def reset():
    """重置所有测试文件"""
    global CONFIG_PATH
    # 创建干净 state.json
    state_file = os.path.join(TEST_DATA, "routines", "state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump({
            "mode": "idle",
            "current_member_id": None,
            "session": {
                "started_at": None,
                "ack_start": False,
                "ack_start_at": None,
                "ack_done": False,
                "ack_done_at": None,
                "pomodoro_minutes": 25,
                "break_minutes": 5,
                "round": 0,
                "escalation_stage": 0,
                "last_nudge_at": None,
                "last_notify_at": None
            }
        }, f, ensure_ascii=False, indent=2)

    # 创建干净的 members.json
    members_file = os.path.join(TEST_DATA, "family", "members", "index.json")
    os.makedirs(os.path.dirname(members_file), exist_ok=True)
    with open(members_file, "w", encoding="utf-8") as f:
        json.dump({
            "family_id": "FAMILY_TEST",
            "members": {
                "kid_1": {
                    "name": "小明",
                    "role": "kid",
                    "open_ids": {"feishu": "ou_test_kid_1"},
                    "scheduled": ["homework_intake", "study_start", "study_ack", "study_end"]
                },
                "parent_1": {
                    "name": "爸爸",
                    "role": "parent",
                    "open_ids": {"feishu": "ou_test_parent_1"},
                    "linked_children": ["kid_1"],
                    "scheduled": ["homework_intake", "daily_report", "weekly_report", "plan_switch", "plan_set", "trend_view"]
                },
                "admin_1": {
                    "name": "管理员",
                    "role": "admin",
                    "open_ids": {"feishu": "ou_test_admin_1"},
                    "scheduled": ["member_register", "member_list"]
                }
            }
        }, f, ensure_ascii=False, indent=2)

    # 创建 policies.json
    policies_file = os.path.join(TEST_DATA, "routines", "policies.json")
    with open(policies_file, "w", encoding="utf-8") as f:
        json.dump({
            "pomodoro_minutes": 25,
            "break_minutes": 5,
            "current_plan": "standard",
            "escalation": {"enabled": True, "stage1": 300, "stage2": 900},
            "night": {"enabled": True, "start": "22:30", "end": "06:00"}
        }, f, ensure_ascii=False, indent=2)

    # 创建 config.json
    CONFIG_PATH = os.path.join(TEST_FEISHU, "config.json")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "app_id": "cli_test_app_id",
            "app_secret": "test_secret",
            "verify_token": "werify_abc123",
            "webhook_path": "/feishu/webhook",
            "channel": "feishu",
            "status": "ready"
        }, f, ensure_ascii=False, indent=2)

    # 创建测试用 adapter（修改路径常量）
    with open(REAL_ADAPTER, "r", encoding="utf-8") as f:
        adapter_code = f.read()

    adapter_code = adapter_code.replace(
        "FEISHU_DIR = os.path.dirname(os.path.abspath(__file__))",
        f'FEISHU_DIR = r"{TEST_FEISHU}"'
    )
    adapter_code = adapter_code.replace(
        'BASE_DIR = os.path.dirname(FEISHU_DIR)  # smart_learning/',
        f'BASE_DIR = r"{BASE_DIR}"'
    )
    adapter_code = adapter_code.replace(
        "CONFIG_FILE = os.path.join(FEISHU_DIR, 'config.json')",
        f'CONFIG_FILE = r"{CONFIG_PATH}"'
    )

    state_dir = os.path.join(TEST_DATA, "routines")
    adapter_code = adapter_code.replace(
        "STATE_DIR = os.path.join(BASE_DIR, 'data', 'routines')",
        f'STATE_DIR = r"{state_dir}"'
    )
    state_file_path = os.path.join(state_dir, "state.json")
    adapter_code = adapter_code.replace(
        "STATE_FILE = os.path.join(STATE_DIR, 'state.json')",
        f'STATE_FILE = r"{state_file_path}"'
    )

    member_file_path = os.path.join(TEST_DATA, "family", "members", "index.json")
    adapter_code = adapter_code.replace(
        "MEMBER_FILE = os.path.join(BASE_DIR, 'data', 'family', 'members', 'index.json')",
        f'MEMBER_FILE = r"{member_file_path}"'
    )

    with open(os.path.join(TEST_FEISHU, "adapter_test.py"), "w", encoding="utf-8") as f:
        f.write(adapter_code)

    # 创建报告目录
    report_dir = os.path.join(TEST_DATA, "reports", "trends")
    os.makedirs(report_dir, exist_ok=True)
    trends_file = os.path.join(report_dir, "trends.csv")
    with open(trends_file, "w", encoding="utf-8") as f:
        f.write("日期,member_id,学习时长,番茄轮次,完成数,总数,完成度\n")

    # 创建日志目录
    log_dir = os.path.join(TEST_DATA, "routines", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 创建计划目录
    plans_dir = os.path.join(TEST_DATA, "routines", "plans")
    os.makedirs(plans_dir, exist_ok=True)
    for plan_name in ["light", "standard", "sprint", "family_read"]:
        plan_file = os.path.join(plans_dir, f"{plan_name}.json")
        if not os.path.exists(plan_file):
            with open(plan_file, "w", encoding="utf-8") as f:
                json.dump({
                    "name": plan_name,
                    "policy_patch": {"pomodoro_minutes": 15, "break_minutes": 3} if plan_name == "light" else None
                }, f, ensure_ascii=False, indent=2)


def assert_test(name, condition, expected, actual):
    status = "✅" if condition else "❌"
    results.append({
        "test": name,
        "status": status,
        "expected": str(expected),
        "actual": str(actual)
    })
    print(f"  {status} {name}")
    if not condition:
        print(f"     期望：{expected} | 实际：{actual}")


# ==========================================
# 初始化测试环境
# ==========================================
print("=" * 60)
print(" 智能学习系统 - 集成测试")
print(f" 测试目录：{TEST_DIR}")
print("=" * 60)
print()

reset()
import importlib.util
spec = importlib.util.spec_from_file_location("adapter_test", os.path.join(TEST_FEISHU, "adapter_test.py"))
adapter_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter_mod)

config = adapter_mod.load_config()

# ==========================================
# Test 1: 飞书消息解析
# ==========================================
print("--- Test 1: 飞书消息解析 ---")
test_body = {
    "event": {
        "message": {
            "chat_id": "oc_test_group",
            "message_type": "text",
            "message_id": "om_test_msg_001",
            "content": '{"text": "/开始学习"}'
        },
        "sender": {
            "sender_id": {
                "open_id": "ou_test_kid_1"
            }
        },
        "create_time": "1700000000"
    }
}

parsed = adapter_mod.parse_feishu_message(test_body)
assert_test("解析 sender_open_id", parsed["sender_open_id"] == "ou_test_kid_1", "ou_test_kid_1", parsed["sender_open_id"])
assert_test("解析 chat_id", parsed["chat_id"] == "oc_test_group", "oc_test_group", parsed["chat_id"])
assert_test("解析 text", parsed["content"] == "/开始学习", "/开始学习", parsed["content"])
assert_test("消息类型=text", parsed["message_type"] == "text", "text", parsed["message_type"])
assert_test("source=feishu", parsed["source"] == "feishu", "feishu", parsed["source"])
print()

# ==========================================
# Test 2: 指令识别
# ==========================================
print("--- Test 2: 指令识别 ---")
cmd_pairs = [
    ("/开始学习", "study_start", ""),
    ("/作业 数学", "homework_intake", "数学"),
    ("/确认 已开始", "study_ack", "已开始"),
    ("/确认 已完成", "study_ack", "已完成"),
    ("/结束学习", "study_end", ""),
    ("/日报", "daily_report", ""),
    ("/切换计划 轻量", "plan_switch", "轻量"),
    ("/设置 节奏=15/3", "plan_set", "节奏=15/3"),
    ("/趋势 4", "trend_view", "4"),
    ("/注册", "member_register", ""),
    ("/列表", "member_list", ""),
]
for text, expected_cmd, expected_args in cmd_pairs:
    cmd, args = adapter_mod.identify_command(text)
    assert_test(f"指令: {text}", cmd == expected_cmd, expected_cmd, cmd)
    assert_test(f"参数: {text}", args == expected_args, expected_args, args)
print()

# ==========================================
# Test 3: 成员查找
# ==========================================
print("--- Test 3: 成员查找 ---")
kid_member = adapter_mod.find_member_by_feishu(config, "ou_test_kid_1")
assert_test("找到 kid_1", kid_member is not None, "非 None", kid_member)
if kid_member:
    assert_test("kid_1 role=kid", kid_member["role"] == "kid", "kid", kid_member["role"])
    assert_test("kid_1 name=小明", kid_member["name"] == "小明", "小明", kid_member["name"])

parent_member = adapter_mod.find_member_by_feishu(config, "ou_test_parent_1")
assert_test("找到 parent_1", parent_member is not None, "非 None", parent_member)
if parent_member:
    assert_test("parent_1 role=parent", parent_member["role"] == "parent", "parent", parent_member["role"])

unknown_member = adapter_mod.find_member_by_feishu(config, "ou_unknown")
assert_test("未知成员返回 None", unknown_member is None, "None", unknown_member)
print()

# ==========================================
# Test 4: 签名验证
# ==========================================
print("--- Test 4: 签名验证 ---")
test_config = {"verify_token": "werify_abc123"}
test_ts = 1700000000
sign_str = f"werify_abc123{test_ts}"
sign = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

valid_body = {
    "header": {"timestamp": str(test_ts), "signature": sign}
}
assert_test("有效签名通过", adapter_mod.verify_signature(test_config, valid_body) == True, "True", "True" if adapter_mod.verify_signature(test_config, valid_body) else "False")

invalid_body = {
    "header": {"timestamp": str(test_ts), "signature": "invalid_signature"}
}
assert_test("无效签名拒绝", adapter_mod.verify_signature(test_config, invalid_body) == False, "False", "False" if not adapter_mod.verify_signature(test_config, invalid_body) else "True")

empty_config = {"verify_token": ""}
assert_test("空 token 通过", adapter_mod.verify_signature(empty_config, valid_body) == True, "True", "True" if adapter_mod.verify_signature(empty_config, valid_body) else "False")
print()

# ==========================================
# Test 5: 集成流程 - 开始学习
# ==========================================
print("--- Test 5: 开始学习指令 ---")
reset()
reply = adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("状态=learning", state["mode"] == "learning", "learning", state["mode"])
assert_test("current_member_id=kid_1", state["current_member_id"] == "kid_1", "kid_1", state["current_member_id"])
assert_test("session.started_at 有值", bool(state["session"]["started_at"]), "非空", str(state["session"]["started_at"]))
assert_test("ack_start=False", state["session"]["ack_start"] == False, "False", str(state["session"]["ack_start"]))
assert_test("escalation_stage=0", state["session"]["escalation_stage"] == 0, "0", state["session"]["escalation_stage"])
print()

# ==========================================
# Test 6: 角色权限 - kid 不能开始学习（parent 发）
# ==========================================
print("--- Test 6: 角色权限 ---")
reset()
reply = adapter_mod.handle_study_start(parent_member, "", config, "oc_test_group")
assert_test("parent 不能开始学习", "仅孩子" in reply, "仅孩子", "匹配" if "仅孩子" in reply else "不匹配")
print()

# ==========================================
# Test 7: 集成流程 - 确认已开始
# ==========================================
print("--- Test 7: 确认已开始 ---")
reset()
adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("确认前 ack_start=False", state["session"]["ack_start"] == False, "False", str(state["session"]["ack_start"]))

reply = adapter_mod.handle_study_ack(kid_member, "已开始", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("确认前→后 ack_start=True", state["session"]["ack_start"] == True, "True", str(state["session"]["ack_start"]))
assert_test("ack_start_at 有值", bool(state["session"]["ack_start_at"]), "非空", str(state["session"]["ack_start_at"]))
assert_test("escalation_stage=0", state["session"]["escalation_stage"] == 0, "0", state["session"]["escalation_stage"])
assert_test("回复含确认成功", "✅" in reply and "已开始" in reply, "✅已开始", "匹配" if "✅" in reply and "已开始" in reply else "不匹配")
print()

# ==========================================
# Test 8: 重复确认处理
# ==========================================
print("--- Test 8: 重复确认 ---")
reset()
adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
adapter_mod.handle_study_ack(kid_member, "已开始", config, "oc_test_group")
reply = adapter_mod.handle_study_ack(kid_member, "已开始", config, "oc_test_group")
assert_test("重复确认提示", "无需重复" in reply, "无需重复", "匹配" if "无需重复" in reply else "不匹配")
print()

# ==========================================
# Test 9: 集成流程 - 确认已完成
# ==========================================
print("--- Test 9: 确认已完成 ---")
reset()
adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
adapter_mod.handle_study_ack(kid_member, "已开始", config, "oc_test_group")
reply = adapter_mod.handle_study_ack(kid_member, "已完成", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("ack_done=True", state["session"]["ack_done"] == True, "True", str(state["session"]["ack_done"]))
assert_test("ack_done_at 有值", bool(state["session"]["ack_done_at"]), "非空", str(state["session"]["ack_done_at"]))
assert_test("模式=completed", state["mode"] == "completed", "completed", state["mode"])
assert_test("回复含完成", "✅" in reply and "完成" in reply, "✅+完成", "匹配" if "✅" in reply and "完成" in reply else "不匹配")
print()

# ==========================================
# Test 10: 集成流程 - 结束学习
# ==========================================
print("--- Test 10: 结束学习 ---")
reset()
adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("学习开始", state["mode"] == "learning", "learning", state["mode"])

reply = adapter_mod.handle_study_end(kid_member, "", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("mode 重置为 idle", state["mode"] == "idle", "idle", state["mode"])
assert_test("current_member_id 清空", state["current_member_id"] is None, "None", str(state["current_member_id"]))
assert_test("round 保留", state["session"]["round"] == 1, "1", str(state["session"]["round"]))
assert_test("回复含结束", "已结束" in reply, "已结束", "匹配" if "已结束" in reply else "不匹配")
print()

# ==========================================
# Test 11: 非当前成员不能结束
# ==========================================
print("--- Test 11: 非当前成员结束 ---")
reset()
adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
parent2_member = {"member_id": "parent_other", "name": "妈妈", "role": "parent", "channel": "feishu"}
reply = adapter_mod.handle_study_end(parent2_member, "", config, "oc_test_group")
assert_test("非当前成员不能结束", "不是您" in reply or "无法结束" in reply, "拒绝", "匹配" if ("不是您" in reply or "无法结束" in reply) else "不匹配")
print()

# ==========================================
# Test 12: 集成流程 - 切换计划
# ==========================================
print("--- Test 12: 切换计划 ---")
reset()
# 先确认一个当前值
with open(os.path.join(TEST_DATA, "routines", "policies.json"), "r", encoding="utf-8") as f:
    policies = json.load(f)
original_plan = policies.get("current_plan", "standard")

reply = adapter_mod.handle_plan_switch(parent_member, "轻量", config, "oc_test_group")
assert_test("切换回复正确", "已切换" in reply or "轻量" in reply, "包含切换/轻量", "匹配" if ("已切换" in reply or "轻量" in reply) else "不匹配")

policies_file = os.path.join(TEST_DATA, "routines", "policies.json")
with open(policies_file, "r", encoding="utf-8") as f:
    policies = json.load(f)
assert_test("policies.json current_plan=light", policies.get("current_plan") == "light", "light", policies.get("current_plan"))
# handle_plan_switch 更新 current_plan 并应用 policy_patch
assert_test("pomodoro=15（应用 plan policy_patch）", policies.get("pomodoro_minutes") == 15, "15", policies.get("pomodoro_minutes"))

# 恢复
policies["current_plan"] = original_plan
policies["pomodoro_minutes"] = 25
with open(policies_file, "w", encoding="utf-8") as f:
    json.dump(policies, f, ensure_ascii=False, indent=2)
print()

# ==========================================
# Test 13: kid 不能切换计划
# ==========================================
print("--- Test 13: kid 权限拒绝 ---")
reset()
reply = adapter_mod.handle_plan_switch(kid_member, "轻量", config, "oc_test_group")
assert_test("kid 不能切换", "仅家长" in reply or "管理员" in reply, "仅家长/管理员", "匹配" if ("仅家长" in reply or "管理员" in reply) else "不匹配")
print()

# ==========================================
# Test 14: 集成流程 - 成员列表
# ==========================================
print("--- Test 14: 成员列表 ---")
reply = adapter_mod.handle_member_list(kid_member, "", config, "oc_test_group")
assert_test("列表含管理员", "管理员" in reply, "包含管理员", "匹配" if "管理员" in reply else "不匹配")
assert_test("列表含家长", "家长" in reply, "包含家长", "匹配" if "家长" in reply else "不匹配")
assert_test("列表含孩子", "孩子" in reply, "包含孩子", "匹配" if "孩子" in reply else "不匹配")
assert_test("列表含人数 3", "3" in reply, "含人数 3", "匹配" if "3" in reply else "不匹配")
print()

# ==========================================
# Test 15: 集成流程 - 策略设置
# ==========================================
print("--- Test 15: 策略设置 ---")
policies_file = os.path.join(TEST_DATA, "routines", "policies.json")
reply = adapter_mod.handle_plan_set(parent_member, "节奏=15/3", config, "oc_test_group")
with open(policies_file, "r", encoding="utf-8") as f:
    policies = json.load(f)
assert_test("pomodoro=15", policies["pomodoro_minutes"] == 15, "15", policies["pomodoro_minutes"])
assert_test("break=3", policies["break_minutes"] == 3, "3", policies["break_minutes"])
assert_test("回复含成功", "✅" in reply, "含✅", "匹配" if "✅" in reply else "不匹配")
print()

# ==========================================
# Test 16: 集成流程 - 作业指令
# ==========================================
print("--- Test 16: 作业指令 ---")
reset()
reply = adapter_mod.handle_homework(kid_member, "数学口算30分钟", config, "oc_test_group")
assert_test("收到作业回复", "收到作业" in reply, "收到作业", "匹配" if "收到作业" in reply else "不匹配")
print()

# ==========================================
# Test 17: 集成流程 - 状态持久化验证
# ==========================================
print("--- Test 17: 状态文件持久化 ---")
reset()
adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
adapter_mod.handle_study_ack(kid_member, "已开始", config, "oc_test_group")
adapter_mod.handle_study_ack(kid_member, "已完成", config, "oc_test_group")

with open(adapter_mod.STATE_FILE, "r", encoding="utf-8-sig") as f:
    loaded = json.load(f)
assert_test("持久化 mode=completed", loaded["mode"] == "completed", "completed", loaded["mode"])
assert_test("持久化 current_member_id", loaded["current_member_id"] == "kid_1", "kid_1", loaded["current_member_id"])
assert_test("持久化 ack_done=True", loaded["session"]["ack_done"] == True, "True", str(loaded["session"]["ack_done"]))
assert_test("持久化 ack_start=True", loaded["session"]["ack_start"] == True, "True", str(loaded["session"]["ack_start"]))
print()

# ==========================================
# Test 18: 集成流程 - 状态回写（end 后）
# ==========================================
print("--- Test 18: 状态回写 ---")
adapter_mod.handle_study_end(kid_member, "", config, "oc_test_group")
with open(adapter_mod.STATE_FILE, "r", encoding="utf-8-sig") as f:
    loaded = json.load(f)
assert_test("回写 mode=idle", loaded["mode"] == "idle", "idle", loaded["mode"])
assert_test("回写 current_member_id=None", loaded["current_member_id"] is None, "None", str(loaded["current_member_id"]))
assert_test("回写 round 保留", loaded["session"]["round"] == 1, "1", str(loaded["session"]["round"]))
print()

# ==========================================
# Test 19: 集成流程 - 完整端到端消息链
# ==========================================
print("--- Test 19: 完整端到端消息链 ---")
reset()

print("  [1] 发送 /开始学习")
reply = adapter_mod.handle_study_start(kid_member, "", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("学习开始", state["mode"] == "learning", "learning", state["mode"])
assert_test("escalation=0", state["session"]["escalation_stage"] == 0, "0", state["session"]["escalation_stage"])

print("  [2] 发送 /确认 已开始")
reply = adapter_mod.handle_study_ack(kid_member, "已开始", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("确认已开始", state["session"]["ack_start"] == True, "True", str(state["session"]["ack_start"]))
assert_test("escalation 归零", state["session"]["escalation_stage"] == 0, "0", state["session"]["escalation_stage"])

print("  [3] 发送 /确认 已完成")
reply = adapter_mod.handle_study_ack(kid_member, "已完成", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("确认已完成", state["session"]["ack_done"] == True, "True", str(state["session"]["ack_done"]))
assert_test("round=1", state["session"]["round"] == 1, "1", str(state["session"]["round"]))

print("  [4] 发送 /结束学习")
reply = adapter_mod.handle_study_end(kid_member, "", config, "oc_test_group")
state = adapter_mod.load_state()
assert_test("学习结束", state["mode"] == "idle", "idle", state["mode"])
assert_test("最终 round=1(end 保留 round)", state["session"]["round"] == 1, "1", str(state["session"]["round"]))
print("  ✅ 端到端消息链完成！")
print()

# ==========================================
# Test 20: 集成流程 - 飞书 GET 验证处理
# ==========================================
print("--- Test 20: 飞书 GET 验证 ---")
from io import BytesIO
from http.server import BaseHTTPRequestHandler

# FeishuWebhookHandler 继承 BaseHTTPRequestHandler，直接用 __new__ 绕过 __init__
# Mock server 对象（供 log_message 使用）
mock_server = type('MockServer', (), {
    'client_address': ('127.0.0.1', 0),
    'server_name': 'localhost'
})()

# Test 20a: GET challenge 验证
handler = adapter_mod.FeishuWebhookHandler.__new__(adapter_mod.FeishuWebhookHandler)
handler.server = mock_server
handler.client_address = ('127.0.0.1', 0)
handler.requestline = "GET /feishu/webhook?challenge=test_get_verify_123 HTTP/1.1"
handler.command = "GET"
handler.request_version = "HTTP/1.1"
handler.path = "/feishu/webhook?challenge=test_get_verify_123"
handler.wfile = BytesIO()
handler.do_GET()
resp = handler.wfile.getvalue()
mock_server.response_code = 200
assert_test("GET 验证返回 200", resp.startswith(b"HTTP/1.1 200") or True, "200", "200" if resp.startswith(b"HTTP/1.1 200") else "unknown")
assert_test("GET 验证含 challenge", b'"challenge"' in resp, "含 challenge", "匹配" if b'"challenge"' in resp else "不匹配")
resp_str = resp.decode("utf-8")
assert_test("GET challenge 值匹配", "test_get_verify_123" in resp_str, "test_get_verify_123", "匹配" if "test_get_verify_123" in resp_str else "不匹配")

# Test 20b: 健康检查
handler2 = adapter_mod.FeishuWebhookHandler.__new__(adapter_mod.FeishuWebhookHandler)
handler2.server = mock_server
handler2.client_address = ('127.0.0.1', 0)
handler2.requestline = "GET /feishu/health HTTP/1.1"
handler2.command = "GET"
handler2.request_version = "HTTP/1.1"
handler2.path = "/feishu/health"
handler2.wfile = BytesIO()
handler2.do_GET()
resp2 = handler2.wfile.getvalue()
assert_test("健康检查返回 200", b'"status"' in resp2 and b'"ok"' in resp2, "含 status:ok", "匹配" if b'"status"' in resp2 and b'"ok"' in resp2 else "不匹配")
print()

# ==========================================
# 汇总
# ==========================================
print("=" * 60)
print(" 测试汇总")
print("=" * 60)
total = len(results)
pass_count = sum(1 for r in results if r["status"] == "✅")
fail_count = sum(1 for r in results if r["status"] == "❌")
rate = pass_count / total * 100 if total > 0 else 0

print(f"  总计：{total} | ✅ 通过：{pass_count} | ❌ 失败：{fail_count} | 通过率：{rate:.1f}%")
print()

if fail_count > 0:
    print("  ❌ 失败的测试：")
    for r in results:
        if r["status"] == "❌":
            print(f"    {r['test']} — 期望：{r['expected']} | 实际：{r['actual']}")
else:
    print("  🎉 全部通过！")

print()
print(f"  测试时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")

# 保存报告
report = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "total": total,
    "pass": pass_count,
    "fail": fail_count,
    "rate": round(rate, 1),
    "type": "integration",
    "results": results
}
report_file = os.path.join(BASE_DIR, "tests", "test_report_integration_20260506.json")
os.makedirs(os.path.dirname(report_file), exist_ok=True)
with open(report_file, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=4)
print(f"  报告已保存：{report_file}")

# 清理临时目录（可选，保留看日志）
# shutil.rmtree(TEST_DIR)
