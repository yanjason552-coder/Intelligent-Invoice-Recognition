// 检查发票识别结果前端显示 - 浏览器控制台脚本
// 使用方法：复制整个脚本到浏览器控制台运行

(async function() {
  console.log('='.repeat(80))
  console.log('检查发票识别结果前端显示')
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
  
  // 发票编号
  const invoiceNo = 'INV-20260205111510-5f22ea3b'
  
  try {
    // 1. 查找发票
    console.log('\n📋 步骤1: 查找发票...')
    const invoiceResponse = await fetch(`/api/v1/invoices?invoice_no=${encodeURIComponent(invoiceNo)}&limit=1`, { headers })
    if (!invoiceResponse.ok) {
      console.error(`❌ 获取发票失败: HTTP ${invoiceResponse.status}`)
      return
    }
    
    const invoiceData = await invoiceResponse.json()
    const invoices = invoiceData.data || []
    
    if (invoices.length === 0) {
      console.error('❌ 未找到发票')
      return
    }
    
    const invoice = invoices[0]
    console.log(`✅ 找到发票: ${invoice.id}`)
    console.log(`   发票编号: ${invoice.invoice_no}`)
    console.log(`   识别状态: ${invoice.recognition_status}`)
    
    // 2. 获取发票详情（包含 normalized_fields）
    console.log(`\n📋 步骤2: 获取发票详情...`)
    const detailResponse = await fetch(`/api/v1/invoices/${invoice.id}`, { headers })
    if (!detailResponse.ok) {
      console.error(`❌ 获取发票详情失败: HTTP ${detailResponse.status}`)
      return
    }
    
    const detailData = await detailResponse.json()
    const invoiceDetail = detailData.data || detailData
    
    console.log(`✅ 获取到发票详情`)
    console.log(`   发票ID: ${invoiceDetail.id}`)
    console.log(`   发票编号: ${invoiceDetail.invoice_no || 'N/A'}`)
    console.log(`   识别状态: ${invoiceDetail.recognition_status || 'N/A'}`)
    
    // 3. 检查 normalized_fields
    console.log(`\n📋 步骤3: 检查识别结果...`)
    if (invoiceDetail.normalized_fields) {
      const fields = invoiceDetail.normalized_fields
      console.log(`✅ normalized_fields 存在`)
      console.log(`   字段数量: ${Object.keys(fields).length}`)
      console.log(`   字段列表: ${Object.keys(fields).join(', ')}`)
      
      // 检查是否是检验记录表
      const isInspectionRecord = (
        (fields.doc_type && (
          fields.doc_type === '检验记录表' || 
          fields.doc_type === '零件检验记录表' ||
          fields.doc_type.includes('检验记录表')
        )) ||
        fields.drawing_no !== undefined ||
        fields.part_name !== undefined ||
        fields.part_no !== undefined ||
        fields.form_title !== undefined ||
        fields.inspector_name !== undefined ||
        (Array.isArray(fields.items) && fields.items.length > 0)
      )
      
      console.log(`\n📊 文档类型判断:`)
      console.log(`   doc_type: ${fields.doc_type || 'N/A'}`)
      console.log(`   是否是检验记录表: ${isInspectionRecord ? '✅ 是' : '❌ 否'}`)
      
      // 显示检验记录表字段
      if (isInspectionRecord) {
        console.log(`\n📋 检验记录表字段:`)
        console.log(`   doc_type: ${fields.doc_type || 'N/A'}`)
        console.log(`   form_title: ${fields.form_title || 'N/A'}`)
        console.log(`   drawing_no: ${fields.drawing_no || 'N/A'}`)
        console.log(`   part_name: ${fields.part_name || 'N/A'}`)
        console.log(`   part_no: ${fields.part_no || 'N/A'}`)
        console.log(`   date: ${fields.date || 'N/A'}`)
        console.log(`   inspector_name: ${fields.inspector_name || 'N/A'}`)
        console.log(`   overall_result: ${fields.overall_result || 'N/A'}`)
        console.log(`   remarks: ${fields.remarks || 'N/A'}`)
        
        if (Array.isArray(fields.items)) {
          console.log(`\n📋 检验项目 (items):`)
          console.log(`   项目数量: ${fields.items.length}`)
          fields.items.slice(0, 5).forEach((item, index) => {
            console.log(`\n   项目 ${index + 1}:`)
            console.log(`     序号: ${item.item_no || 'N/A'}`)
            console.log(`     检验项目: ${item.inspection_item || 'N/A'}`)
            console.log(`     规格要求: ${item.spec_requirement || 'N/A'}`)
            console.log(`     实测值: ${item.actual_value || 'N/A'}`)
            console.log(`     判定: ${item.judgement || 'N/A'}`)
          })
          if (fields.items.length > 5) {
            console.log(`   ... 还有 ${fields.items.length - 5} 个项目`)
          }
        } else {
          console.log(`\n⚠️ items 不是数组或不存在`)
        }
      } else {
        console.log(`\n📋 发票字段:`)
        console.log(`   invoice_no: ${fields.invoice_no || 'N/A'}`)
        console.log(`   invoice_type: ${fields.invoice_type || 'N/A'}`)
        console.log(`   amount: ${fields.amount || 'N/A'}`)
        console.log(`   tax_amount: ${fields.tax_amount || 'N/A'}`)
        console.log(`   total_amount: ${fields.total_amount || 'N/A'}`)
      }
      
      // 检查 field_defs_snapshot
      if (invoiceDetail.field_defs_snapshot) {
        console.log(`\n📋 field_defs_snapshot 存在:`)
        if (Array.isArray(invoiceDetail.field_defs_snapshot)) {
          console.log(`   类型: 数组，字段数: ${invoiceDetail.field_defs_snapshot.length}`)
        } else if (typeof invoiceDetail.field_defs_snapshot === 'object') {
          console.log(`   类型: 对象，字段数: ${Object.keys(invoiceDetail.field_defs_snapshot).length}`)
        }
      } else {
        console.log(`\n📋 field_defs_snapshot: ❌ 不存在（检验记录表通常没有）`)
      }
      
    } else {
      console.log(`❌ normalized_fields 不存在`)
    }
    
    // 4. 总结
    console.log(`\n${'='.repeat(80)}`)
    console.log('📊 前端显示检查总结:')
    console.log('='.repeat(80))
    
    if (invoiceDetail.normalized_fields) {
      const fields = invoiceDetail.normalized_fields
      const isInspectionRecord = (
        (fields.doc_type && (
          fields.doc_type === '检验记录表' || 
          fields.doc_type === '零件检验记录表' ||
          fields.doc_type.includes('检验记录表')
        )) ||
        fields.drawing_no !== undefined ||
        fields.part_name !== undefined ||
        fields.part_no !== undefined ||
        fields.form_title !== undefined ||
        fields.inspector_name !== undefined ||
        (Array.isArray(fields.items) && fields.items.length > 0)
      )
      
      console.log(`✅ 识别结果数据存在`)
      console.log(`✅ 文档类型: ${fields.doc_type || 'N/A'}`)
      console.log(`${isInspectionRecord ? '✅' : '❌'} 识别为检验记录表: ${isInspectionRecord ? '是' : '否'}`)
      
      if (isInspectionRecord) {
        console.log(`\n前端应该显示:`)
        console.log(`   1. 检验记录表信息（头信息）`)
        console.log(`      - 日期、文档类型、图号、表单标题、检验员、零件名称、零件号、总体结果`)
        console.log(`   2. 检验记录表字段详情（${Object.keys(fields).filter(k => k !== 'items').length} 个字段）`)
        console.log(`   3. 检验项目信息（${fields.items?.length || 0} 项）`)
      } else {
        console.log(`\n前端应该显示:`)
        console.log(`   1. 发票抬头信息`)
        console.log(`   2. 识别字段详情`)
        console.log(`   3. 发票行项目信息`)
      }
    } else {
      console.log(`❌ 识别结果数据不存在`)
    }
    
    console.log('='.repeat(80))
    
  } catch (error) {
    console.error('❌ 检查过程中发生错误:', error)
    console.error('错误详情:', error.stack)
  }
})()

