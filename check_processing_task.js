// 检查 processing 状态的任务
// 发票ID: c2f45a11-3bdd-4766-9fb3-dc09f932ac4e

(async function() {
    const invoiceId = "c2f45a11-3bdd-4766-9fb3-dc09f932ac4e";
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    console.log('='.repeat(80));
    console.log('检查 Processing 状态的任务');
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
        
        // 查找 processing 状态的任务
        const processingTasks = tasks.filter(t => t.status === 'processing');
        const failedTasks = tasks.filter(t => t.status === 'failed');
        const completedTasks = tasks.filter(t => t.status === 'completed');
        const pendingTasks = tasks.filter(t => t.status === 'pending');
        
        console.log('任务状态统计:');
        console.log(`   Processing: ${processingTasks.length}`);
        console.log(`   Failed: ${failedTasks.length}`);
        console.log(`   Completed: ${completedTasks.length}`);
        console.log(`   Pending: ${pendingTasks.length}`);
        console.log();
        
        // 检查 processing 状态的任务
        if (processingTasks.length > 0) {
            console.log('='.repeat(80));
            console.log('Processing 状态的任务详情:');
            console.log('='.repeat(80));
            
            processingTasks.forEach((task, index) => {
                console.log(`\n任务 ${index + 1}:`);
                console.log(`  任务ID: ${task.id}`);
                console.log(`  任务编号: ${task.task_no || 'N/A'}`);
                console.log(`  状态: ${task.status}`);
                console.log(`  创建时间: ${task.create_time}`);
                console.log(`  开始时间: ${task.start_time || 'N/A'}`);
                console.log(`  结束时间: ${task.end_time || 'N/A'}`);
                console.log(`  Request ID: ${task.request_id || '❌ 未调用 Dify API'}`);
                console.log(`  Trace ID: ${task.trace_id || 'N/A'}`);
                console.log(`  错误代码: ${task.error_code || 'N/A'}`);
                console.log(`  错误消息: ${task.error_message || 'N/A'}`);
                
                // 计算处理时间
                if (task.start_time) {
                    const startTime = new Date(task.start_time);
                    const now = new Date();
                    const duration = Math.floor((now - startTime) / 1000);
                    console.log(`  处理时长: ${duration} 秒 (${Math.floor(duration / 60)} 分钟)`);
                }
                
                // 诊断
                console.log(`\n  诊断:`);
                if (!task.request_id) {
                    console.log(`  ⚠️  Dify API 尚未调用`);
                    console.log(`  💡 可能原因:`);
                    console.log(`     1. 任务刚启动，Dify API 调用还未开始`);
                    console.log(`     2. Dify API 调用失败（检查后端日志）`);
                    console.log(`     3. 任务参数有问题`);
                } else {
                    console.log(`  ✅ Dify API 已调用`);
                    console.log(`     Request ID: ${task.request_id}`);
                    
                    if (task.error_code) {
                        console.log(`  ❌ 调用失败`);
                        console.log(`     错误代码: ${task.error_code}`);
                        console.log(`     错误消息: ${task.error_message}`);
                    } else {
                        console.log(`  ✅ 调用成功，等待结果...`);
                    }
                }
            });
        }
        
        // 检查失败的任务
        if (failedTasks.length > 0) {
            console.log('\n' + '='.repeat(80));
            console.log('Failed 状态的任务详情:');
            console.log('='.repeat(80));
            
            failedTasks.forEach((task, index) => {
                console.log(`\n任务 ${index + 1}:`);
                console.log(`  任务ID: ${task.id}`);
                console.log(`  任务编号: ${task.task_no || 'N/A'}`);
                console.log(`  错误代码: ${task.error_code || 'N/A'}`);
                console.log(`  错误消息: ${task.error_message || 'N/A'}`);
                console.log(`  Request ID: ${task.request_id || 'N/A'}`);
                
                // 错误分析
                const errorCode = task.error_code?.toUpperCase() || '';
                const errorMsg = task.error_message || '';
                
                console.log(`\n  错误分析:`);
                if (errorCode.includes('TIMEOUT') || errorMsg.includes('超时') || errorMsg.includes('timeout')) {
                    console.log(`  🔍 问题: 请求超时`);
                    console.log(`  💡 解决方案:`);
                    console.log(`     1. 检查网络连接`);
                    console.log(`     2. 检查 Dify API 端点地址`);
                    console.log(`     3. 增加超时时间配置`);
                } else if (errorCode.includes('CONNECT') || errorMsg.includes('连接') || errorMsg.includes('Connection')) {
                    console.log(`  🔍 问题: 无法连接到 Dify API`);
                    console.log(`  💡 解决方案:`);
                    console.log(`     1. 检查 Dify API 端点地址是否正确`);
                    console.log(`     2. 检查网络连接`);
                    console.log(`     3. 检查防火墙设置`);
                } else if (errorCode.includes('AUTH') || errorMsg.includes('401') || errorMsg.includes('403')) {
                    console.log(`  🔍 问题: 认证失败`);
                    console.log(`  💡 解决方案:`);
                    console.log(`     1. 检查 API 密钥是否正确`);
                    console.log(`     2. 重新配置 API 密钥`);
                } else {
                    console.log(`  🔍 问题: ${task.error_code || '未知错误'}`);
                    console.log(`  💡 错误消息: ${errorMsg.substring(0, 200)}`);
                }
            });
        }
        
        // 检查已完成的任务
        if (completedTasks.length > 0) {
            console.log('\n' + '='.repeat(80));
            console.log('Completed 状态的任务:');
            console.log('='.repeat(80));
            
            completedTasks.forEach((task, index) => {
                console.log(`\n任务 ${index + 1}:`);
                console.log(`  任务ID: ${task.id}`);
                console.log(`  任务编号: ${task.task_no || 'N/A'}`);
                console.log(`  开始时间: ${task.start_time || 'N/A'}`);
                console.log(`  结束时间: ${task.end_time || 'N/A'}`);
                console.log(`  Request ID: ${task.request_id || 'N/A'}`);
            });
        }
        
        console.log('\n' + '='.repeat(80));
        console.log('检查完成');
        console.log('='.repeat(80));
        
        // 建议
        if (processingTasks.length > 0) {
            console.log('\n💡 建议:');
            console.log('   1. 如果任务长时间处于 processing 状态，检查后端日志');
            console.log('   2. 如果 Dify API 未调用，检查任务参数和模型配置');
            console.log('   3. 等待任务完成，或查看后端日志获取详细信息');
        }
        
    } catch (error) {
        console.error('❌ 检查失败:', error);
        console.error('错误详情:', error.stack);
    }
})();

