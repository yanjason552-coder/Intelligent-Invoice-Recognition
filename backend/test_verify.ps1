# 验证脚本 - 测试 PowerShell 是否能正确解析
Write-Host "Verification script started" -ForegroundColor Green

# 测试字符代码
$charCode = 38
$testChar = [char]$charCode
Write-Host "Character code $charCode = '$testChar'" -ForegroundColor Yellow

# 测试字符串拼接
$part1 = "skip=0"
$part2 = "limit=10"
$result = $part1 + $testChar + $part2
Write-Host "Query string: $result" -ForegroundColor Cyan

# 测试哈希表
$testHash = @{
    key1 = "value1"
    key2 = "value2"
}
Write-Host "Hashtable test: $($testHash.Count) items" -ForegroundColor Yellow

Write-Host "Verification script completed successfully" -ForegroundColor Green


