// 检查最新创建的任务，验证修复是否生效
// 在浏览器控制台运行

const token = localStorage.getItem('access_token');

(async function() {
    console.log('=== 检查最新任务 ===\n');
    
    const res = await fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=10', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    const tasks = data.data || [];
    
    if (tasks.length === 0) {
        console.log('没有找到任务');
        return;
    }
    
    // 按创建时间排序，最新的在前
    tasks.sort((a, b) => new Date(b.create_time) - new Date(a.create_time));
    
    console.log(`找到 ${tasks.length} 个任务，显示最新的3个:\n`);
    
    tasks.slice(0, 3).forEach((task, i) => {
        console.log(`任务 ${i + 1}: ${task.task_no}`);
        console.log(`  创建时间: ${task.create_time}`);
        console.log(`  状态: ${task.status}`);
        console.log(`  模型: ${task.model_name || 'N/A'}`);
        console.log(`  模板ID (任务字段): ${task.template_id || 'null'}`);
        console.log(`  模板ID (params中): ${task.params?.template_id || 'N/A'}`);
        console.log(`  模板策略: ${task.params?.template_strategy || 'N/A'}`);
        console.log(`  提示词: ${task.params?.template_prompt ? '✓ 存在 (' + task.params.template_prompt.length + '字符)' : '✗ 不存在'}`);
        
        // 检查修复是否生效
        const isFixed = task.template_id !== null && task.template_id !== undefined;
        const hasPrompt = !!task.params?.template_prompt;
        
        if (isFixed && hasPrompt) {
            console.log(`  ✅ 修复生效：template_id 和 template_prompt 都已正确保存`);
        } else if (isFixed && !hasPrompt) {
            console.log(`  ⚠ 部分修复：template_id 已保存，但 template_prompt 不存在`);
            console.log(`     提示：处理任务时会从模板获取 prompt`);
        } else if (!isFixed && hasPrompt) {
            console.log(`  ⚠ 部分修复：template_prompt 已保存，但 template_id 为 null`);
        } else {
            console.log(`  ❌ 修复未生效：template_id 和 template_prompt 都未保存`);
            console.log(`     提示：请确认后端服务已重启`);
        }
        
        console.log('');
    });
    
    // 检查是否有处理中的任务
    const processingTasks = tasks.filter(t => t.status === 'processing');
    if (processingTasks.length > 0) {
        console.log(`\n处理中的任务 (${processingTasks.length}个):`);
        processingTasks.forEach(task => {
            const elapsed = task.start_time ? 
                Math.round((new Date() - new Date(task.start_time)) / 1000) : 0;
            console.log(`  - ${task.task_no}: 已处理 ${elapsed} 秒`);
        });
    }
})();

