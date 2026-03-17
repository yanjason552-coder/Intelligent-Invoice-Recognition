// 简化版：在浏览器控制台运行此代码来监控发票识别任务
// 使用方法：复制以下代码到浏览器控制台（Console）运行

const filename = "China SY inv 1.PDF";
const token = localStorage.getItem('access_token');

console.log('=== 开始监控发票识别任务 ===');
console.log(`文件名: ${filename}\n`);

// 1. 查找发票
fetch('http://localhost:8000/api/v1/invoices/query?limit=100', {
    headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(data => {
    const invoices = data.data || [];
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
    
    const invoiceId = foundInvoice.id;
    
    // 2. 查询该发票的识别任务
    return Promise.all([
        fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=100', {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json()),
        Promise.resolve(invoiceId)
    ]);
})
.then(([taskData, invoiceId]) => {
    const allTasks = taskData.data || [];
    const tasks = allTasks.filter(t => t.invoice_id === invoiceId);
        
        if (tasks.length === 0) {
            console.log('⚠ 该发票还没有识别任务');
            console.log('请在前端创建识别任务后重新运行此脚本');
            return null;
        }
        
        console.log(`✓ 找到 ${tasks.length} 个任务:\n`);
        tasks.forEach((task, i) => {
            console.log(`任务 ${i + 1}:`);
            console.log('  任务编号:', task.task_no);
            console.log('  状态:', task.status);
            console.log('  模型:', task.model_name || 'N/A');
            console.log('  模板ID:', task.template_id || 'N/A');
            console.log('  包含提示词:', task.params?.template_prompt ? '✓ 是' : '✗ 否');
            console.log('  创建时间:', task.create_time);
            console.log('');
        });
        
        // 选择最新的任务
        const latestTask = tasks[0];
        console.log('选择监控任务:', latestTask.task_no);
        console.log('');
        
        // 开始监控
        return latestTask.id;
    });
})
.then(taskId => {
    if (!taskId) return;
    
    console.log('开始监控任务...');
    console.log('每5秒检查一次状态\n');
    
    let checkCount = 0;
    let lastStatus = null;
    const maxChecks = 120; // 最多检查10分钟
    
    const checkStatus = () => {
        if (checkCount >= maxChecks) {
            console.log('\n⚠ 达到最大检查次数，停止监控');
            return;
        }
        
        checkCount++;
        
        fetch('http://localhost:8000/api/v1/invoices/recognition-tasks?limit=100', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(r => r.json())
        .then(data => {
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
                process.stdout.write(`\r[${now}] 处理中... (已处理 ${elapsed} 秒)`);
            }
            
            // 任务完成或失败
            if (status === 'completed') {
                console.log('\n\n✓ 任务完成！');
                console.log('正在获取识别结果...\n');
                
                // 获取识别结果
                fetch(`http://localhost:8000/api/v1/invoices/recognition-results?task_id=${taskId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                })
                .then(r => r.json())
                .then(resultData => {
                    const results = resultData.data || [];
                    if (results.length > 0) {
                        const result = results[0];
                        console.log('识别结果:');
                        console.log('  状态:', result.status);
                        if (result.accuracy) console.log('  准确率:', (result.accuracy * 100).toFixed(2) + '%');
                        if (result.confidence) console.log('  置信度:', (result.confidence * 100).toFixed(2) + '%');
                        console.log('  识别字段数:', result.recognized_fields + '/' + result.total_fields);
                    }
                });
                
                return;
            } else if (status === 'failed') {
                console.log('\n\n❌ 任务失败');
                return;
            }
            
            // 继续监控
            setTimeout(checkStatus, 5000);
        })
        .catch(err => {
            console.error('查询失败:', err);
        });
    };
    
    // 开始第一次检查
    checkStatus();
})
.catch(err => {
    console.error('错误:', err);
});

