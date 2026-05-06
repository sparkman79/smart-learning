# Phase 4: 端到端测试验证

## 测试数据准备

### 1. 模拟作业输入测试 (homework-intake)

在 `data/homework/inbox/` 创建测试文件：

```
测试文件：kid_1_20260505_220000.txt
内容：明天语文作业：1.背诵《静夜思》 2.写生字"月"10 遍 3.数学口算题 20 道
```

预期输出：
- 文件被 `homework-intake` Skill 处理
- 生成 `data/homework/parsed/kid_1_20260505_220000_parsed.json`
- 双视图输出正确

### 2. 测试学习模式切换 (study-mode)

执行流程：
```
用户发送：/开始学习
```

预期结果：
- `state.json` 的 `mode` 更新为 `study`
- `current_member_id` 设为 `kid_1`
- `session.started_at` 记录当前时间

### 3. 测试确认机制 (study-ack)

执行流程：
```
用户发送：/已准备好
```

预期结果：
- `state.json` 的 `session.ack_start` 更新
- 升级提醒停止

### 4. 测试日报生成 (daily-report)

手动触发：
```
执行 daily-report Skill
```

预期结果：
- `data/reports/daily/report_20260505.txt` 生成
- `data/reports/trends/trends.csv` 追加记录

---

## 快速测试命令

### 测试 1: 检查目录结构
```powershell
Get-ChildItem -Path "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning" -Recurse | Select-Object FullName, Length
```

### 测试 2: 检查状态机
```powershell
Get-Content "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning\data\routines\state.json"
```

### 测试 3: 检查成员配置
```powershell
Get-Content "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning\data\family\members\index.json"
```

### 测试 4: 检查策略配置
```powershell
Get-Content "C:\Users\Administrator\AppData\Roaming\winclaw\.openclaw\workspace\smart_learning\data\routines\policies.json"
```

---

## 端到端流程测试

### 完整流程模拟

1. **家长发送作业**
   ```
   家长：帮我记录明天作业：语文背诵《静夜思》，数学口算 20 道
   ```
   → homework-intake 处理，生成 parsed 文件

2. **开始学习**
   ```
   孩子：/开始学习
   ```
   → study-mode 触发，state.json 更新

3. **确认准备**
   ```
   孩子：/已准备好
   ```
   → study-ack 处理，升级停止

4. **结束学习**
   ```
   孩子：/结束学习
   ```
   → daily-report 生成日报

---

## 验证清单

- [ ] `data/homework/inbox/` 目录存在
- [ ] `data/homework/parsed/` 目录存在
- [ ] `data/homework/done/` 目录存在
- [ ] `data/reports/daily/` 目录存在
- [ ] `data/reports/weekly/` 目录存在
- [ ] `data/family/members/index.json` 配置正确
- [ ] `data/routines/state.json` 初始状态正确
- [ ] `data/routines/policies.json` 策略配置正确
- [ ] 8 个 Skill 的 `SKILL.md` 文件完整
- [ ] `cron/jobs.json` 包含新增的 2 个任务
- [ ] 所有文件路径可访问

---

## 预期结果

### 成功标准
1. ✅ 所有目录和文件创建成功
2. ✅ JSON 配置文件语法正确
3. ✅ Skill 脚本可执行
4. ✅ 定时任务配置生效
5. ✅ 端到端流程可完整运行

### 异常处理
1. ❌ 如果 homework-intake 无法处理文件 → 检查 SKILL.md 配置
2. ❌ 如果 study-mode 无法更新 state.json → 检查权限
3. ❌ 如果 daily-report 无法生成 → 检查目录权限

---

## 下一步

测试完成后，根据结果：
- 全部通过 → 进入 Phase 5: 部署上线
- 部分失败 → 修复问题后重新测试
- 全部失败 → 返回 Phase 1 重新检查
