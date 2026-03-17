// 在浏览器控制台运行此代码来监控发票识别任务
// 使用方法：复制以下代码到浏览器控制台（Console）运行

(async function monitorInvoice() {
    const filename = "China SY inv 1.PDF";
    const token = localStorage.getItem('access_token');
    
    console.log('=== 开始监控发票识别任务 ===');
    console.log(`文件名: ${filename}\n`);
    
    try {
        // 1. 查找发票
        const invoiceResponse = await fetch('http://localhost:8000/api/v1/invoices/query?limit=100', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const invoiceData = await invoiceResponse.json();
        const invoices = invoiceData.data || [];
        
        let foundInvoice = null;
        let foundFile = null;
        
        for (const invoice of invoices) {
            const files = invoice.files || [];
            for (const file of files) {
                if (file.filename && file.filename.toLowerCase().includes(filename.toLowerCase())) {
                    foundInvoice = invoice;
                    foundFile = file;
                    break;
                }
            }
            if (foundInvoice) break;
        }
        
        if (!foundInvoice) {
            console.error('❌ 未找到发票文件:', filename);
            return;
        }
        
        console.log('✓ 找到发票:');
        console.log('  发票ID:', foundInvoice.id);
        console.log('  文件名:', foundFile.filename);
        console.log('  文件ID:', foundFile.id);
        console.log('');
        
        // 2. 查询该发票的识别任务
        const taskResponse = await fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=100', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const taskData = await taskResponse.json();
        const allTasks = taskData.data || [];
        const tasks = allTasks.filter(t => t.invoice_id === foundInvoice.id);
        
        if (tasks.length === 0) {
            console.log('⚠ 该发票还没有识别任务');
            console.log('请在前端创建识别任务后重新运行此脚本');
            return;
        }
        
        console.log(`✓ 找到 ${tasks.length} 个任务:\n`);
        tasks.forEach((task, i) => {
            console.log(`任务 ${i + 1}:`);
            console.log('  任务编号:', task.task_no);
            console.log('  状态:', task.status);
            console.log('  模型:', task.model_name || 'N/A');
            console.log('  模板ID:', task.template_id || 'N/A');
            console.log('  包含提示词:', task.params?.template_prompt ? '✓ 是 (' + task.params.template_prompt.length + '字符)' : '✗ 否');
            console.log('  创建时间:', task.create_time);
            
            // 检查模型
            const modelName = (task.model_name || '').toLowerCase();
            if (modelName.includes('v3') || modelName.includes('jsonschema')) {
                console.log('  ⭐ 使用正确的模型');
            } else {
                console.log('  ⚠ 使用的模型可能不正确');
            }
            console.log('');
        });
        
        // 选择最新的任务
        const latestTask = tasks[0];
        const taskId = latestTask.id;
        
        console.log('选择监控任务:', latestTask.task_no);
        console.log('开始监控... (每5秒检查一次)\n');
        
        // 3. 开始监控
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
                    console.log('❌ 无法找到任务');
                    return;
                }
                
                const status = task.status;
                const now = new Date().toLocaleTimeString();
                
                // 状态变化时显示详细信息
                if (status !== lastStatus) {
                    console.log(`\n[${now}] 状态变化: ${status}`);
                    console.log('  任务编号:', task.task_no);
                    console.log('  使用的模型:', task.model_name || 'N/A');
                    console.log('  模板ID:', task.template_id || 'N/A');
                    console.log('  包含提示词:', task.params?.template_prompt ? '✓ 是' : '✗ 否');
                    
                    // 检查模型
                    const modelName = (task.model_name || '').toLowerCase();
                    if (modelName.includes('v3') || modelName.includes('jsonschema')) {
                        console.log('  ⭐ 使用正确的模型');
                    } else {
                        console.log('  ⚠ 使用的模型可能不正确');
                    }
                    
                    if (task.start_time) console.log('  开始时间:', task.start_time);
                    if (task.end_time) console.log('  结束时间:', task.end_time);
                    
                    lastStatus = status;
                } else if (status === 'processing') {
                    // 处理中时显示进度
                    const elapsed = task.start_time ? 
                        Math.round((new Date() - new Date(task.start_time)) / 1000) : 0;
                    console.log(`[${now}] 处理中... (已处理 ${elapsed} 秒)`);
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
                            console.log('  状态:', result.status);
                            if (result.accuracy !== null && result.accuracy !== undefined) {
                                console.log('  准确率:', (result.accuracy * 100).toFixed(2) + '%');
                            }
                            if (result.confidence !== null && result.confidence !== undefined) {
                                console.log('  置信度:', (result.confidence * 100).toFixed(2) + '%');
                            }
                            console.log('  识别字段数:', result.recognized_fields + '/' + result.total_fields);
                            
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
                    console.log('错误信息:', task.params?.error_message || 'N/A');
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

