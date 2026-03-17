// 启动所有待处理的识别任务 - 浏览器控制台脚本
// 使用方法：复制整个脚本到浏览器控制台运行

(async function() {
  console.log('='.repeat(80))
  console.log('启动待处理任务')
  console.log('='.repeat(80))
  
  // 获取 access_token
  const token = localStorage.getItem('access_token')
  if (!token) {
    console.error('❌ 未找到 access_token，请先登录')
    return
  }
  
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
  
  // 发票文件ID
  const invoiceFileId = 'a9e353a6-2bef-4918-8af2-18560eb96f5b'
  const invoiceNo = 'INV-20260205111510-5f22ea3b'
  
  try {
    // 1. 查找发票
    console.log('\n📋 步骤1: 查找发票...')
    let invoice = null
    
    // 方法1: 通过发票编号查找
    try {
      const response1 = await fetch(`/api/v1/invoices?invoice_no=${encodeURIComponent(invoiceNo)}&limit=1`, { headers })
      if (response1.ok) {
        const data1 = await response1.json()
        if (data1.data && data1.data.length > 0) {
          invoice = data1.data[0]
          console.log(`✅ 通过发票编号找到发票: ${invoice.id}`)
        }
      }
    } catch (e) {
      console.log('⚠️ 通过发票编号查找失败:', e.message)
    }
    
    // 方法2: 通过文件ID查找
    if (!invoice) {
      try {
        const filesResponse = await fetch('/api/v1/invoices/files/list?limit=1000', { headers })
        if (filesResponse.ok) {
          const filesData = await filesResponse.json()
          if (filesData.data && filesData.data.length > 0) {
            const file = filesData.data.find(f => f.id === invoiceFileId)
            if (file) {
              const invoiceResponse = await fetch(`/api/v1/invoices/${file.invoice_id}`, { headers })
              if (invoiceResponse.ok) {
                const invoiceData = await invoiceResponse.json()
                invoice = invoiceData.data
                console.log(`✅ 通过文件ID找到发票: ${invoice.id}`)
              }
            }
          }
        }
      } catch (e) {
        console.log('⚠️ 通过文件ID查找失败:', e.message)
      }
    }
    
    if (!invoice) {
      console.error('❌ 未找到发票')
      return
    }
    
    // 2. 获取待处理任务
    console.log(`\n📋 步骤2: 获取待处理任务...`)
    const tasksResponse = await fetch(`/api/v1/invoices/recognition-tasks?invoice_id=${invoice.id}&limit=100`, { headers })
    if (!tasksResponse.ok) {
      console.error(`❌ 获取任务列表失败: HTTP ${tasksResponse.status}`)
      return
    }
    
    const tasksData = await tasksResponse.json()
    const tasks = tasksData.data || []
    const pendingTasks = tasks.filter(t => t.status === 'pending')
    
    console.log(`✅ 找到 ${pendingTasks.length} 个待处理任务`)
    
    if (pendingTasks.length === 0) {
      console.log('✅ 没有待处理的任务')
      return
    }
    
    // 3. 启动所有待处理任务
    console.log(`\n📋 步骤3: 启动任务...`)
    const results = []
    
    for (const task of pendingTasks) {
      try {
        console.log(`\n启动任务: ${task.id} (${task.task_no || 'N/A'})`)
        const startResponse = await fetch(`/api/v1/invoices/recognition-tasks/${task.id}/start`, {
          method: 'POST',
          headers
        })
        
        const startData = await startResponse.json()
        
        if (startResponse.ok) {
          console.log(`✅ 任务启动成功`)
          results.push({ taskId: task.id, success: true, message: startData.message || '成功' })
        } else {
          console.log(`❌ 任务启动失败: ${startData.detail || startResponse.statusText}`)
          results.push({ taskId: task.id, success: false, message: startData.detail || startResponse.statusText })
        }
        
        // 等待一下再启动下一个任务
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (e) {
        console.log(`❌ 启动任务异常: ${e.message}`)
        results.push({ taskId: task.id, success: false, message: e.message })
      }
    }
    
    // 4. 等待几秒后检查状态
    console.log(`\n📋 步骤4: 等待5秒后检查任务状态...`)
    await new Promise(resolve => setTimeout(resolve, 5000))
    
    const statusResponse = await fetch(`/api/v1/invoices/recognition-tasks?invoice_id=${invoice.id}&limit=100`, { headers })
    if (statusResponse.ok) {
      const statusData = await statusResponse.json()
      const updatedTasks = statusData.data || []
      
      console.log(`\n📊 任务状态更新:`)
      updatedTasks.forEach(task => {
        const result = results.find(r => r.taskId === task.id)
        if (result) {
          console.log(`\n任务 ${task.task_no || task.id}:`)
          console.log(`   状态: ${task.status}`)
          console.log(`   Request ID: ${task.request_id || '❌ 未调用 Dify API'}`)
          console.log(`   错误: ${task.error_message || 'N/A'}`)
        }
      })
    }
    
    // 5. 总结
    console.log(`\n${'='.repeat(80)}`)
    console.log('📊 启动结果总结:')
    const successCount = results.filter(r => r.success).length
    const failedCount = results.filter(r => !r.success).length
    
    console.log(`   成功启动: ${successCount}`)
    console.log(`   启动失败: ${failedCount}`)
    
    if (failedCount > 0) {
      console.log(`\n失败的任务:`)
      results.filter(r => !r.success).forEach(r => {
        console.log(`   - ${r.taskId}: ${r.message}`)
      })
    }
    
    console.log('='.repeat(80))
    
  } catch (error) {
    console.error('❌ 启动任务过程中发生错误:', error)
    console.error('错误详情:', error.stack)
  }
})()

