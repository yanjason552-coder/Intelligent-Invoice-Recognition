# PowerShell 测试脚本说明

## 问题修复说明

所有测试脚本已经修复，完全移除了 `&` 字符，使用 `[char]38` 来生成分隔符。

## 可用脚本

1. **test_final.ps1** - 最简版本（推荐）
   - 最小化代码
   - 完全避免特殊字符
   - 包含基本错误处理

2. **test_api_v2.ps1** - 简化版本
   - 包含更多测试步骤
   - 使用函数封装

3. **test_api.ps1** - 完整版本
   - 包含完整日志记录
   - 包含所有测试步骤

4. **diagnose.ps1** - 诊断脚本
   - 检查 PowerShell 环境
   - 验证脚本文件
   - 测试解析功能

## 使用方法

```powershell
cd backend

# 运行最简版本（推荐）
.\test_final.ps1

# 或运行简化版本
.\test_api_v2.ps1

# 或运行完整版本
.\test_api.ps1

# 运行诊断脚本
.\diagnose.ps1
```

## 如果仍然遇到错误

1. 检查 PowerShell 版本：`$PSVersionTable.PSVersion`
2. 运行诊断脚本：`.\diagnose.ps1`
3. 检查文件编码：确保文件是 UTF-8 编码
4. 提供完整的错误信息（包括行号和错误消息）

## 技术细节

所有脚本使用以下方法避免 `&` 字符：
- 使用 `[char]38` 生成 `&` 字符
- 使用哈希表让 PowerShell 自动处理表单编码
- 使用变量存储分隔符字符


