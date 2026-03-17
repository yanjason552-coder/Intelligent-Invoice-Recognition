// 检查任务状态和详细信息
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
    
    console.log('任务状态:');
    console.log(`  状态: ${task.status}`);
    console.log(`  创建时间: ${task.create_time}`);
    console.log(`  开始时间: ${task.start_time || 'N/A'}`);
    console.log(`  结束时间: ${task.end_time || 'N/A'}`);
    
    if (task.start_time) {
        const startTime = new Date(task.start_time);
        const elapsed = Math.round((new Date() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        console.log(`  已处理时间: ${minutes}分${seconds}秒`);
        
        if (elapsed > 300) {
            console.log(`\n⚠ 任务处理时间超过5分钟，可能存在问题`);
            console.log(`建议检查后端日志或联系管理员`);
        }
    }
    
    console.log(`\n任务配置:`);
    console.log(`  模型: ${task.model_name}`);
    console.log(`  模板ID (任务字段): ${task.template_id || 'N/A'}`);
    console.log(`  模板ID (params中): ${task.params?.template_id || 'N/A'}`);
    console.log(`  模板策略: ${task.params?.template_strategy || 'N/A'}`);
    console.log(`  提示词: ${task.params?.template_prompt ? '✓ 存在 (' + task.params.template_prompt.length + '字符)' : '✗ 不存在'}`);
    
    console.log(`\n问题分析:`);
    if (!task.template_id) {
        console.log(`  ❌ 任务的 template_id 字段为 null（应该在创建时保存）`);
    }
    if (!task.params?.template_prompt) {
        console.log(`  ❌ 任务的 params 中没有 template_prompt（应该在创建时从模板获取）`);
        console.log(`  模板实际有 prompt（787字符），但创建任务时没有获取到`);
    }
    
    console.log(`\n建议:`);
    console.log(`  1. 检查后端日志，查看任务创建时的错误信息`);
    console.log(`  2. 如果任务失败，重新创建任务（修复后的代码应该能正确工作）`);
    console.log(`  3. 如果任务成功但没有使用模板，可以重新创建任务`);
    
    // 检查是否有错误信息
    if (task.params?.error_message) {
        console.log(`\n错误信息: ${task.params.error_message}`);
    }
})();

