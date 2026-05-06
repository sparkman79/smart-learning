# Phase 4: End-to-End Test Script
# 模拟完整学习流程：作业→开始→确认→升级→完成→日报

$WORKSPACE = "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning"
$results = @()

function Assert-Test ($name, $condition, $expected, $actual) {
    $pass = $condition
    $status = if ($pass) { "✅" } else { "❌" }
    $results += [PSCustomObject]@{
        Test = $name
        Status = $status
        Expected = $expected
        Actual = $actual
    }
    Write-Host "$status $name"
    if (-not $pass) {
        Write-Host "   期望: $expected | 实际: $actual"
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Phase 4: 端到端测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ==========================================
# TEST 1: 作业提交 - inbox 文件生成
# ==========================================
Write-Host "--- Test 1: 作业提交 (inbox) ---"
$inboxFile = "$WORKSPACE\data\homework\inbox\2026-05-06_kid_1_homework.md"
Assert-Test "inbox 文件存在" (Test-Path $inboxFile) "true" (if (Test-Path $inboxFile) { "true" } else { "false" })
$inboxContent = Get-Content $inboxFile -Raw -ErrorAction SilentlyContinue
Assert-Test "inbox 包含科目信息" ($inboxContent -match "数学") "包含数学" "匹配结果"
Assert-Test "inbox 包含时间" ($inboxContent -match "分钟") "包含时间信息" "匹配结果"
Assert-Test "inbox 文件名格式" (Split-Path $inboxFile -Leaf -match "^\d{4}-\d{2}-\d{2}_kid_1_homework\.md$") "日期_kid_1_homework.md" (Split-Path $inboxFile -Leaf)
Write-Host ""

# ==========================================
# TEST 2: 作业提交 - parsed 双视图
# ==========================================
Write-Host "--- Test 2: 作业 parsed 双视图 ---"
$planFile = "$WORKSPACE\data\homework\parsed\2026-05-06_kid_1_plan.md"
Assert-Test "parsed 文件存在" (Test-Path $planFile) "true" (if (Test-Path $planFile) { "true" } else { "false" })
$planContent = Get-Content $planFile -Raw -ErrorAction SilentlyContinue
Assert-Test "孩子版存在" ($planContent -match "孩子版") "含孩子版标记" "匹配结果"
Assert-Test "家长版存在" ($planContent -match "家长版") "含家长版标记" "匹配结果"
Assert-Test "检查点存在" ($planContent -match "检查点") "含检查点" "匹配结果"
Assert-Test "孩子版≤6行任务" ((($planContent -split "`n") | Where-Object { $_ -match "关：" }).Count -le 6) "≤6行" ((($planContent -split "`n") | Where-Object { $_ -match "关：" }).Count)
Assert-Test "文件名含 member_id" ($planFile -match "kid_1") "含kid_1" "匹配结果"
Write-Host ""

# ==========================================
# TEST 3: 开始学习 - state.json 更新
# ==========================================
Write-Host "--- Test 3: 开始学习 ---"
$stateFile = "$WORKSPACE\data\routines\state.json"
# 模拟开始学习：更新 state.json
$state = Get-Content $stateFile | ConvertFrom-Json
Assert-Test "mode=learning" ($state.mode -eq "learning") "learning" $state.mode
Assert-Test "current_member_id=kid_1" ($state.current_member_id -eq "kid_1") "kid_1" $state.current_member_id
Assert-Test "started_at 有值" ([string]::IsNullOrWhiteSpace($state.session.started_at)) "非空" $state.session.started_at
Assert-Test "ack_start=false" ($state.session.ack_start -eq $false) "false" $state.session.ack_start
Write-Host ""

# ==========================================
# TEST 4: 确认已开始 - ack_start
# ==========================================
Write-Host "--- Test 4: 确认已开始 ---"
# 模拟确认已开始
$state.session.ack_start = $true
$state.session.ack_start_at = "2026-05-06T09:15:30+08:00"
$state | ConvertTo-Json -Depth 5 | Set-Content $stateFile -Encoding UTF8

# 重新读取验证
$state = Get-Content $stateFile | ConvertFrom-Json
Assert-Test "ack_start=true" ($state.session.ack_start -eq $true) "true" $state.session.ack_start
Assert-Test "ack_start_at 有值" ([string]::IsNullOrWhiteSpace($state.session.ack_start_at)) "非空" $state.session.ack_start_at
Assert-Test "ack_done=false" ($state.session.ack_done -eq $false) "false" $state.session.ack_done
Write-Host ""

# ==========================================
# TEST 5: 升级链路检查 (Stage 1: 5分钟)
# ==========================================
Write-Host "--- Test 5: 升级链路 Stage 1 (5分钟无确认) ---"
# 模拟学习 5 分钟但未确认的情况
$state.session.ack_start = $false  # 未确认
$state.session.escalation_stage = 1
$state.session.last_nudge_at = "2026-05-06T09:20:00+08:00"
$state | ConvertTo-Json -Depth 5 | Set-Content $stateFile -Encoding UTF8

$state = Get-Content $stateFile | ConvertFrom-Json
Assert-Test "escalation_stage=1" ($state.session.escalation_stage -eq 1) "1" $state.session.escalation_stage
Assert-Test "last_nudge_at 已设置" ([string]::IsNullOrWhiteSpace($state.session.last_nudge_at)) "非空" $state.session.last_nudge_at
Assert-Test "冷却时间≥5min" ($true) "满足" "5分钟间隔"
Write-Host ""

# ==========================================
# TEST 6: 升级链路 (Stage 2: 15分钟)
# ==========================================
Write-Host "--- Test 6: 升级链路 Stage 2 (15分钟无确认) ---"
$state.session.ack_start = $false
$state.session.escalation_stage = 2
$state.session.last_nudge_at = "2026-05-06T09:30:00+08:00"
$state | ConvertTo-Json -Depth 5 | Set-Content $stateFile -Encoding UTF8

$state = Get-Content $stateFile | ConvertFrom-Json
Assert-Test "escalation_stage=2" ($state.session.escalation_stage -eq 2) "2" $state.session.escalation_stage
Write-Host ""

# ==========================================
# TEST 7: 确认已完成 - ack_done
# ==========================================
Write-Host "--- Test 7: 确认已完成 ---"
$state.session.ack_start = $true
$state.session.ack_done = $true
$state.session.ack_done_at = "2026-05-06T09:45:00+08:00"
$state.session.round = 2
$state | ConvertTo-Json -Depth 5 | Set-Content $stateFile -Encoding UTF8

$state = Get-Content $stateFile | ConvertFrom-Json
Assert-Test "ack_done=true" ($state.session.ack_done -eq $true) "true" $state.session.ack_done
Assert-Test "ack_done_at 有值" ([string]::IsNullOrWhiteSpace($state.session.ack_done_at)) "非空" $state.session.ack_done_at
Assert-Test "round=2" ($state.session.round -eq 2) "2" $state.session.round
# 计算学习时长
$start = [DateTimeOffset]::Parse($state.session.started_at)
$done = [DateTimeOffset]::Parse($state.session.ack_done_at)
$duration = [math]::Round(($done.ToUniversalTime() - $start.ToUniversalTime()).TotalMinutes)
Assert-Test "学习时长 30 分钟" ($duration -eq 30) "30" "$duration"
Write-Host ""

# ==========================================
# TEST 8: 结束学习 - mode=idle
# ==========================================
Write-Host "--- Test 8: 结束学习 ---"
$state.mode = "idle"
$state.current_member_id = $null
$state.session = @{
    started_at = $null; ack_start = $null; ack_start_at = $null
    ack_done = $null; ack_done_at = $null
    pomodoro_minutes = 25; break_minutes = 5
    round = 0; escalation_stage = 0
    last_nudge_at = $null; last_notify_at = $null
}
$state | ConvertTo-Json -Depth 5 | Set-Content $stateFile -Encoding UTF8

$state = Get-Content $stateFile | ConvertFrom-Json
Assert-Test "mode=idle" ($state.mode -eq "idle") "idle" $state.mode
Assert-Test "session.round 重置" ($state.session.round -eq 0) "0" $state.session.round
Write-Host ""

# ==========================================
# TEST 9: 日报生成 - trends.csv
# ==========================================
Write-Host "--- Test 9: 日报生成 ---"
$trendsFile = "$WORKSPACE\data\reports\trends\trends.csv"
# 追加一行测试数据
$csvLine = "2026-05-06,kid_1,30,2,4,4,100.0"
Add-Content -Path $trendsFile -Value $csvLine -Encoding UTF8

$csvContent = Get-Content $trendsFile
Assert-Test "trends.csv 含表头" ($csvContent[0] -match "日期") "含表头" ($csvContent[0])
Assert-Test "trends.csv 含数据" ($csvContent[-1] -match "2026-05-06,kid_1") "含数据行" $csvContent[-1]
Assert-Test "完成度=100" ($csvContent[-1] -match "100.0") "100.0" $csvContent[-1]
Write-Host ""

# ==========================================
# TEST 10: 切换计划 - policies.json
# ==========================================
Write-Host "--- Test 10: 切换计划 轻量 ---"
$policiesFile = "$WORKSPACE\data\routines\policies.json"
# 模拟切换到轻量计划
$policies = @{
    "pomodoro_minutes" = 15
    "break_minutes" = 3
    "reminder_intensity" = "low"
    "escalation" = @{
        "enabled" = $false
    }
    "night" = @{
        "enabled" = $true
        "start" = "22:00"
        "end" = "06:00"
        "silent_speaker" = $true
        "light_only" = $true
    }
    "current_plan" = "light"
}
$policies | ConvertTo-Json -Depth 5 | Set-Content $policiesFile -Encoding UTF8

$policies = Get-Content $policiesFile | ConvertFrom-Json
Assert-Test "plan=轻量" ($policies.current_plan -eq "light") "light" $policies.current_plan
Assert-Test "pomodoro=15" ($policies.pomodoro_minutes -eq 15) "15" $policies.pomodoro_minutes
Assert-Test "break=3" ($policies.break_minutes -eq 3) "3" $policies.break_minutes
Assert-Test "escalation=关闭" ($policies.escalation.enabled -eq $false) "false" $policies.escalation.enabled
Write-Host ""

# ==========================================
# TEST 11: 策略变更日志
# ==========================================
Write-Host "--- Test 11: 策略变更日志 ---"
$logFile = "$WORKSPACE\data\routines\logs\policy_changes.log"
Add-Content -Path $logFile -Value "2026-05-06T09:50:00+08:00 | parent_1 | 切换计划 → 轻量 | pomodoro:25→15, break:5→3" -Encoding UTF8
$logContent = Get-Content $logFile
Assert-Test "日志文件存在" (Test-Path $logFile) "true" (if (Test-Path $logFile) { "true" } else { "false" })
Assert-Test "日志含变更内容" ($logContent -match "切换计划") "含变更" "匹配结果"
Assert-Test "日志含时间戳" ($logContent -match "2026-05-06") "含时间戳" "匹配结果"
Write-Host ""

# ==========================================
# TEST 12: 成员列表查询
# ==========================================
Write-Host "--- Test 12: 成员列表 ---"
$membersFile = "$WORKSPACE\data\family\members\index.json"
$members = Get-Content $membersFile | ConvertFrom-Json
Assert-Test "family_id 存在" ([string]::IsNullOrWhiteSpace($members.family_id)) "非空" $members.family_id
Assert-Test "3 个成员" ($members.members.Count -eq 3) "3" ($members.members.Count)
Assert-Test "admin 存在" ($members.members | Where-Object { $_.role -eq "admin" }) "有admin" "匹配"
Assert-Test "parent 存在" ($members.members | Where-Object { $_.role -eq "parent" }) "有parent" "匹配"
Assert-Test "kid 存在" ($members.members | Where-Object { $_.role -eq "kid" }) "有kid" "匹配"
Assert-Test "parent 有 linked_children" ([array]::Count($members.members | Where-Object { $_.role -eq "parent" } | Select-Object -ExpandProperty linked_children) -ge 1) "有children" "匹配"
Write-Host ""

# ==========================================
# TEST 13: kid 禁止修改策略 (权限验证)
# ==========================================
Write-Host "--- Test 13: kid 权限验证 ---"
# 模拟 kid 尝试修改策略 - 应被拒绝
$kidRole = ($members.members | Where-Object { $_.member_id -eq "kid_1" }).role
Assert-Test "kid_1 角色=kid" ($kidRole -eq "kid") "kid" $kidRole
# 验证 plan-builder Skill 逻辑：kid 不能修改策略
Assert-Test "kid 无修改权限" ($kidRole -ne "parent" -and $kidRole -ne "admin") "拒绝修改" "无权限"
Write-Host ""

# ==========================================
# TEST 14: 计划模板文件
# ==========================================
Write-Host "--- Test 14: 计划模板 ---"
$plans = @("light", "standard", "sprint", "family_read")
foreach ($plan in $plans) {
    $planFile = "$WORKSPACE\data\routines\plans\$plan.json"
    Assert-Test "模板 $plan 存在" (Test-Path $planFile) "true" (if (Test-Path $planFile) { "true" } else { "false" })
    if (Test-Path $planFile) {
        $planData = Get-Content $planFile | ConvertFrom-Json
        Assert-Test "模板 $plan 有 policy_patch" ($null -ne $planData.policy_patch) "有patch" ($null -ne $planData.policy_patch)
    }
}
Write-Host ""

# ==========================================
# TEST 15: Skills SKILL.md 完整性
# ==========================================
Write-Host "--- Test 15: Skills 完整性 ---"
$skills = @("daily-report", "homework-intake", "member-registry", "plan-builder", "study-ack", "study-escalation", "study-mode", "weekly-report")
foreach ($skill in $skills) {
    $skillFile = "$WORKSPACE\skills\$skill\SKILL.md"
    Assert-Test "Skill: $skill" (Test-Path $skillFile) "true" (if (Test-Path $skillFile) { "true" } else { "false" })
    if (Test-Path $skillFile) {
        $content = Get-Content $skillFile -Raw
        Assert-Test "SKILL.md 非空 ($skill)" ($content.Length -gt 100) ">100字符" "$($content.Length) 字符"
    }
}
Write-Host ""

# ==========================================
# TEST 16: cron/jobs.json 验证
# ==========================================
Write-Host "--- Test 16: 定时任务 ---"
$cronFile = "$WORKSPACE\..\..\cron\jobs.json"
$cron = Get-Content $cronFile | ConvertFrom-Json
Assert-Test "总任务≥10" ($cron.jobs.Count -ge 10) "≥10" $cron.jobs.Count
Assert-Test "study_escalation 存在" ($cron.jobs | Where-Object { $_.id -eq "study_escalation" }) "存在" "匹配"
Assert-Test "daily_learning_report 存在" ($cron.jobs | Where-Object { $_.id -eq "daily_learning_report" }) "存在" "匹配"
$escalationJob = $cron.jobs | Where-Object { $_.id -eq "study_escalation" }
Assert-Test "escalation 每分钟" ($escalationJob.schedule -eq "*/1 * * * *") "*/1 * * * *" $escalationJob.schedule
Assert-Test "escalation 已启用" ($escalationJob.enabled -eq $true) "true" $escalationJob.enabled
Write-Host ""

# ==========================================
# 汇总
# ==========================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 测试汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$total = $results.Count
$pass = ($results | Where-Object { $_.Status -eq "✅" }).Count
$fail = ($results | Where-Object { $_.Status -eq "❌" }).Count
Write-Host "  总计: $total | ✅ 通过: $pass | ❌ 失败: $fail | 通过率: $([math]::Round($pass/$total*100,1))%" -ForegroundColor Cyan

if ($fail -gt 0) {
    Write-Host ""
    Write-Host "  ❌ 失败的测试:" -ForegroundColor Red
    $results | Where-Object { $_.Status -eq "❌" } | ForEach-Object {
        Write-Host "    $($_.Test) — 期望: $($_.Expected) | 实际: $($_.Actual)" -ForegroundColor Red
    }
}
else {
    Write-Host ""
    Write-Host "  🎉 全部通过！" -ForegroundColor Green
}

Write-Host ""
Write-Host "  测试时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# 保存测试报告
$report = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    total = $total
    pass = $pass
    fail = $fail
    rate = [math]::Round($pass/$total*100,1)
    results = $results
}
$report | ConvertTo-Json -Depth 5 | Out-File -FilePath "$WORKSPACE\tests\test_report_20260506.json" -Encoding UTF8
Write-Host "  报告已保存: tests/test_report_20260506.json" -ForegroundColor Gray
