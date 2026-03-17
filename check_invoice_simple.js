// 简化版：直接通过 invoice_file.id 查找发票错误
// 在浏览器控制台中运行此代码

(async function() {
    const invoiceFileId = "a9e353a6-2bef-4918-8af2-18560eb96f5b";  // invoice_file.id
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    if (!token) {
        console.error('❌ 未找到 access_token，请先登录');
        return;
    }
    
    console.log('='.repeat(80));
    console.log('发票 Dify API 调用失败诊断');
    console.log('='.repeat(80));
    console.log(`发票文件ID: ${invoiceFileId}`);
    console.log();
    
    try {
        // 1. 通过文件列表查找发票
        console.log('正在查找发票文件...');
        const filesResponse = await fetch(`${baseUrl}/api/v1/invoices/files/list?limit=1000`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!filesResponse.ok) {
            console.error(`❌ 查询文件列表失败: HTTP ${filesResponse.status}`);
            const errorText = await filesResponse.text();
            console.error(`错误信息: ${errorText}`);
            return;
        }
        
        const filesData = await filesResponse.json();
        const fileItem = filesData.data?.find(f => 
            f.id === invoiceFileId || 
            f.file_id === invoiceFileId ||
            (f.file && f.file.id === invoiceFileId)
        );
        
        if (!fileItem) {
            console.error('❌ 未找到发票文件');
            console.log(`查询到的文件数量: ${filesData.data?.length || 0}`);
            return;
        }
        
        console.log('✅ 找到发票文件:');
        console.log(`   文件ID: ${fileItem.id || fileItem.file_id}`);
        console.log(`   文件名: ${fileItem.file_name || 'N/A'}`);
        console.log(`   发票ID: ${fileItem.invoice_id || 'N/A'}`);
        console.log();
        
        if (!fileItem.invoice_id) {
            console.error('❌ 发票文件未关联到发票');
            return;
        }
        
        // 2. 获取发票详情
        console.log('正在获取发票详情...');
        const invoiceResponse = await fetch(`${baseUrl}/api/v1/invoices/${fileItem.invoice_id}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!invoiceResponse.ok) {
            console.error(`❌ 获取发票详情失败: HTTP ${invoiceResponse.status}`);
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
        
        // 3. 获取识别任务
        console.log('正在查找识别任务...');
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
        const tasks = tasksData.data?.filter(task => task.invoice_id === invoice.id) || [];
        
        if (tasks.length === 0) {
            console.error('❌ 未找到识别任务');
            return;
        }
        
        console.log(`✅ 找到 ${tasks.length} 个识别任务`);
        console.log();
        
        // 4. 诊断每个任务
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

