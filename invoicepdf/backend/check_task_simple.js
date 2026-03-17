// 简化版：在浏览器控制台直接运行
// 复制以下代码到浏览器控制台（Console）运行

const token = localStorage.getItem('access_token');

// 查询模型配置
fetch('http://localhost:8000/api/v1/config/llm/list', {
    headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(result => {
    const configs = result.data || [];
    console.log('=== 模型配置列表 ===');
    configs.forEach(c => {
        const isV3 = c.name.includes('v3_JsonSchema') || c.name.includes('JsonSchema') || 
                     (c.name.toLowerCase().includes('v3') && c.name.toLowerCase().includes('json'));
        console.log(`${isV3 ? '⭐' : '  '} ${c.name} (ID: ${c.id})`);
        if (isV3) console.log(`     状态: ${c.status}, 类型: ${c.app_type}`);
    });
    
    // 查询处理中的任务
    return fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?status=processing&limit=10', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
})
.then(r => r.json())
.then(data => {
    const tasks = data.data || [];
    console.log('\n=== 处理中的任务 ===');
    if (tasks.length === 0) {
        console.log('没有处理中的任务');
    } else {
        tasks.forEach((task, i) => {
            console.log(`\n任务 ${i + 1}: ${task.task_no}`);
            console.log(`  状态: ${task.status}`);
            console.log(`  模型: ${task.model_name || 'N/A'}`);
            console.log(`  模型配置ID: ${task.params?.model_config_id || 'N/A'}`);
            console.log(`  模板ID: ${task.template_id || 'N/A'}`);
            console.log(`  模板策略: ${task.params?.template_strategy || 'N/A'}`);
            console.log(`  包含提示词: ${task.params?.template_prompt ? '✓ 是 (' + task.params.template_prompt.length + '字符)' : '✗ 否'}`);
            
            const isV3 = task.model_name && (
                task.model_name.includes('v3_JsonSchema') || 
                task.model_name.includes('JsonSchema') ||
                (task.model_name.toLowerCase().includes('v3') && task.model_name.toLowerCase().includes('json'))
            );
            console.log(`  使用v3_JsonSchema: ${isV3 ? '⭐ 是' : '⚠ 否'}`);
        });
    }
})
.catch(err => console.error('错误:', err));

