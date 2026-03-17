// 检查任务详细参数
// 在浏览器控制台运行

const taskId = "TASK-20260128110745-ee3a2a5b"; // 替换为实际任务ID
const token = localStorage.getItem('access_token');

(async function() {
    console.log('=== 检查任务详情 ===');
    console.log(`任务编号: ${taskId}\n`);
    
    // 查询任务列表
    const res = await fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=100', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    const task = data.data.find(t => t.task_no === taskId);
    
    if (!task) {
        console.log('未找到任务');
        return;
    }
    
    console.log('任务详情:');
    console.log(`  任务ID: ${task.id}`);
    console.log(`  状态: ${task.status}`);
    console.log(`  模型: ${task.model_name}`);
    console.log(`  模板ID: ${task.template_id || 'N/A'}`);
    console.log(`  创建时间: ${task.create_time}`);
    console.log(`  开始时间: ${task.start_time || 'N/A'}`);
    console.log(`  结束时间: ${task.end_time || 'N/A'}`);
    
    console.log('\n任务参数 (params):');
    console.log(JSON.stringify(task.params, null, 2));
    
    console.log('\n关键参数检查:');
    console.log(`  model_config_id: ${task.params?.model_config_id || 'N/A'}`);
    console.log(`  template_id: ${task.params?.template_id || 'N/A'}`);
    console.log(`  template_strategy: ${task.params?.template_strategy || 'N/A'}`);
    console.log(`  template_prompt: ${task.params?.template_prompt ? '✓ 存在 (' + task.params.template_prompt.length + '字符)' : '✗ 不存在'}`);
    console.log(`  recognition_mode: ${task.params?.recognition_mode || 'N/A'}`);
    
    // 如果模板ID存在，查询模板详情
    if (task.params?.template_id) {
        console.log('\n查询模板详情...');
        try {
            const templateRes = await fetch(`http://localhost:8000/api/v1/templates/${task.params.template_id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (templateRes.ok) {
                const template = await templateRes.json();
                console.log(`  模板名称: ${template.name}`);
                console.log(`  模板类型: ${template.template_type}`);
                console.log(`  模板状态: ${template.status}`);
                console.log(`  模板提示词: ${template.prompt ? '✓ 存在 (' + template.prompt.length + '字符)' : '✗ 不存在'}`);
            }
        } catch (e) {
            console.log('  无法获取模板详情:', e.message);
        }
    }
    
    // 检查任务是否卡住
    if (task.status === 'processing' && task.start_time) {
        const startTime = new Date(task.start_time);
        const elapsed = Math.round((new Date() - startTime) / 1000);
        console.log(`\n任务已处理: ${elapsed} 秒 (${Math.round(elapsed / 60)} 分钟)`);
        
        if (elapsed > 300) { // 超过5分钟
            console.log('⚠ 任务处理时间较长，可能需要检查后端日志');
        }
    }
})();
