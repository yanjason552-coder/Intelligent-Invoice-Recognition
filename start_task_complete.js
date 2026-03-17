// 完整版：启动任务并检查结果
// 发票ID: c2f45a11-3bdd-4766-9fb3-dc09f932ac4e

(async function() {
    const invoiceId = "c2f45a11-3bdd-4766-9fb3-dc09f932ac4e";
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    console.log('='.repeat(80));
    console.log('启动识别任务（完整版）');
    console.log('='.repeat(80));
    console.log(`发票ID: ${invoiceId}`);
    console.log();
    
    try {
        // 1. 获取任务列表
        console.log('步骤1: 正在获取任务列表...');
        const tasksResponse = await fetch(`${baseUrl}/api/v1/invoices/recognition-tasks?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!tasksResponse.ok) {
            const errorText = await tasksResponse.text();
            console.error(`❌ 获取任务列表失败: HTTP ${tasksResponse.status}`);
            console.error(`错误信息: ${errorText}`);
            return;
        }
        
        const tasksData = await tasksResponse.json();
        const tasks = tasksData.data?.filter(task => 
            task.invoice_id === invoiceId && 
            task.status === 'pending'
        ) || [];
        
        console.log(`✅ 找到 ${tasks.length} 个 pending 状态的任务`);
        
        if (tasks.length === 0) {
            console.log('⚠️  没有需要启动的任务');
            return;
        }
        
        // 显示所有 pending 任务
        tasks.forEach((task, index) => {
            console.log(`   ${index + 1}. 任务ID: ${task.id}`);
            console.log(`      任务编号: ${task.task_no || 'N/A'}`);
            console.log(`      创建时间: ${task.create_time || 'N/A'}`);
        });
        console.log();
        
        // 2. 启动最新的任务
        const latestTask = tasks[0];
        console.log('步骤2: 正在启动任务...');
        console.log(`   任务ID: ${latestTask.id}`);
        console.log(`   任务编号: ${latestTask.task_no || 'N/A'}`);
        console.log();
        
        const startResponse = await fetch(`${baseUrl}/api/v1/invoices/recognition-tasks/${latestTask.id}/start`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`   响应状态: HTTP ${startResponse.status}`);
        
        if (!startResponse.ok) {
            const errorText = await startResponse.text();
            console.error(`❌ 启动任务失败: HTTP ${startResponse.status}`);
            console.error(`错误信息: ${errorText}`);
            
            // 尝试解析错误详情
            try {
                const errorJson = JSON.parse(errorText);
                if (errorJson.detail) {
                    console.error(`详细错误: ${errorJson.detail}`);
                }
            } catch (e) {
                console.error(`原始错误: ${errorText}`);
            }
            return;
        }
        
        const result = await startResponse.json();
        console.log('✅ 任务启动成功');
        console.log(`   响应消息: ${result.message || JSON.stringify(result)}`);
        console.log();
        
        // 3. 等待并检查任务状态
        console.log('步骤3: 等待 3 秒后检查任务状态...');
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        console.log('步骤4: 正在检查任务状态...');
        const checkResponse = await fetch(`${baseUrl}/api/v1/invoices/recognition-tasks?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (checkResponse.ok) {
            const checkData = await checkResponse.json();
            const updatedTask = checkData.data?.find(t => t.id === latestTask.id);
            
            if (updatedTask) {
                console.log('✅ 任务状态已更新:');
                console.log(`   状态: ${updatedTask.status}`);
                console.log(`   开始时间: ${updatedTask.start_time || 'N/A'}`);
                console.log(`   Request ID: ${updatedTask.request_id || 'N/A'}`);
                console.log(`   Trace ID: ${updatedTask.trace_id || 'N/A'}`);
                
                if (updatedTask.error_code) {
                    console.log(`   ❌ 错误代码: ${updatedTask.error_code}`);
                }
                if (updatedTask.error_message) {
                    console.log(`   ❌ 错误消息: ${updatedTask.error_message}`);
                }
                console.log();
                
                // 状态分析
                if (updatedTask.status === 'processing') {
                    console.log('📊 状态分析:');
                    console.log('   ✅ 任务正在处理中');
                    console.log('   💡 建议: 等待任务完成，或使用监控脚本查看进度');
                } else if (updatedTask.status === 'failed') {
                    console.log('📊 状态分析:');
                    console.log('   ❌ 任务失败');
                    console.log('   💡 建议: 查看错误信息并修复问题');
                    
                    // 错误分析
                    const errorCode = updatedTask.error_code?.toUpperCase() || '';
                    const errorMsg = updatedTask.error_message || '';
                    
                    if (errorCode.includes('TIMEOUT') || errorMsg.includes('超时') || errorMsg.includes('timeout')) {
                        console.log('   🔍 问题: 请求超时');
                        console.log('   💡 解决方案:');
                        console.log('      1. 检查网络连接');
                        console.log('      2. 检查 Dify API 端点地址');
                        console.log('      3. 增加超时时间配置');
                    } else if (errorCode.includes('CONNECT') || errorMsg.includes('连接') || errorMsg.includes('Connection')) {
                        console.log('   🔍 问题: 无法连接到 Dify API');
                        console.log('   💡 解决方案:');
                        console.log('      1. 检查 Dify API 端点地址是否正确');
                        console.log('      2. 检查网络连接');
                        console.log('      3. 检查防火墙设置');
                    } else if (errorCode.includes('AUTH') || errorMsg.includes('401') || errorMsg.includes('403')) {
                        console.log('   🔍 问题: 认证失败');
                        console.log('   💡 解决方案:');
                        console.log('      1. 检查 API 密钥是否正确');
                        console.log('      2. 重新配置 API 密钥');
                    }
                } else if (updatedTask.status === 'completed') {
                    console.log('📊 状态分析:');
                    console.log('   ✅ 任务已完成');
                } else if (updatedTask.status === 'pending') {
                    console.log('📊 状态分析:');
                    console.log('   ⚠️  任务仍为 pending 状态');
                    console.log('   💡 可能原因:');
                    console.log('      1. 任务启动后还未开始处理');
                    console.log('      2. 后端服务可能有问题');
                    console.log('      3. 检查后端日志');
                }
            } else {
                console.log('⚠️  未找到更新后的任务');
            }
        } else {
            console.error(`❌ 检查任务状态失败: HTTP ${checkResponse.status}`);
        }
        
        console.log();
        console.log('='.repeat(80));
        console.log('操作完成');
        console.log('='.repeat(80));
        
    } catch (error) {
        console.error('❌ 操作失败:', error);
        console.error('错误类型:', error.name);
        console.error('错误消息:', error.message);
        if (error.stack) {
            console.error('错误堆栈:', error.stack);
        }
    }
})();

