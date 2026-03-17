// 检查发票识别状态 - 浏览器控制台脚本
// 使用方法：复制整个脚本到浏览器控制台运行

(async function() {
  console.log('='.repeat(80))
  console.log('发票识别状态检查')
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
    
    console.log(`\n📄 发票信息:`)
    console.log(`   ID: ${invoice.id}`)
    console.log(`   发票编号: ${invoice.invoice_no || 'N/A'}`)
    console.log(`   识别状态: ${invoice.recognition_status || 'N/A'}`)
    console.log(`   文件ID: ${invoice.file_id || 'N/A'}`)
    
    // 2. 获取识别任务列表
    console.log(`\n📋 步骤2: 获取识别任务列表...`)
    const tasksResponse = await fetch(`/api/v1/invoices/recognition-tasks?invoice_id=${invoice.id}&limit=100`, { headers })
    if (!tasksResponse.ok) {
      console.error(`❌ 获取任务列表失败: HTTP ${tasksResponse.status}`)
      const errorText = await tasksResponse.text()
      console.error(`   错误详情: ${errorText}`)
      return
    }
    
    const tasksData = await tasksResponse.json()
    const tasks = tasksData.data || []
    console.log(`✅ 找到 ${tasks.length} 个任务`)
    
    if (tasks.length === 0) {
      console.log('⚠️ 没有找到识别任务')
      return
    }
    
    // 3. 显示任务详情
    console.log(`\n📋 步骤3: 任务详情:`)
    tasks.forEach((task, index) => {
      console.log(`\n任务 ${index + 1}:`)
      console.log(`   任务ID: ${task.id}`)
      console.log(`   任务编号: ${task.task_no || 'N/A'}`)
      console.log(`   状态: ${task.status || 'N/A'}`)
      console.log(`   创建时间: ${task.create_time || 'N/A'}`)
      console.log(`   开始时间: ${task.start_time || 'N/A'}`)
      console.log(`   结束时间: ${task.end_time || 'N/A'}`)
      console.log(`   Request ID: ${task.request_id || '❌ 未调用 Dify API'}`)
      console.log(`   Trace ID: ${task.trace_id || 'N/A'}`)
      console.log(`   错误代码: ${task.error_code || 'N/A'}`)
      console.log(`   错误消息: ${task.error_message || 'N/A'}`)
      
      if (task.params) {
        console.log(`   模型配置ID: ${task.params.model_config_id || 'N/A'}`)
        console.log(`   模板ID: ${task.params.template_id || 'N/A'}`)
      }
    })
    
    // 4. 获取识别结果
    console.log(`\n📋 步骤4: 获取识别结果...`)
    try {
      const resultResponse = await fetch(`/api/v1/invoices/${invoice.id}/recognition-result`, { headers })
      if (resultResponse.ok) {
        const resultData = await resultResponse.json()
        if (resultData.data) {
          const result = resultData.data
          console.log(`✅ 找到识别结果:`)
          console.log(`   结果ID: ${result.id}`)
          console.log(`   状态: ${result.status || 'N/A'}`)
          console.log(`   识别时间: ${result.recognition_time || 'N/A'}`)
          console.log(`   总字段数: ${result.total_fields || 'N/A'}`)
          console.log(`   识别字段数: ${result.recognized_fields || 'N/A'}`)
          console.log(`   准确率: ${result.accuracy ? (result.accuracy * 100).toFixed(2) + '%' : 'N/A'}`)
          
          if (result.normalized_fields) {
            console.log(`\n   标准化字段预览:`)
            const fields = result.normalized_fields
            if (typeof fields === 'object') {
              Object.keys(fields).slice(0, 10).forEach(key => {
                const value = fields[key]
                if (value !== null && value !== undefined && value !== '') {
                  console.log(`     ${key}: ${typeof value === 'object' ? JSON.stringify(value).substring(0, 50) + '...' : String(value).substring(0, 50)}`)
                }
              })
            }
          }
        } else {
          console.log('⚠️ 未找到识别结果')
        }
      } else {
        console.log(`⚠️ 获取识别结果失败: HTTP ${resultResponse.status}`)
      }
    } catch (e) {
      console.log(`⚠️ 获取识别结果异常: ${e.message}`)
    }
    
    // 5. 检查模型配置
    console.log(`\n📋 步骤5: 检查模型配置...`)
    const pendingTasks = tasks.filter(t => t.status === 'pending' || t.status === 'processing')
    if (pendingTasks.length > 0) {
      const firstTask = pendingTasks[0]
      if (firstTask.params && firstTask.params.model_config_id) {
        try {
          const configResponse = await fetch(`/api/v1/config/llm/${firstTask.params.model_config_id}`, { headers })
          if (configResponse.ok) {
            const configData = await configResponse.json()
            if (configData.data) {
              const config = configData.data
              console.log(`✅ 模型配置信息:`)
              console.log(`   配置名称: ${config.name || 'N/A'}`)
              console.log(`   应用类型: ${config.app_type || 'N/A'}`)
              console.log(`   API端点: ${config.endpoint || 'N/A'}`)
              console.log(`   工作流ID: ${config.workflow_id || '❌ 未设置'}`)
              console.log(`   应用ID: ${config.app_id || 'N/A'}`)
              console.log(`   是否启用: ${config.is_active ? '✅ 是' : '❌ 否'}`)
              
              if (config.app_type === 'workflow' && !config.workflow_id) {
                console.log(`\n⚠️ 警告: 工作流类型但未设置 workflow_id，这会导致 API 调用失败！`)
              }
            }
          }
        } catch (e) {
          console.log(`⚠️ 获取模型配置失败: ${e.message}`)
        }
      }
    }
    
    // 6. 总结
    console.log(`\n${'='.repeat(80)}`)
    console.log('📊 总结:')
    const successTasks = tasks.filter(t => t.status === 'success')
    const failedTasks = tasks.filter(t => t.status === 'failed')
    const pendingTasks2 = tasks.filter(t => t.status === 'pending')
    const processingTasks = tasks.filter(t => t.status === 'processing')
    
    console.log(`   总任务数: ${tasks.length}`)
    console.log(`   成功: ${successTasks.length}`)
    console.log(`   失败: ${failedTasks.length}`)
    console.log(`   待处理: ${pendingTasks2.length}`)
    console.log(`   处理中: ${processingTasks.length}`)
    
    if (processingTasks.length > 0) {
      const procTask = processingTasks[0]
      if (!procTask.request_id) {
        console.log(`\n⚠️ 处理中的任务没有 request_id，可能的原因:`)
        console.log(`   1. workflow_id 未设置或配置错误`)
        console.log(`   2. Dify API 调用失败（查看后端日志）`)
        console.log(`   3. 任务卡在某个步骤`)
      }
    }
    
    if (pendingTasks2.length > 0) {
      console.log(`\n💡 建议: 有 ${pendingTasks2.length} 个待处理任务，可以尝试启动它们`)
    }
    
    console.log('='.repeat(80))
    
  } catch (error) {
    console.error('❌ 检查过程中发生错误:', error)
    console.error('错误详情:', error.stack)
  }
})()

