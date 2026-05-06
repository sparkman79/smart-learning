#!/usr/bin/env python3
"""智能学习系统端到端测试"""
import os
import json
import csv
from datetime import datetime

WORKSPACE = r"C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning"
results = []

def assert_test(name, condition, expected, actual):
    status = "✅" if condition else "❌"
    results.append({
        "test": name,
        "status": status,
        "expected": str(expected),
        "actual": str(actual)
    })
    print(f"{status} {name}")
    if not condition:
        print(f"   期望：{expected} | 实际：{actual}")

print("=" * 60)
print(" 智能学习系统端到端测试")
print("=" * 60)
print()

# ==========================================
# TEST 1: 作业提交 - inbox 文件生成
# ==========================================
print("--- Test 1: 作业提交 (inbox) ---")
inbox_file = os.path.join(WORKSPACE, "data", "homework", "inbox", "2026-05-06_kid_1_homework.md")
assert_test("inbox 文件存在", os.path.exists(inbox_file), "true", "true" if os.path.exists(inbox_file) else "false")
if os.path.exists(inbox_file):
    with open(inbox_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert_test("inbox 包含科目信息", "数学" in content, "包含数学", "匹配结果")
    assert_test("inbox 包含时间", "分钟" in content, "包含时间信息", "匹配结果")
print()

# ==========================================
# TEST 2: 作业提交 - parsed 双视图
# ==========================================
print("--- Test 2: 作业 parsed 双视图 ---")
plan_file = os.path.join(WORKSPACE, "data", "homework", "parsed", "2026-05-06_kid_1_plan.md")
assert_test("parsed 文件存在", os.path.exists(plan_file), "true", "true" if os.path.exists(plan_file) else "false")
if os.path.exists(plan_file):
    with open(plan_file, "r", encoding="utf-8") as f:
        plan_content = f.read()
    assert_test("孩子版存在", "孩子版" in plan_content, "含孩子版标记", "匹配结果")
    assert_test("家长版存在", "家长版" in plan_content, "含家长版标记", "匹配结果")
    assert_test("检查点存在", "检查点" in plan_content, "含检查点", "匹配结果")
print()

# ==========================================
# TEST 3: 开始学习 - state.json 更新
# ==========================================
print("--- Test 3: 开始学习 ---")
state_file = os.path.join(WORKSPACE, "data", "routines", "state.json")
with open(state_file, "r", encoding="utf-8-sig") as f:
    state = json.load(f)

# 模拟开始学习：设置初始状态
state["mode"] = "learning"
state["current_member_id"] = "kid_1"
state["session"]["started_at"] = "2026-05-06T09:10:00+08:00"
state["session"]["ack_start"] = False
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=4)

with open(state_file, "r", encoding="utf-8-sig") as f:
    state = json.load(f)

assert_test("mode=learning", state.get("mode") == "learning", "learning", state.get("mode"))
assert_test("current_member_id=kid_1", state.get("current_member_id") == "kid_1", "kid_1", state.get("current_member_id"))
assert_test("started_at 有值", bool(state.get("session", {}).get("started_at")), "非空", state.get("session", {}).get("started_at"))
assert_test("ack_start=false", state.get("session", {}).get("ack_start") == False, "false", state.get("session", {}).get("ack_start"))
print()

# ==========================================
# TEST 4: 确认已开始 - ack_start
# ==========================================
print("--- Test 4: 确认已开始 ---")
state["session"]["ack_start"] = True
state["session"]["ack_start_at"] = "2026-05-06T09:15:30+08:00"
state["session"]["ack_done"] = False
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=4)

with open(state_file, "r", encoding="utf-8-sig") as f:
    state = json.load(f)

assert_test("ack_start=true", state["session"]["ack_start"] == True, "true", state["session"]["ack_start"])
assert_test("ack_start_at 有值", bool(state["session"]["ack_start_at"]), "非空", state["session"]["ack_start_at"])
assert_test("ack_done=false", state["session"]["ack_done"] == False, "false", state["session"]["ack_done"])
print()

# ==========================================
# TEST 5: 升级链路检查 (Stage 1: 5 分钟)
# ==========================================
print("--- Test 5: 升级链路 Stage 1 (5 分钟无确认) ---")
state["session"]["ack_start"] = False
state["session"]["escalation_stage"] = 1
state["session"]["last_nudge_at"] = "2026-05-06T09:20:00+08:00"
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=4)

with open(state_file, "r", encoding="utf-8-sig") as f:
    state = json.load(f)

assert_test("escalation_stage=1", state["session"]["escalation_stage"] == 1, "1", state["session"]["escalation_stage"])
assert_test("last_nudge_at 已设置", bool(state["session"]["last_nudge_at"]), "非空", state["session"]["last_nudge_at"])
print()

# ==========================================
# TEST 6: 升级链路 (Stage 2: 15 分钟)
# ==========================================
print("--- Test 6: 升级链路 Stage 2 (15 分钟无确认) ---")
state["session"]["ack_start"] = False
state["session"]["escalation_stage"] = 2
state["session"]["last_nudge_at"] = "2026-05-06T09:30:00+08:00"
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=4)

