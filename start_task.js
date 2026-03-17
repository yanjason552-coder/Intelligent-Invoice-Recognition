// 启动识别任务
// 发票ID: c2f45a11-3bdd-4766-9fb3-dc09f932ac4e

(async function() {
    const invoiceId = "c2f45a11-3bdd-4766-9fb3-dc09f932ac4e";
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    console.log('='.repeat(80));
    console.log('启动识别任务');
    console.log('='.repeat(80));
    console.log(`发票ID: ${invoiceId}`);
    console.log();
    
    try {
        // 1. 获取任务列表
        console.log('正在获取任务列表...');
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
        const tasks = tasksData.data?.filter(task => 
            task.invoice_id === invoiceId && 
            task.status === 'pending'
        ) || [];
        
        if (tasks.length === 0) {
            console.log('⚠️  未找到 pending 状态的任务');
            return;
        }
        
        console.log(`找到 ${tasks.length} 个 pending 状态的任务`);
        console.log();
        
        // 2. 启动最新的任务
        const latestTask = tasks[0]; // 取第一个（最新的）
        console.log(`准备启动任务: ${latestTask.task_no || latestTask.id}`);
        console.log(`任务ID: ${latestTask.id}`);
        console.log();
        
        // 3. 启动任务
        console.log('正在启动任务...');
        const startResponse = await fetch(`${baseUrl}/api/v1/invoices/recognition-tasks/${latestTask.id}/start`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!startResponse.ok) {
            const errorText = await startResponse.text();
            console.error(`❌ 启动任务失败: HTTP ${startResponse.status}`);
            console.error(`错误信息: ${errorText}`);
            return;
        }
        
        const result = await startResponse.json();
        console.log('✅ 任务启动响应:');
        console.log(JSON.stringify(result, null, 2));
        console.log();
        
        // 4. 等待几秒后检查任务状态
        console.log('等待 3 秒后检查任务状态...');
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 5. 再次获取任务状态
        console.log('正在检查任务状态...');
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
                console.log('任务状态更新:');
                console.log(`  状态: ${updatedTask.status}`);
                console.log(`  开始时间: ${updatedTask.start_time || 'N/A'}`);
                console.log(`  Request ID: ${updatedTask.request_id || 'N/A'}`);
                console.log(`  错误代码: ${updatedTask.error_code || 'N/A'}`);
                console.log(`  错误消息: ${updatedTask.error_message || 'N/A'}`);
                
                if (updatedTask.status === 'processing') {
                    console.log();
                    console.log('✅ 任务正在处理中...');
                    console.log('💡 建议: 等待任务完成，或使用监控脚本查看进度');
                } else if (updatedTask.status === 'failed') {
                    console.log();
                    console.log('❌ 任务失败');
                    console.log('💡 请查看错误信息并修复问题');
                } else if (updatedTask.status === 'completed') {
                    console.log();
                    console.log('✅ 任务已完成');
                }
            }
        }
        
        console.log();
        console.log('='.repeat(80));
        console.log('操作完成');
        console.log('='.repeat(80));
        
    } catch (error) {
        console.error('❌ 操作失败:', error);
        console.error('错误详情:', error.stack);
    }
})();

