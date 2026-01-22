// 前端API调试脚本
// 在浏览器控制台中运行

async function debugAPI() {
  console.log('🔍 开始调试API连接...')
  
  // 检查访问令牌
  const token = localStorage.getItem('access_token')
  console.log('访问令牌:', token ? '存在' : '不存在')
  
  if (!token) {
    console.error('❌ 未找到访问令牌，请先登录')
    return
  }
  
  // 测试API连接
  try {
    const response = await fetch('/api/v1/salesOrderDocD/unified', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        action: 'list',
        module: 'sales_order_doc_d',
        page: 1,
        limit: 5,
        timestamp: new Date().toISOString()
      })
    })
    
    console.log('响应状态:', response.status)
    console.log('响应头:', Object.fromEntries(response.headers.entries()))
    
    const responseText = await response.text()
    console.log('响应文本:', responseText)
    
    if (response.ok) {
      try {
        const result = JSON.parse(responseText)
        console.log('✅ API连接成功!')
        console.log('响应数据:', result)
      } catch (e) {
        console.error('❌ JSON解析失败:', e)
      }
    } else {
      console.error('❌ API调用失败:', response.status, responseText)
    }
    
  } catch (error) {
    console.error('❌ 网络错误:', error)
  }
}

// 运行调试
debugAPI() 