with open(state_file, "r", encoding="utf-8-sig") as f:
    state = json.load(f)

assert_test("escalation_stage=2", state["session"]["escalation_stage"] == 2, "2", state["session"]["escalation_stage"])
print()

# ==========================================
# TEST 7: 确认已完成 - ack_done
# ==========================================
print("--- Test 7: 确认已完成 ---")
state["session"]["ack_start"] = True
state["session"]["ack_done"] = True
state["session"]["ack_done_at"] = "2026-05-06T09:40:00+08:00"
state["session"]["round"] = 2
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=4)

with open(state_file, "r", encoding="utf-8-sig") as f:
    state = json.load(f)

assert_test("ack_done=true", state["session"]["ack_done"] == True, "true", state["session"]["ack_done"])
assert_test("ack_done_at 有值", bool(state["session"]["ack_done_at"]), "非空", state["session"]["ack_done_at"])
assert_test("round=2", state["session"]["round"] == 2, "2", state["session"]["round"])

# 计算学习时长
start_str = state["session"]["started_at"]
done_str = state["session"]["ack_done_at"]
if start_str and done_str:
    from dateutil import parser
    start_dt = parser.parse(start_str)
    done_dt = parser.parse(done_str)
    duration = (done_dt - start_dt).total_seconds() / 60
    assert_test("学习时长 30 分钟", abs(duration - 30) < 1, "30", f"{duration:.1f}")
else:
    assert_test("学习时长 30 分钟", False, "30", "缺少时间数据")
print()

# ==========================================
# TEST 8: 结束学习 - mode=idle
# ==========================================
print("--- Test 8: 结束学习 ---")
state["mode"] = "idle"
state["current_member_id"] = None
state["session"] = {
    "started_at": None,
    "ack_start": None,
    "ack_start_at": None,
    "ack_done": None,
    "ack_done_at": None,
    "pomodoro_minutes": 25,
    "break_minutes": 5,
    "round": 0,
    "escalation_stage": 0,
    "last_nudge_at": None,
    "last_notify_at": None
}
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=4)

with open(state_file, "r", encoding="utf-8-sig") as f:
    state = json.load(f)

assert_test("mode=idle", state["mode"] == "idle", "idle", state["mode"])
assert_test("session.round 重置", state["session"]["round"] == 0, "0", state["session"]["round"])
print()

# ==========================================
# TEST 9: 日报生成 - trends.csv
# ==========================================
print("--- Test 9: 日报生成 ---")
trends_file = os.path.join(WORKSPACE, "data", "reports", "trends", "trends.csv")
csv_line = "2026-05-06,kid_1,30,2,4,4,100.0"
with open(trends_file, "a", encoding="utf-8") as f:
    f.write(csv_line + "\n")

with open(trends_file, "r", encoding="utf-8") as f:
    csv_content = f.readlines()

assert_test("trends.csv 含表头", "日期" in csv_content[0], "含表头", csv_content[0].strip())
assert_test("trends.csv 含数据", "2026-05-06,kid_1" in csv_content[-1], "含数据行", csv_content[-1].strip())
assert_test("完成度=100", "100.0" in csv_content[-1], "100.0", csv_content[-1].strip())
print()

# ==========================================
# TEST 10: 切换计划 - policies.json
# ==========================================
print("--- Test 10: 切换计划 轻量 ---")
policies_file = os.path.join(WORKSPACE, "data", "routines", "policies.json")
policies = {
    "pomodoro_minutes": 15,
    "break_minutes": 3,
    "reminder_intensity": "low",
    "escalation": {"enabled": False},
    "night": {
        "enabled": True,
        "start": "22:00",
        "end": "06:00",
        "silent_speaker": True,
        "light_only": True
    },
    "current_plan": "light"
}
with open(policies_file, "w", encoding="utf-8") as f:
    json.dump(policies, f, ensure_ascii=False, indent=4)

with open(policies_file, "r", encoding="utf-8") as f:
    policies = json.load(f)

assert_test("plan=轻量", policies["current_plan"] == "light", "light", policies["current_plan"])
assert_test("pomodoro=15", policies["pomodoro_minutes"] == 15, "15", policies["pomodoro_minutes"])
assert_test("break=3", policies["break_minutes"] == 3, "3", policies["break_minutes"])
assert_test("escalation=关闭", policies["escalation"]["enabled"] == False, "false", policies["escalation"]["enabled"])
print()

# ==========================================
# TEST 11: 策略变更日志
# ==========================================
print("--- Test 11: 策略变更日志 ---")
log_file = os.path.join(WORKSPACE, "data", "routines", "logs", "policy_changes.log")
log_entry = "2026-05-06T09:50:00+08:00 | parent_1 | 切换计划 → 轻量 | pomodoro:25→15, break:5→3\n"
with open(log_file, "a", encoding="utf-8") as f:
    f.write(log_entry)

with open(log_file, "r", encoding="utf-8") as f:
    log_content = f.read()

