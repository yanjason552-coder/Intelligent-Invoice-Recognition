// 在浏览器控制台运行此代码来测试API
// 1. 先获取token（如果已登录）
const token = localStorage.getItem('access_token');

if (!token) {
    console.error('未找到token，请先登录');
} else {
    console.log('找到token:', token.substring(0, 20) + '...');
    
    // 2. 调用API
    fetch('http://localhost:8000/api/v1/statistics/recognition-status', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('响应状态:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('识别情况数据:', data);
        
        // 格式化显示
        console.log('\n========== 识别情况报告 ==========');
        console.log('任务状态:', data.task_status);
        console.log('长时间处理中的任务:', data.stuck_tasks?.length || 0, '个');
        console.log('最近失败的任务:', data.failed_tasks?.length || 0, '个');
        console.log('识别结果统计:', data.result_status);
        console.log('模板提示词使用情况:', data.prompt_usage);
        console.log('模型配置使用情况:', data.model_usage);
        console.log('===================================\n');
    })
    .catch(error => {
        console.error('请求失败:', error);
    });
}

