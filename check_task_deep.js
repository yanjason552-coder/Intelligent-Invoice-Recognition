// 深度检查任务状态和参数
// 发票ID: c2f45a11-3bdd-4766-9fb3-dc09f932ac4e

(async function() {
    const invoiceId = "c2f45a11-3bdd-4766-9fb3-dc09f932ac4e";
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    console.log('='.repeat(80));
    console.log('深度检查任务状态');
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
        
        // 检查 processing 状态的任务
        const processingTask = tasks.find(t => t.status === 'processing');
        
        if (processingTask) {
            console.log('='.repeat(80));
            console.log('Processing 任务详细分析:');
            console.log('='.repeat(80));
            console.log(`任务ID: ${processingTask.id}`);
            console.log(`任务编号: ${processingTask.task_no || 'N/A'}`);
            console.log(`状态: ${processingTask.status}`);
            console.log(`创建时间: ${processingTask.create_time}`);
            console.log(`开始时间: ${processingTask.start_time || 'N/A'}`);
            
            // 计算处理时长
            if (processingTask.start_time) {
                const startTime = new Date(processingTask.start_time);
                const now = new Date();
                const duration = Math.floor((now - startTime) / 1000);
                console.log(`处理时长: ${duration} 秒 (${Math.floor(duration / 60)} 分钟)`);
            }
            
            console.log(`Request ID: ${processingTask.request_id || '❌ 未调用 Dify API'}`);
            console.log(`Trace ID: ${processingTask.trace_id || 'N/A'}`);
            console.log(`错误代码: ${processingTask.error_code || 'N/A'}`);
            console.log(`错误消息: ${processingTask.error_message || 'N/A'}`);
            console.log();
            
            // 检查任务参数
            const params = processingTask.params || {};
            console.log('任务参数详情:');
            console.log(JSON.stringify(params, null, 2));
            console.log();
            
            // 检查关键参数
            const modelConfigId = params.model_config_id;
            const templateId = params.template_id || processingTask.template_id;
            const templatePrompt = params.template_prompt;
            
            console.log('关键参数检查:');
            if (modelConfigId) {
                console.log(`  ✅ 模型配置ID: ${modelConfigId}`);
                
                // 获取模型配置
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
                    console.log(`  ⚠️  无法获取模型配置: ${e.message}`);
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
                console.log(`  ✅ 提示词预览: ${promptStr.substring(0, 200)}...`);
            } else {
                console.log(`  ⚠️  提示词未设置`);
            }
            console.log();
            
            // 诊断
            console.log('诊断结果:');
            if (!processingTask.request_id) {
                console.log('  ❌ Dify API 尚未调用');
                console.log('  💡 可能原因:');
                console.log('     1. 任务刚启动，Dify API 调用还未开始');
                console.log('     2. Dify API 调用失败（检查后端日志）');
                console.log('     3. 任务参数有问题（如缺少 model_config_id、template_prompt 等）');
                console.log('     4. 模型配置有问题（如 endpoint、api_key、workflow_id 等）');
                console.log('     5. 文件上传到 Dify 失败');
                console.log();
                console.log('  🔍 建议:');
                console.log('     1. 查看后端日志获取详细错误信息');
                console.log('     2. 检查模型配置是否正确');
                console.log('     3. 检查任务参数是否完整');
                console.log('     4. 如果任务长时间处于 processing 状态，可能需要手动标记为失败');
            } else {
                console.log('  ✅ Dify API 已调用');
                console.log(`     Request ID: ${processingTask.request_id}`);
            }
        } else {
            console.log('⚠️  未找到 processing 状态的任务');
        }
        
        console.log();
        console.log('='.repeat(80));
        console.log('检查完成');
        console.log('='.repeat(80));
        
    } catch (error) {
        console.error('❌ 检查失败:', error);
        console.error('错误详情:', error.stack);
    }
})();

