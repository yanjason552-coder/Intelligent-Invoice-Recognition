/**
 * 发票数据导出工具
 * 用于导出发票和行项目数据为CSV格式
 */

interface InvoiceExportData {
  id: string
  invoice_no: string
  invoice_type: string
  invoice_date: string | null
  amount: number | null
  tax_amount: number | null
  total_amount: number | null
  supplier_name: string | null
  supplier_tax_no: string | null
  buyer_name: string | null
  buyer_tax_no: string | null
  recognition_accuracy: number | null
  recognition_status: string
  review_status: string
  create_time: string
}

interface InvoiceItemExportData {
  invoice_id: string
  invoice_no: string
  line_no: number
  name: string | null
  part_no: string | null
  supplier_partno: string | null
  unit: string | null
  quantity: number | null
  unit_price: number | null
  amount: number | null
  tax_rate: string | null
  tax_amount: number | null
}

/**
 * 将数据转换为CSV格式
 */
function convertToCSV(data: any[], headers: string[]): string {
  // CSV头部
  const csvHeaders = headers.join(',')
  
  // CSV数据行
  const csvRows = data.map(row => {
    return headers.map(header => {
      const value = row[header]
      if (value === null || value === undefined) {
        return ''
      }
      // 如果值包含逗号、引号或换行符，需要用引号包裹并转义引号
      const stringValue = String(value)
      if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
        return `"${stringValue.replace(/"/g, '""')}"`
      }
      return stringValue
    }).join(',')
  })
  
  return [csvHeaders, ...csvRows].join('\n')
}

/**
 * 下载CSV文件
 */
function downloadCSV(csvContent: string, filename: string) {
  // 添加BOM以支持Excel正确显示中文
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 导出发票数据为CSV
 */
export function exportInvoicesToCSV(
  invoices: InvoiceExportData[],
  invoiceItems: InvoiceItemExportData[],
  filename?: string
) {
  if (invoices.length === 0) {
    throw new Error('没有数据可导出')
  }

  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const defaultFilename = `发票数据_${timestamp}.csv`
  const finalFilename = filename || defaultFilename

  // 发票表数据
  const invoiceHeaders = [
    '发票ID',
    '票据编号',
    '票据类型',
    '开票日期',
    '金额（不含税）',
    '税额',
    '合计金额',
    '供应商名称',
    '供应商税号',
    '采购方名称',
    '采购方税号',
    '识别准确率',
    '识别状态',
    '审核状态',
    '创建时间'
  ]

  const invoiceData = invoices.map(inv => ({
    '发票ID': inv.id,
    '票据编号': inv.invoice_no || '',
    '票据类型': inv.invoice_type || '',
    '开票日期': inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString('zh-CN') : '',
    '金额（不含税）': inv.amount !== null && inv.amount !== undefined ? inv.amount.toFixed(2) : '',
    '税额': inv.tax_amount !== null && inv.tax_amount !== undefined ? inv.tax_amount.toFixed(2) : '',
    '合计金额': inv.total_amount !== null && inv.total_amount !== undefined ? inv.total_amount.toFixed(2) : '',
    '供应商名称': inv.supplier_name || '',
    '供应商税号': inv.supplier_tax_no || '',
    '采购方名称': inv.buyer_name || '',
    '采购方税号': inv.buyer_tax_no || '',
    '识别准确率': inv.recognition_accuracy !== null && inv.recognition_accuracy !== undefined 
      ? `${inv.recognition_accuracy.toFixed(2)}%` : '',
    '识别状态': inv.recognition_status || '',
    '审核状态': inv.review_status || '',
    '创建时间': inv.create_time ? new Date(inv.create_time).toLocaleString('zh-CN') : ''
  }))

  // 行项目表数据
  const itemHeaders = [
    '发票ID',
    '票据编号',
    '行号',
    '项目名称',
    '零件号',
    '供应商零件号',
    '单位',
    '数量',
    '单价',
    '金额',
    '税率',
    '税额'
  ]

  const itemData = invoiceItems.map(item => ({
    '发票ID': item.invoice_id || '',
    '票据编号': item.invoice_no || '',
    '行号': item.line_no || '',
    '项目名称': item.name || '',
    '零件号': item.part_no || '',
    '供应商零件号': item.supplier_partno || '',
    '单位': item.unit || '',
    '数量': item.quantity !== null && item.quantity !== undefined ? item.quantity.toFixed(2) : '',
    '单价': item.unit_price !== null && item.unit_price !== undefined ? item.unit_price.toFixed(2) : '',
    '金额': item.amount !== null && item.amount !== undefined ? item.amount.toFixed(2) : '',
    '税率': item.tax_rate || '',
    '税额': item.tax_amount !== null && item.tax_amount !== undefined ? item.tax_amount.toFixed(2) : ''
  }))

  // 生成CSV内容（发票数据和行项目数据合并，用空行分隔）
  const invoiceCSV = convertToCSV(invoiceData, invoiceHeaders)
  const itemCSV = convertToCSV(itemData, itemHeaders)
  
  // 合并两个CSV，用空行和标题分隔
  const combinedCSV = [
    '=== 发票抬头信息 ===',
    invoiceCSV,
    '',
    '=== 发票行项目信息 ===',
    itemCSV
  ].join('\n')

  // 下载文件
  downloadCSV(combinedCSV, finalFilename)
}

