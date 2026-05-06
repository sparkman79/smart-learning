# 智能学习系统 - 快速验证脚本

## 验证检查项

### 1. 目录结构检查
```powershell
# 检查所有必需目录是否存在
$dirs = @(
    "data/homework/inbox",
    "data/homework/parsed",
    "data/homework/done",
    "data/reports/daily",
    "data/reports/weekly",
    "data/reports/trends",
    "data/members/kid_1",
    "data/members/parent_1",
    "data/members/admin_1",
    "data/family/shared"
)

$base = "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning"
$all_ok = $true

foreach ($dir in $dirs) {
    $path = Join-Path $base $dir
    if (Test-Path $path) {
        Write-Host "✅ $dir" -ForegroundColor Green
    } else {
        Write-Host "❌ $dir" -ForegroundColor Red
        $all_ok = $false
    }
}
```

### 2. 配置文件验证
```powershell
# 验证 JSON 文件语法
$json_files = @(
    "data/family/members/index.json",
    "data/routines/state.json",
    "data/routines/policies.json",
    "data/routines/plans/standard.json"
)

foreach ($file in $json_files) {
    $path = Join-Path $base $file
    try {
        $content = Get-Content $path -Raw | ConvertFrom-Json
        Write-Host "✅ $file (语法正确)" -ForegroundColor Green
    } catch {
        Write-Host "❌ $file (语法错误): $_" -ForegroundColor Red
    }
}
```

### 3. Skill 文件完整性
```powershell
$skills = @(
    "homework-intake",
    "study-mode",
    "study-ack",
    "study-escalation",
    "daily-report",
    "weekly-report",
    "plan-builder",
    "member-registry"
)

foreach ($skill in $skills) {
    $path = Join-Path $base "skills/$skill/SKILL.md"
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "✅ $skill/SKILL.md ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "❌ $skill/SKILL.md 缺失" -ForegroundColor Red
    }
}
```

### 4. 测试数据验证
```powershell
# 验证测试数据文件
$test_files = @(
    "data/homework/inbox/kid_1_20260505_220000.txt",
    "data/homework/parsed/kid_1_20260505_220000_parsed.json",
    "data/reports/trends/trends.csv"
)

foreach ($file in $test_files) {
    $path = Join-Path $base $file
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "✅ $file ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "❌ $file 缺失" -ForegroundColor Red
    }
}
```

### 5. 定时任务验证
```powershell
# 验证 cron 配置
$cron_file = "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\cron\jobs.json"
try {
    $jobs = Get-Content $cron_file -Raw | ConvertFrom-Json
    $study_jobs = $jobs.jobs | Where-Object { $_.id -like "study_*" -or $_.id -like "*learning*" }
    Write-Host "✅ 学习相关定时任务: $($study_jobs.Count) 个" -ForegroundColor Green
    $study_jobs | ForEach-Object {
        Write-Host "  - $($_.id) ($($_.schedule))" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ cron 配置读取失败: $_" -ForegroundColor Red
}
```

## 完整验证命令（一键执行）

```powershell
# 在 smart_learning 目录下执行
cd "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning"
.\verify.ps1
```
