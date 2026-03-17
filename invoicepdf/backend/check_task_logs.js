// 检查任务详细状态和可能的错误
// 在浏览器控制台运行

const taskId = "TASK-20260128110745-ee3a2a5b";
const token = localStorage.getItem('access_token');

(async function() {
    console.log('=== 检查任务状态 ===');
    console.log(`任务编号: ${taskId}\n`);
    
    const res = await fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=100', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    const task = data.data.find(t => t.task_no === taskId);
    
    if (!task) {
        console.log('未找到任务');
        return;
    }
    
    const startTime = task.start_time ? new Date(task.start_time) : null;
    const now = new Date();
    const elapsed = startTime ? Math.round((now - startTime) / 1000) : 0;
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    console.log('任务信息:');
    console.log(`  状态: ${task.status}`);
    console.log(`  创建时间: ${task.create_time}`);
    console.log(`  开始时间: ${task.start_time || 'N/A'}`);
    console.log(`  已处理时间: ${minutes}分${seconds}秒`);
    
    console.log(`\n配置信息:`);
    console.log(`  模型: ${task.model_name}`);
    console.log(`  模板ID (任务字段): ${task.template_id || 'N/A'}`);
    console.log(`  模板ID (params中): ${task.params?.template_id || 'N/A'}`);
    console.log(`  提示词: ${task.params?.template_prompt ? '✓ 存在 (' + task.params.template_prompt.length + '字符)' : '✗ 不存在'}`);
    
    console.log(`\n分析:`);
    if (elapsed > 600) {
        console.log(`  ⚠ 任务已处理超过10分钟，可能存在问题`);
        console.log(`  建议:`);
        console.log(`    1. 检查后端日志，查看是否有错误或超时`);
        console.log(`    2. 检查 DIFY API 是否正常响应`);
        console.log(`    3. 如果任务卡住，可以考虑取消并重新创建`);
    } else if (elapsed > 300) {
        console.log(`  ⚠ 任务已处理超过5分钟，可能较慢但仍在处理中`);
    } else {
        console.log(`  ✓ 任务正在正常处理中`);
    }
    
    // 检查是否有错误信息
    if (task.params?.error_message) {
        console.log(`\n错误信息: ${task.params.error_message}`);
    }
    if (task.error_message) {
        console.log(`\n任务错误: ${task.error_message}`);
    }
    if (task.error_code) {
        console.log(`\n错误代码: ${task.error_code}`);
    }
    
    console.log(`\n建议操作:`);
    console.log(`  1. 查看后端控制台日志，查找任务相关的日志`);
    console.log(`  2. 如果看到 "从模板对象获取到模板提示词" 的日志，说明修复生效`);
    console.log(`  3. 如果任务继续卡住，可以等待或取消后重新创建`);
})();

