// 在浏览器控制台中运行此代码来检查发票错误
// 使用方法1: 通过发票编号查找
// const invoiceNo = "INV-20260205111510-5f22ea3b";
// 使用方法2: 通过 invoice_file.id 查找
// const invoiceFileId = "a9e353a6-2bef-4918-8af2-18560eb96f5b";

(async function() {
    // 配置：选择一种方式
    const invoiceNo = "INV-20260205111510-5f22ea3b";  // 方式1: 发票编号
    const invoiceFileId = "a9e353a6-2bef-4918-8af2-18560eb96f5b";  // 方式2: invoice_file.id
    
    const token = localStorage.getItem('access_token');
    const baseUrl = window.location.origin;
    
    if (!token) {
        console.error('未找到 access_token，请先登录');
        return;
    }
    
    console.log('='.repeat(80));
    console.log('发票 Dify API 调用失败诊断');
    console.log('='.repeat(80));
    if (invoiceNo) {
        console.log(`发票编号: ${invoiceNo}`);
    }
    if (invoiceFileId) {
        console.log(`发票文件ID: ${invoiceFileId}`);
    }
    console.log();
    
    try {
        let invoice = null;
        
        // 方式1: 通过发票编号查找
        if (invoiceNo) {
            console.log('正在通过发票编号查找发票...');
            const invoicesResponse = await fetch(`${baseUrl}/api/v1/invoices/query?invoice_no=${encodeURIComponent(invoiceNo)}&limit=100`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!invoicesResponse.ok) {
                console.error(`查询失败: HTTP ${invoicesResponse.status}`);
                const errorText = await invoicesResponse.text();
                console.error(`错误信息: ${errorText}`);
                return;
            }
            
            const invoicesData = await invoicesResponse.json();
            invoice = invoicesData.data?.[0];  // 取第一个匹配的
        }
        
        // 方式2: 通过 invoice_file.id 查找
        if (!invoice && invoiceFileId) {
            console.log('正在通过发票文件ID查找发票...');
            // 先获取发票文件信息
            const fileResponse = await fetch(`${baseUrl}/api/v1/invoices/files/list?limit=1000`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (fileResponse.ok) {
                const filesData = await fileResponse.json();
                const fileItem = filesData.data?.find(f => f.id === invoiceFileId || f.file_id === invoiceFileId);
                
                if (fileItem && fileItem.invoice_id) {
                    // 通过 invoice_id 获取发票详情
                    const invoiceResponse = await fetch(`${baseUrl}/api/v1/invoices/${fileItem.invoice_id}`, {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (invoiceResponse.ok) {
                        invoice = await invoiceResponse.json();
                    }
                }
            }
        }
        
        if (!invoice) {
            console.error('未找到发票');
            if (invoiceNo) {
                console.error(`请检查发票编号是否正确: ${invoiceNo}`);
            }
            if (invoiceFileId) {
                console.error(`请检查发票文件ID是否正确: ${invoiceFileId}`);
            }
            return;
        }
        
        console.log('✅ 找到发票:');
        console.log(`   发票ID: ${invoice.id}`);
        console.log(`   发票编号: ${invoice.invoice_no}`);
        console.log(`   识别状态: ${invoice.recognition_status}`);
        if (invoice.error_code) {
            console.log(`   ❌ 错误代码: ${invoice.error_code}`);
        }
        if (invoice.error_message) {
            console.log(`   ❌ 错误消息: ${invoice.error_message}`);
        }
        console.log();
        
        // 2. 获取识别任务
        console.log('正在查找识别任务...');
        const tasksResponse = await fetch(`${baseUrl}/api/v1/invoices/recognition-tasks?limit=100`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const tasksData = await tasksResponse.json();
        const tasks = tasksData.data?.filter(task => task.invoice_id === invoice.id) || [];
        
        if (tasks.length === 0) {
            console.error('未找到识别任务');
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
            console.log(`任务编号: ${task.task_no}`);
            console.log(`状态: ${task.status}`);
            console.log(`创建时间: ${task.create_time}`);
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
            console.log('任务参数:');
            if (params.model_config_id) {
                console.log(`  ✅ 模型配置ID: ${params.model_config_id}`);
            } else {
                console.log(`  ❌ 模型配置ID未设置`);
            }
            
            if (params.template_id || task.template_id) {
                console.log(`  ✅ 模板ID: ${params.template_id || task.template_id}`);
            }
            
            if (params.template_prompt) {
                const promptStr = String(params.template_prompt);
                console.log(`  ✅ 提示词已设置，长度: ${promptStr.length} 字符`);
            } else {
                console.log(`  ⚠️  提示词未设置`);
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
                
                if (errorCode.includes('TIMEOUT') || errorMsg.includes('超时')) {
                    console.log('🔍 问题: 请求超时');
                    console.log('💡 建议:');
                    console.log('   1. 检查网络连接');
                    console.log('   2. 检查 Dify API 端点地址是否正确');
                    console.log('   3. 增加超时时间配置');
                } else if (errorCode.includes('CONNECT') || errorMsg.includes('连接') || errorMsg.includes('Connection')) {
                    console.log('🔍 问题: 无法连接到 Dify API');
                    console.log('💡 建议:');
                    console.log('   1. 检查 Dify API 端点地址是否正确');
                    console.log('   2. 检查网络连接');
                    console.log('   3. 检查防火墙设置');
                } else if (errorCode.includes('AUTH') || errorMsg.includes('401') || errorMsg.includes('403') || errorMsg.includes('Unauthorized')) {
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
                } else {
                    console.log(`🔍 问题: ${task.error_code}`);
                    console.log(`💡 错误消息: ${errorMsg.substring(0, 200)}`);
                }
                console.log();
            }
        }
        
        console.log('='.repeat(80));
        console.log('诊断完成');
        console.log('='.repeat(80));
        
    } catch (error) {
        console.error('诊断失败:', error);
    }
})();

