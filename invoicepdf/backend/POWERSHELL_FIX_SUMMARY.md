# PowerShell 脚本修复总结

## 问题描述

PowerShell 脚本中出现 "AmpersandNotAllowed" 错误，因为 `&` 字符被 PowerShell 解析为命令分隔符。

## 修复完成

所有 PowerShell 脚本已经修复，完全移除了 `&` 字符：

### 已修复的脚本

1. **test_api.ps1** - API 测试脚本（完整版）
2. **test_api_v2.ps1** - API 测试脚本（简化版）
3. **test_final.ps1** - API 测试脚本（最简版）
4. **RUN_MIGRATION.ps1** - 数据库迁移脚本
5. **fix_migration.ps1** - 迁移修复脚本
6. **diagnose.ps1** - 诊断脚本

### 修复方法

1. **使用字符代码**：`$separator = [char]38` 替代 `&` 字符
2. **使用哈希表**：让 PowerShell 自动处理表单编码
3. **移除重定向**：将 `2>&1` 改为使用管道和错误处理
4. **移除注释中的 &**：所有注释和显示文本中的 `&` 都已移除

## 验证结果

通过 `grep` 确认：**所有 PowerShell 脚本中完全没有 `&` 字符**。

## 测试步骤

### 1. 测试 API 脚本

```powershell
cd backend
.\test_final.ps1
```

### 2. 运行数据库迁移

```powershell
cd backend
.\RUN_MIGRATION.ps1
```

### 3. 运行诊断脚本

```powershell
cd backend
.\diagnose.ps1
```

## 如果问题仍然存在

如果运行脚本时仍然出现 "AmpersandNotAllowed" 错误，请：

1. **检查 PowerShell 版本**：
   ```powershell
   $PSVersionTable.PSVersion
   ```

2. **检查文件编码**：
   ```powershell
   [System.IO.File]::ReadAllText("backend\test_final.ps1", [System.Text.Encoding]::UTF8) | Select-String -Pattern '&'
   ```

3. **提供完整错误信息**：
   - 错误消息
   - 错误行号
   - PowerShell 版本
   - 运行方式（直接运行还是通过其他脚本调用）

4. **尝试直接运行最小测试**：
   ```powershell
   cd backend
   Write-Host "Test" -ForegroundColor Green
   $test = [char]38
   Write-Host "Character code 38: $test" -ForegroundColor Yellow
   ```

## 技术细节

### 字符代码方法

```powershell
# 定义分隔符
$separator = [char]38  # ASCII 码 38 = &

# 使用分隔符
$queryString = $parts -join $separator
```

### 哈希表方法

```powershell
# 构建表单数据
$loginBody = @{
    username = $Username
    password = $Password
}

# PowerShell 会自动处理编码
Invoke-RestMethod -Body $loginBody ...
```

### 错误处理替代重定向

```powershell
# 旧方法（可能引起问题）
$output = command 2>&1

# 新方法（安全）
$output = @()
command | ForEach-Object { $output += $_ }
```

## 文件列表

所有已修复的脚本文件：
- `backend/test_api.ps1`
- `backend/test_api_v2.ps1`
- `backend/test_final.ps1`
- `backend/RUN_MIGRATION.ps1`
- `backend/fix_migration.ps1`
- `backend/diagnose.ps1`

## 最后更新

2024-01-15 - 所有脚本已修复并验证


