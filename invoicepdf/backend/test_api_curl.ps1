# PowerShell脚本：使用curl测试API
# 使用方法：修改下面的 $token 变量为你的实际token

$token = "YOUR_TOKEN_HERE"  # 替换为你的实际token

# 测试识别情况API
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/statistics/recognition-status" `
        -Method Get `
        -Headers $headers
    
    Write-Host "========== 识别情况报告 ==========" -ForegroundColor Green
    Write-Host ""
    Write-Host "【任务状态】" -ForegroundColor Yellow
    Write-Host "  待处理: $($response.task_status.pending)"
    Write-Host "  处理中: $($response.task_status.processing)"
    Write-Host "  已完成: $($response.task_status.completed)"
    Write-Host "  失败: $($response.task_status.failed)"
    Write-Host "  总计: $($response.task_status.total)"
    Write-Host ""
    
    Write-Host "【长时间处理中的任务】" -ForegroundColor Yellow
    if ($response.stuck_tasks.Count -gt 0) {
        Write-Host "  共 $($response.stuck_tasks.Count) 个任务"
        $response.stuck_tasks | Select-Object -First 5 | ForEach-Object {
            Write-Host "  - $($_.task_no): 已处理 $($_.duration_minutes) 分钟"
        }
    } else {
        Write-Host "  [OK] 没有长时间处理中的任务"
    }
    Write-Host ""
    
    Write-Host "【最近失败的任务】" -ForegroundColor Yellow
    if ($response.failed_tasks.Count -gt 0) {
        Write-Host "  共 $($response.failed_tasks.Count) 个任务"
        $response.failed_tasks | Select-Object -First 5 | ForEach-Object {
            Write-Host "  - $($_.task_no): $($_.error_code)"
        }
    } else {
        Write-Host "  [OK] 没有失败的任务"
    }
    Write-Host ""
    
    Write-Host "【识别结果统计】" -ForegroundColor Yellow
    Write-Host "  结果总数: $($response.result_status.total)"
    Write-Host "  成功: $($response.result_status.success)"
    Write-Host "  失败: $($response.result_status.failed)"
    Write-Host "  部分成功: $($response.result_status.partial)"
    if ($response.result_status.avg_accuracy) {
        Write-Host "  平均准确率: $([math]::Round($response.result_status.avg_accuracy * 100, 2))%"
    }
    Write-Host ""
    
    Write-Host "【模板提示词使用情况】" -ForegroundColor Yellow
    Write-Host "  使用提示词的任务数: $($response.prompt_usage.tasks_with_prompt)"
    Write-Host "  总任务数: $($response.prompt_usage.total_tasks)"
    if ($response.prompt_usage.usage_rate) {
        Write-Host "  使用率: $([math]::Round($response.prompt_usage.usage_rate * 100, 2))%"
    }
    Write-Host ""
    
    Write-Host "===================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "完整JSON数据:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "错误: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "响应内容: $responseBody" -ForegroundColor Red
    }
}

