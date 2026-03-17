// 直接通过发票ID查询任务（避免使用有问题的端点）
// 发票ID: c2f45a11-3bdd-4766-9fb3-dc09f932ac4e

(async function() {
    const invoiceId = "c2f45a11-3bdd-4766-9fb3-dc09f932ac4e";
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    if (!token) {
        console.error('❌ 未找到 access_token，请先登录');
        return;
    }
    
    console.log('='.repeat(80));
    console.log('发票 Dify API 调用失败诊断（直接查询）');
    console.log('='.repeat(80));
    console.log(`发票ID: ${invoiceId}`);
    console.log();
    
    try {
        // 1. 获取发票详情
        console.log('正在获取发票详情...');
        const invoiceResponse = await fetch(`${baseUrl}/api/v1/invoices/${invoiceId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!invoiceResponse.ok) {
            console.error(`❌ 获取发票详情失败: HTTP ${invoiceResponse.status}`);
            const errorText = await invoiceResponse.text();
            console.error(`错误信息: ${errorText}`);
            return;
        }
        
        const invoice = await invoiceResponse.json();
        console.log('✅ 找到发票:');
        console.log(`   发票ID: ${invoice.id}`);
        console.log(`   发票编号: ${invoice.invoice_no || 'N/A'}`);
        console.log(`   识别状态: ${invoice.recognition_status || 'N/A'}`);
        if (invoice.error_code) {
            console.log(`   ❌ 错误代码: ${invoice.error_code}`);
        }
        if (invoice.error_message) {
            console.log(`   ❌ 错误消息: ${invoice.error_message}`);
        }
        console.log();
        
        // 2. 直接查询数据库（通过后端API查询该发票的所有任务）
        // 由于 /recognition-tasks 端点有问题，我们尝试通过其他方式获取
        console.log('正在查找识别任务...');
        console.log('⚠️  注意: 如果 /recognition-tasks 端点返回 500 错误，');
        console.log('   请查看后端日志获取详细错误信息');
        console.log();
        
        // 尝试查询任务列表（如果失败，会显示错误）
        const tasksResponse = await fetch(`${baseUrl}/api/v1/invoices/recognition-tasks?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!tasksResponse.ok) {
            console.error(`❌ 获取任务列表失败: HTTP ${tasksResponse.status}`);
            const errorText = await tasksResponse.text();
            console.error(`错误信息: ${errorText}`);
            console.log();
            console.log('💡 建议:');
            console.log('   1. 检查后端日志查看详细错误');
            console.log('   2. 后端端点 /api/v1/invoices/recognition-tasks 可能存在问题');
            console.log('   3. 已修复该端点，请重启后端服务后重试');
            return;
        }
        
        const tasksData = await tasksResponse.json();
        const tasks = tasksData.data?.filter(task => task.invoice_id === invoiceId) || [];
        
        if (tasks.length === 0) {
            console.log('⚠️  未找到识别任务');
            console.log('   可能原因:');
            console.log('   1. 任务尚未创建');
            console.log('   2. 任务属于其他发票');
            console.log('   3. 权限问题');
            return;
        }
        
        console.log(`✅ 找到 ${tasks.length} 个识别任务`);
        console.log();
        
        // 3. 诊断每个任务
        for (let i = 0; i < tasks.length; i++) {
            const task = tasks[i];
            console.log('='.repeat(80));
            console.log(`任务 ${i + 1}/${tasks.length}:`);
            console.log('='.repeat(80));
            console.log(`任务ID: ${task.id}`);
            console.log(`任务编号: ${task.task_no || 'N/A'}`);
            console.log(`状态: ${task.status || 'N/A'}`);
            console.log(`创建时间: ${task.create_time || 'N/A'}`);
            console.log(`开始时间: ${task.start_time || 'N/A'}`);
            console.log(`结束时间: ${task.end_time || 'N/A'}`);
            console.log();
            
            if (task.error_code) {
                console.log(`❌ 错误代码: ${task.error_code}`);
            }
            if (task.error_message) {
                console.log(`❌ 错误消息: ${task.error_message}`);
                console.log();
            }
            
            // 检查任务参数
            const params = task.params || {};
            console.log('任务参数检查:');
            if (params.model_config_id) {
                console.log(`  ✅ 模型配置ID: ${params.model_config_id}`);
            } else {
                console.log(`  ❌ 模型配置ID未设置`);
            }
            
            if (params.template_id || task.template_id) {
                console.log(`  ✅ 模板ID: ${params.template_id || task.template_id}`);
            } else {
                console.log(`  ⚠️  模板ID未设置`);
            }
            
            if (params.template_prompt) {
                const promptStr = String(params.template_prompt);
                console.log(`  ✅ 提示词已设置，长度: ${promptStr.length} 字符`);
                console.log(`  ✅ 提示词预览: ${promptStr.substring(0, 100)}...`);
            } else {
                console.log(`  ⚠️  提示词未包含在任务参数中`);
            }
            console.log();
            
            // 检查 Dify API 调用
            if (task.request_id) {
                console.log(`✅ Dify API 已调用`);
                console.log(`   Request ID: ${task.request_id}`);
            } else {
                console.log(`❌ Dify API 未调用（没有 request_id）`);
            }
            
            if (task.trace_id) {
                console.log(`   Trace ID: ${task.trace_id}`);
            }
            console.log();
            
            // 错误分析
            if (task.error_code) {
                console.log('错误分析:');
                const errorCode = task.error_code.toUpperCase();
                const errorMsg = task.error_message || '';
                
                if (errorCode.includes('TIMEOUT') || errorMsg.includes('超时') || errorMsg.includes('timeout')) {
                    console.log('🔍 问题: 请求超时');
                    console.log('💡 建议:');
                    console.log('   1. 检查网络连接');
                    console.log('   2. 检查 Dify API 端点地址是否正确');
                    console.log('   3. 增加超时时间配置');
                } else if (errorCode.includes('CONNECT') || errorMsg.includes('连接') || errorMsg.includes('Connection') || errorMsg.includes('connect')) {
                    console.log('🔍 问题: 无法连接到 Dify API');
                    console.log('💡 建议:');
                    console.log('   1. 检查 Dify API 端点地址是否正确');
                    console.log('   2. 检查网络连接');
                    console.log('   3. 检查防火墙设置');
                    console.log('   4. 尝试在浏览器中访问 Dify API 端点');
                } else if (errorCode.includes('AUTH') || errorMsg.includes('401') || errorMsg.includes('403') || errorMsg.includes('Unauthorized') || errorMsg.includes('认证')) {
                    console.log('🔍 问题: 认证失败');
                    console.log('💡 建议:');
                    console.log('   1. 检查 API 密钥是否正确');
                    console.log('   2. 检查 API 密钥是否过期');
                    console.log('   3. 重新配置 API 密钥');
                } else if (errorCode.includes('NOT_FOUND') || errorMsg.includes('404')) {
                    console.log('🔍 问题: 资源未找到');
                    console.log('💡 建议:');
                    console.log('   1. 检查 workflow_id 或 app_id 是否正确');
                    console.log('   2. 检查 Dify 平台上的工作流/应用是否存在');
                } else if (errorCode.includes('BAD_PARAMS')) {
                    console.log('🔍 问题: 参数错误');
                    console.log('💡 建议:');
                    console.log('   1. 检查模型配置是否完整');
                    console.log('   2. 检查任务参数是否正确');
                    console.log('   3. 检查模板配置是否正确');
                } else {
                    console.log(`🔍 问题: ${task.error_code}`);
                    console.log(`💡 错误消息: ${errorMsg.substring(0, 300)}`);
                }
                console.log();
            }
        }
        
        console.log('='.repeat(80));
        console.log('诊断完成');
        console.log('='.repeat(80));
        
    } catch (error) {
        console.error('❌ 诊断失败:', error);
        console.error('错误详情:', error.stack);
    }
})();

