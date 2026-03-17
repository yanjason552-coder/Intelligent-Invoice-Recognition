// 修复版：在浏览器控制台运行此代码来监控发票识别任务
// 使用方法：复制以下代码到浏览器控制台（Console）运行

(async function monitorInvoice() {
    const filename = "China SY inv 1.PDF";
    const token = localStorage.getItem('access_token');
    
    console.log('=== 查找发票 ===');
    console.log(`搜索文件名: ${filename}\n`);
    
    try {
        // 1. 获取所有发票
        const invoiceResponse = await fetch('http://localhost:8000/api/v1/invoices/query?limit=100', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const invoiceData = await invoiceResponse.json();
        const invoices = invoiceData.data || [];
        
        console.log(`找到 ${invoices.length} 个发票，正在检查文件名...\n`);
        
        // 2. 对每个发票获取文件信息
        let foundInvoice = null;
        let foundFile = null;
        
        for (const invoice of invoices) {
            try {
                const fileResponse = await fetch(`http://localhost:8000/api/v1/invoices/${invoice.id}/file`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (fileResponse.ok) {
                    const fileData = await fileResponse.json();
                    const fileName = fileData.file_name || '';
                    
                    console.log(`  检查: ${fileName}`);
                    
                    if (fileName.toLowerCase().includes(filename.toLowerCase()) || 
                        filename.toLowerCase().includes(fileName.toLowerCase())) {
                        foundInvoice = invoice;
                        foundFile = fileData;
                        console.log(`\n✓ 找到匹配的发票！`);
                        break;
                    }
                }
            } catch (err) {
                // 忽略单个发票的文件获取错误
                console.log(`  发票 ${invoice.id}: 无法获取文件信息`);
            }
        }
        
        if (!foundInvoice) {
            console.log('\n❌ 未找到匹配的发票文件');
            console.log('\n所有发票列表:');
            for (let i = 0; i < Math.min(invoices.length, 10); i++) {
                const inv = invoices[i];
                try {
                    const fileRes = await fetch(`http://localhost:8000/api/v1/invoices/${inv.id}/file`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (fileRes.ok) {
                        const file = await fileRes.json();
                        console.log(`  ${i + 1}. ${file.file_name} (发票ID: ${inv.id})`);
                    }
                } catch (e) {
                    console.log(`  ${i + 1}. 发票ID: ${inv.id} (无法获取文件名)`);
                }
            }
            return;
        }
        
        console.log(`\n发票信息:`);
        console.log(`  发票ID: ${foundInvoice.id}`);
        console.log(`  发票编号: ${foundInvoice.invoice_no}`);
        console.log(`  文件名: ${foundFile.file_name}`);
        console.log(`  文件ID: ${foundFile.id}`);
        console.log(`  文件类型: ${foundFile.file_type}`);
        console.log(`  创建时间: ${foundInvoice.create_time}`);
        
        // 3. 查询该发票的识别任务
        const taskResponse = await fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=100', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const taskData = await taskResponse.json();
        const allTasks = taskData.data || [];
        const tasks = allTasks.filter(t => t.invoice_id === foundInvoice.id);
        
        if (tasks.length === 0) {
            console.log('\n⚠ 该发票还没有识别任务');
            console.log('请在前端创建识别任务后重新运行此脚本');
            return;
        }
        
        console.log(`\n找到 ${tasks.length} 个任务:\n`);
        tasks.forEach((task, i) => {
            console.log(`任务 ${i + 1}:`);
            console.log(`  任务编号: ${task.task_no}`);
            console.log(`  状态: ${task.status}`);
            console.log(`  模型: ${task.model_name || 'N/A'}`);
            console.log(`  模板ID: ${task.template_id || 'N/A'}`);
            console.log(`  包含提示词: ${task.params?.template_prompt ? '✓ 是 (' + task.params.template_prompt.length + '字符)' : '✗ 否'}`);
            console.log(`  创建时间: ${task.create_time}`);
            
            // 检查模型
            const modelName = (task.model_name || '').toLowerCase();
            if (modelName.includes('v3') || modelName.includes('jsonschema')) {
                console.log(`  ⭐ 使用正确的模型`);
            } else {
                console.log(`  ⚠ 使用的模型可能不正确`);
            }
            console.log('');
        });
        
        // 4. 选择最新的任务进行监控
        const latestTask = tasks[0];
        const taskId = latestTask.id;
        
        console.log(`选择监控任务: ${latestTask.task_no}`);
        console.log(`开始监控... (每5秒检查一次)\n`);
        console.log('='.repeat(60));
        
        // 5. 开始监控
        let checkCount = 0;
        let lastStatus = null;
        const maxChecks = 120; // 最多检查10分钟
        
        const checkStatus = async () => {
            if (checkCount >= maxChecks) {
                console.log('\n⚠ 达到最大检查次数，停止监控');
                return;
            }
            
            checkCount++;
            
            try {
                const response = await fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=100', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                const tasks = data.data || [];
                const task = tasks.find(t => t.id === taskId);
                
                if (!task) {
                    console.log('\n❌ 无法找到任务');
                    return;
                }
                
                const status = task.status;
                const now = new Date().toLocaleTimeString();
                
                // 状态变化时显示详细信息
                if (status !== lastStatus) {
                    console.log(`\n[${now}] 状态变化: ${status}`);
                    console.log(`  任务编号: ${task.task_no}`);
                    console.log(`  使用的模型: ${task.model_name || 'N/A'}`);
                    console.log(`  模板ID: ${task.template_id || 'N/A'}`);
                    console.log(`  包含提示词: ${task.params?.template_prompt ? '✓ 是' : '✗ 否'}`);
                    
                    // 检查模型
                    const modelName = (task.model_name || '').toLowerCase();
                    if (modelName.includes('v3') || modelName.includes('jsonschema')) {
                        console.log(`  ⭐ 使用正确的模型`);
                    } else {
                        console.log(`  ⚠ 使用的模型可能不正确`);
                    }
                    
                    if (task.start_time) console.log(`  开始时间: ${task.start_time}`);
                    if (task.end_time) console.log(`  结束时间: ${task.end_time}`);
                    
                    lastStatus = status;
                } else if (status === 'processing') {
                    // 处理中时显示进度
                    const elapsed = task.start_time ? 
                        Math.round((new Date() - new Date(task.start_time)) / 1000) : 0;
                    console.log(`[${now}] 处理中... (已处理 ${elapsed} 秒)`, '\r');
                }
                
                // 任务完成或失败
                if (status === 'completed') {
                    console.log('\n\n✓ 任务完成！');
                    console.log('正在获取识别结果...\n');
                    
                    // 获取识别结果
                    try {
                        const resultResponse = await fetch(`http://localhost:8000/api/v1/invoices/recognition-results?task_id=${taskId}`, {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        const resultData = await resultResponse.json();
                        const results = resultData.data || [];
                        
                        if (results.length > 0) {
                            const result = results[0];
                            console.log('识别结果:');
                            console.log(`  状态: ${result.status}`);
                            if (result.accuracy !== null && result.accuracy !== undefined) {
                                console.log(`  准确率: ${(result.accuracy * 100).toFixed(2)}%`);
                            }
                            if (result.confidence !== null && result.confidence !== undefined) {
                                console.log(`  置信度: ${(result.confidence * 100).toFixed(2)}%`);
                            }
                            console.log(`  识别字段数: ${result.recognized_fields}/${result.total_fields}`);
                            
                            // 获取字段详情
                            if (result.id) {
                                const fieldsResponse = await fetch(`http://localhost:8000/api/v1/invoices/recognition-results/${result.id}/fields`, {
                                    headers: { 'Authorization': `Bearer ${token}` }
                                });
                                const fieldsData = await fieldsResponse.json();
                                const fields = fieldsData.data || [];
                                
                                if (fields.length > 0) {
                                    console.log(`\n识别字段详情 (共 ${fields.length} 个字段，显示前10个):`);
                                    fields.slice(0, 10).forEach(field => {
                                        const value = field.field_value || '';
                                        const displayValue = value.length > 50 ? value.substring(0, 50) + '...' : value;
                                        console.log(`  ${field.field_name}: ${displayValue}`);
                                    });
                                    if (fields.length > 10) {
                                        console.log(`  ... 还有 ${fields.length - 10} 个字段`);
                                    }
                                }
                            }
                        } else {
                            console.log('⚠ 未找到识别结果');
                        }
                    } catch (err) {
                        console.error('获取识别结果失败:', err);
                    }
                    
                    console.log('\n=== 监控结束 ===');
                    return;
                } else if (status === 'failed') {
                    console.log('\n\n❌ 任务失败');
                    console.log(`错误信息: ${task.params?.error_message || 'N/A'}`);
                    console.log('\n=== 监控结束 ===');
                    return;
                }
                
                // 继续监控
                setTimeout(checkStatus, 5000);
            } catch (err) {
                console.error('查询失败:', err);
                setTimeout(checkStatus, 5000);
            }
        };
        
        // 开始第一次检查
        checkStatus();
        
    } catch (err) {
        console.error('错误:', err);
    }
})();

