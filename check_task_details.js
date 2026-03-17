// 详细检查任务状态和参数
// 发票ID: c2f45a11-3bdd-4766-9fb3-dc09f932ac4e

(async function() {
    const invoiceId = "c2f45a11-3bdd-4766-9fb3-dc09f932ac4e";
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    console.log('='.repeat(80));
    console.log('任务详细诊断');
    console.log('='.repeat(80));
    console.log(`发票ID: ${invoiceId}`);
    console.log();
    
    try {
        // 获取任务列表
        const tasksResponse = await fetch(`${baseUrl}/api/v1/invoices/recognition-tasks?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!tasksResponse.ok) {
            console.error(`❌ 获取任务列表失败: HTTP ${tasksResponse.status}`);
            return;
        }
        
        const tasksData = await tasksResponse.json();
        const tasks = tasksData.data?.filter(task => task.invoice_id === invoiceId) || [];
        
        console.log(`找到 ${tasks.length} 个任务`);
        console.log();
        
        for (let i = 0; i < tasks.length; i++) {
            const task = tasks[i];
            console.log('='.repeat(80));
            console.log(`任务 ${i + 1}/${tasks.length}: ${task.task_no || task.id}`);
            console.log('='.repeat(80));
            console.log(`任务ID: ${task.id}`);
            console.log(`状态: ${task.status}`);
            console.log(`创建时间: ${task.create_time}`);
            console.log(`开始时间: ${task.start_time || '❌ 未启动'}`);
            console.log(`结束时间: ${task.end_time || 'N/A'}`);
            console.log(`Request ID: ${task.request_id || '❌ 未调用 Dify API'}`);
            console.log(`Trace ID: ${task.trace_id || 'N/A'}`);
            console.log(`错误代码: ${task.error_code || 'N/A'}`);
            console.log(`错误消息: ${task.error_message || 'N/A'}`);
            console.log();
            
            // 检查任务参数
            console.log('任务参数:');
            const params = task.params || {};
            console.log(JSON.stringify(params, null, 2));
            console.log();
            
            // 检查关键参数
            console.log('关键参数检查:');
            const modelConfigId = params.model_config_id;
            const templateId = params.template_id || task.template_id;
            const templatePrompt = params.template_prompt;
            const recognitionMode = params.recognition_mode;
            
            if (modelConfigId) {
                console.log(`  ✅ 模型配置ID: ${modelConfigId}`);
                
                // 尝试获取模型配置详情
                try {
                    const configsResponse = await fetch(`${baseUrl}/api/v1/config/llm/list`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (configsResponse.ok) {
                        const configsData = await configsResponse.json();
                        const config = configsData.data?.find(c => c.id === modelConfigId);
                        if (config) {
                            console.log(`  ✅ 模型配置名称: ${config.name}`);
                            console.log(`  ✅ API端点: ${config.endpoint}`);
                            console.log(`  ✅ 应用类型: ${config.app_type}`);
                            console.log(`  ✅ 工作流ID: ${config.workflow_id || 'N/A'}`);
                            console.log(`  ✅ 应用ID: ${config.app_id || 'N/A'}`);
                            console.log(`  ✅ 是否启用: ${config.is_active}`);
                            console.log(`  ✅ 是否默认: ${config.is_default}`);
                            
                            // 检查配置问题
                            const issues = [];
                            if (!config.endpoint) issues.push('API端点地址为空');
                            if (!config.api_key) issues.push('API密钥为空');
                            if (config.app_type === 'workflow' && !config.workflow_id) issues.push('工作流类型但未设置 workflow_id');
                            if (config.app_type === 'chat' && !config.app_id) issues.push('对话类型但未设置 app_id');
                            if (!config.is_active) issues.push('配置未启用');
                            
                            if (issues.length > 0) {
                                console.log(`  ⚠️  配置问题:`);
                                issues.forEach(issue => console.log(`     - ${issue}`));
                            }
                        } else {
                            console.log(`  ❌ 模型配置不存在: ${modelConfigId}`);
                        }
                    }
                } catch (e) {
                    console.log(`  ⚠️  无法获取模型配置详情: ${e.message}`);
                }
            } else {
                console.log(`  ❌ 模型配置ID未设置`);
            }
            
            if (templateId) {
                console.log(`  ✅ 模板ID: ${templateId}`);
            } else {
                console.log(`  ⚠️  模板ID未设置`);
            }
            
            if (templatePrompt) {
                const promptStr = String(templatePrompt);
                console.log(`  ✅ 提示词已设置，长度: ${promptStr.length} 字符`);
                console.log(`  ✅ 提示词预览: ${promptStr.substring(0, 150)}...`);
            } else {
                console.log(`  ⚠️  提示词未设置`);
            }
            
            if (recognitionMode) {
                console.log(`  ✅ 识别模式: ${recognitionMode}`);
            } else {
                console.log(`  ⚠️  识别模式未设置`);
            }
            console.log();
            
            // 诊断 pending 状态的原因
            if (task.status === 'pending') {
                console.log('Pending 状态诊断:');
                
                if (!task.start_time) {
                    console.log('  ❌ 任务未启动（没有 start_time）');
                    console.log('  💡 建议: 调用 /api/v1/invoices/recognition-tasks/{task_id}/start 启动任务');
                    console.log(`  💡 启动命令: POST ${baseUrl}/api/v1/invoices/recognition-tasks/${task.id}/start`);
                } else {
                    console.log('  ✅ 任务已启动');
                    
                    if (!task.request_id) {
                        console.log('  ❌ Dify API 未调用（没有 request_id）');
                        console.log('  💡 可能原因:');
                        console.log('     1. 任务启动后调用 Dify API 失败');
                        console.log('     2. 检查后端日志查看详细错误');
                        console.log('     3. 检查模型配置是否正确');
                    } else {
                        console.log('  ✅ Dify API 已调用');
                    }
                }
                console.log();
            }
            
            // 如果是 failed 状态，显示错误信息
            if (task.status === 'failed') {
                console.log('失败状态分析:');
                console.log(`  错误代码: ${task.error_code || 'N/A'}`);
                console.log(`  错误消息: ${task.error_message || 'N/A'}`);
                console.log();
            }
        }
        
        console.log('='.repeat(80));
        console.log('诊断完成');
        console.log('='.repeat(80));
        console.log();
        console.log('💡 下一步操作:');
        console.log('   1. 如果任务未启动，需要调用启动接口');
        console.log('   2. 如果任务已启动但未调用 Dify API，检查后端日志');
        console.log('   3. 如果配置有问题，修复配置后重新创建任务');
        
    } catch (error) {
        console.error('❌ 诊断失败:', error);
        console.error('错误详情:', error.stack);
    }
})();

