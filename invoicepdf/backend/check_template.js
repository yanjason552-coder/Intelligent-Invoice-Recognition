// 检查模板详情
// 在浏览器控制台运行

const templateId = "3cede2eb-2acf-465e-91da-899cff8ad9bd";
const token = localStorage.getItem('access_token');

(async function() {
    console.log('=== 检查模板详情 ===');
    console.log(`模板ID: ${templateId}\n`);
    
    try {
        const res = await fetch(`http://localhost:8000/api/v1/templates/${templateId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) {
            console.log(`❌ 获取模板失败: ${res.status} ${res.statusText}`);
            const error = await res.json();
            console.log('错误详情:', error);
            return;
        }
        
        const template = await res.json();
        console.log('模板信息:');
        console.log(`  名称: ${template.name}`);
        console.log(`  类型: ${template.template_type}`);
        console.log(`  状态: ${template.status}`);
        console.log(`  提示词: ${template.prompt ? '✓ 存在 (' + template.prompt.length + '字符)' : '✗ 不存在'}`);
        
        if (template.prompt) {
            console.log(`\n提示词内容（前200字符）:`);
            console.log(template.prompt.substring(0, 200));
        } else {
            console.log('\n⚠ 模板没有设置提示词！');
            console.log('请在前端编辑模板，添加提示词内容。');
        }
    } catch (err) {
        console.error('错误:', err);
    }
})();