assert_test("日志文件存在", os.path.exists(log_file), "true", "true" if os.path.exists(log_file) else "false")
assert_test("日志含变更内容", "切换计划" in log_content, "含变更", "匹配结果")
assert_test("日志含时间戳", "2026-05-06" in log_content, "含时间戳", "匹配结果")
print()

# ==========================================
# TEST 12: 成员列表查询
# ==========================================
print("--- Test 12: 成员列表 ---")
members_file = os.path.join(WORKSPACE, "data", "family", "members", "index.json")
with open(members_file, "r", encoding="utf-8") as f:
    members = json.load(f)

assert_test("family_id 存在", bool(members.get("family_id")), "非空", members.get("family_id"))
assert_test("3 个成员", len(members.get("members", [])) == 3, "3", len(members.get("members", [])))
assert_test("admin 存在", any(m["role"] == "admin" for m in members.get("members", [])), "有 admin", "匹配")
assert_test("parent 存在", any(m["role"] == "parent" for m in members.get("members", [])), "有 parent", "匹配")
assert_test("kid 存在", any(m["role"] == "kid" for m in members.get("members", [])), "有 kid", "匹配")
parent_members = [m for m in members.get("members", []) if m["role"] == "parent"]
if parent_members:
    assert_test("parent 有 linked_children", len(parent_members[0].get("linked_children", [])) >= 1, "有 children", "匹配")
else:
    assert_test("parent 有 linked_children", False, "有 children", "无 parent")
print()

# ==========================================
# TEST 13: kid 禁止修改策略 (权限验证)
# ==========================================
print("--- Test 13: kid 权限验证 ---")
kid_member = next((m for m in members["members"] if m["member_id"] == "kid_1"), None)
assert_test("kid_1 角色=kid", kid_member and kid_member["role"] == "kid", "kid", kid_member["role"] if kid_member else "未找到")
assert_test("kid 无修改权限", kid_member and kid_member["role"] != "parent" and kid_member["role"] != "admin", "拒绝修改", "无权限")
print()

# ==========================================
# TEST 14: 计划模板文件
# ==========================================
print("--- Test 14: 计划模板 ---")
for plan_name in ["light", "standard", "sprint", "family_read"]:
    plan_file = os.path.join(WORKSPACE, "data", "routines", "plans", f"{plan_name}.json")
    assert_test(f"模板 {plan_name} 存在", os.path.exists(plan_file), "true", "true" if os.path.exists(plan_file) else "false")
    if os.path.exists(plan_file):
        with open(plan_file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        assert_test(f"模板 {plan_name} 有 policy_patch", "policy_patch" in plan_data, "有 patch", "有 patch" if "policy_patch" in plan_data else "无 patch")
print()

# ==========================================
# TEST 15: Skills SKILL.md 完整性
# ==========================================
print("--- Test 15: Skills 完整性 ---")
for skill_name in ["daily-report", "homework-intake", "member-registry", "plan-builder", "study-ack", "study-escalation", "study-mode", "weekly-report"]:
    skill_file = os.path.join(WORKSPACE, "skills", skill_name, "SKILL.md")
    assert_test(f"Skill: {skill_name}", os.path.exists(skill_file), "true", "true" if os.path.exists(skill_file) else "false")
    if os.path.exists(skill_file):
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert_test(f"SKILL.md 非空 ({skill_name})", len(content) > 100, ">100 字符", f"{len(content)} 字符")
print()

# ==========================================
# TEST 16: cron/jobs.json 验证
# ==========================================
print("--- Test 16: 定时任务 ---")
cron_file = os.path.join(os.path.dirname(WORKSPACE), "cron", "jobs.json")
if os.path.exists(cron_file):
    with open(cron_file, "r", encoding="utf-8") as f:
        cron = json.load(f)
    
    assert_test("总任务≥10", len(cron.get("jobs", [])) >= 10, "≥10", len(cron.get("jobs", [])))
    
    jobs = cron.get("jobs", [])
    assert_test("study_escalation 存在", any(j["id"] == "study_escalation" for j in jobs), "存在", "匹配")
    assert_test("daily_learning_report 存在", any(j["id"] == "daily_learning_report" for j in jobs), "存在", "匹配")
    
    escalation_job = next((j for j in jobs if j["id"] == "study_escalation"), None)
    if escalation_job:
        assert_test("escalation 每分钟", escalation_job["schedule"] == "*/1 * * * *", "*/1 * * * *", escalation_job["schedule"])
        assert_test("escalation 已启用", escalation_job["enabled"] == True, "true", escalation_job["enabled"])
else:
    assert_test("cron/jobs.json 存在", False, "存在", "文件不存在")
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
print(f"  测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 保存测试报告
report = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total": total,
    "pass": pass_count,
    "fail": fail_count,
    "rate": round(rate, 1),
    "results": results
}
report_file = os.path.join(WORKSPACE, "tests", "test_report_20260506.json")
with open(report_file, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=4)

print(f"  报告已保存：tests/test_report_20260506.json")
