// 在浏览器控制台运行此代码来检查任务详情和模型配置
// 获取token
const token = localStorage.getItem('access_token');

console.log('=== 开始检查任务和模型配置 ===\n');

// 1. 查询所有模型配置
fetch('http://localhost:8000/api/v1/config/llm/list', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
})
.then(r => r.json())
.then(result => {
    const modelConfigs = result.data || [];
    console.log('【模型配置列表】');
    if (modelConfigs && modelConfigs.length > 0) {
        modelConfigs.forEach((config, i) => {
            console.log(`${i + 1}. ${config.name} (ID: ${config.id})`);
            console.log(`   状态: ${config.status}`);
            console.log(`   提供商: ${config.provider}`);
            if (config.name.includes('v3_JsonSchema') || config.name.includes('JsonSchema')) {
                console.log('   ⭐ 这是 v3_JsonSchema 模型');
            }
        });
        
        // 查找 v3_JsonSchema
        const v3Model = modelConfigs.find(c => 
            c.name.includes('v3_JsonSchema') || 
            c.name.includes('JsonSchema') ||
            c.name.toLowerCase().includes('v3') && c.name.toLowerCase().includes('json')
        );
        
        if (v3Model) {
            console.log(`\n✓ 找到 v3_JsonSchema 模型:`);
            console.log(`  名称: ${v3Model.name}`);
            console.log(`  ID: ${v3Model.id}`);
            console.log(`  状态: ${v3Model.status}`);
        } else {
            console.log('\n⚠ 未找到 v3_JsonSchema 模型，请检查模型名称');
        }
    } else {
        console.log('未找到模型配置');
    }
    
    console.log('\n');
    
    // 2. 查询识别任务列表（只查询处理中的任务）
    return fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?status=processing&limit=10', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
})
.then(r => r.json())
.then(tasksData => {
    console.log('【处理中的任务详情】');
    
    if (tasksData && tasksData.data && tasksData.data.length > 0) {
        tasksData.data.forEach((task, index) => {
            console.log(`\n任务 ${index + 1}:`);
            console.log('  任务编号:', task.task_no);
            console.log('  任务ID:', task.id);
            console.log('  状态:', task.status);
            console.log('  创建时间:', task.create_time);
            console.log('  开始时间:', task.start_time || '未开始');
            console.log('  结束时间:', task.end_time || '未结束');
            console.log('  识别模式:', task.recognition_mode || 'N/A');
            console.log('  使用的模型:', task.model_name || 'N/A');
            console.log('  模型配置ID:', task.params?.model_config_id || 'N/A');
            console.log('  模板ID:', task.template_id || 'N/A');
            console.log('  模板策略:', task.params?.template_strategy || 'N/A');
            console.log('  是否包含提示词:', !!task.params?.template_prompt);
            
            if (task.params?.template_prompt) {
                console.log('  ✓ 提示词长度:', task.params.template_prompt.length, '字符');
                console.log('  提示词内容（前200字符）:', task.params.template_prompt.substring(0, 200));
            } else {
                console.log('  ✗ 未包含提示词');
            }
            
            // 检查是否使用了 v3_JsonSchema
            if (task.model_name && (
                task.model_name.includes('v3_JsonSchema') || 
                task.model_name.includes('JsonSchema') ||
                (task.model_name.toLowerCase().includes('v3') && task.model_name.toLowerCase().includes('json'))
            )) {
                console.log('  ⭐ 使用的是 v3_JsonSchema 模型');
            } else {
                console.log('  ⚠ 未使用 v3_JsonSchema 模型');
                console.log('  当前使用的模型:', task.model_name || '未知');
            }
            
            // 显示所有参数键
            if (task.params) {
                console.log('  参数键列表:', Object.keys(task.params));
            }
        });
    } else {
        console.log('没有处理中的任务');
    }
    
    console.log('\n');
    
    // 3. 查询所有任务（包括已完成和失败的）
    return fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=5', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
})
.then(r => r.json())
.then(allTasksData => {
    console.log('【最近的任务（所有状态）】');
    
    if (allTasksData && allTasksData.data && allTasksData.data.length > 0) {
        allTasksData.data.forEach((task, index) => {
            console.log(`\n任务 ${index + 1}: ${task.task_no}`);
            console.log('  状态:', task.status);
            console.log('  模型:', task.model_name || 'N/A');
            console.log('  创建时间:', task.create_time);
            if (task.params?.template_prompt) {
                console.log('  ✓ 包含提示词');
            }
        });
    }
    
    console.log('\n=== 检查完成 ===');
})
.catch(err => {
    console.error('查询失败:', err);
});

