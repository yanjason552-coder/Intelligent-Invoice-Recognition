/**
 * 发票数据导出为 Excel 工具
 * 用于导出发票和行项目数据为 Excel 格式
 */

import * as XLSX from 'xlsx'

interface InvoiceExportData {
  id: string
  invoice_no: string
  invoice_type: string
  invoice_date: string | null
  amount: number | null
  tax_amount: number | null
  total_amount: number | null
  currency?: string | null
  supplier_name: string | null
  supplier_tax_no: string | null
  buyer_name: string | null
  buyer_tax_no: string | null
  purchase_order?: string | null
  doc_type?: string | null
  model_name?: string | null
  normalized_fields?: Record<string, any> | null
  [key: string]: any
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
  // 尺寸检验记录相关字段
  inspection_item?: string | null
  spec_requirement?: string | null
  actual_value?: string | null
  judgement?: string | null
  notes?: string | null
  [key: string]: any
}

interface ExcelRowData {
  'COMPANY CODE': string
  'VENDORNO': string
  'VENDOR NAME': string
  'BILLNO': string
  'BILL DATE': string
  'PURCHASE ORDER': string
  'GRAND TOTAL': number | string
  'VAT': number | string
  'ITEM': number | string
  'MATERIAL DESCRIPTION': string
  'QUANTITY': number | string
  'UNIT PRICE': number | string
  'AMOUNT': number | string
}

interface DimensionInspectionRowData {
  '票据编号': string
  '审核员': string
  '日期': string
  '文档类型': string
  '检验项': string
  '要求': string
  '实际值': string
  '值范围': string
  '检验结果': string
  '备注': string
}

/**
 * 格式化日期
 */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return ''
    // 格式化为 YYYY-MM-DD
    return date.toISOString().split('T')[0]
  } catch {
    return ''
  }
}

/**
 * 格式化数字
 */
function formatNumber(value: number | null | undefined): number | string {
  if (value === null || value === undefined) return ''
  return value
}

/**
 * 判断是否为尺寸检验记录
 */
function isDimensionInspectionRecord(invoice: InvoiceExportData): boolean {
  // 检查主字段
  if (invoice.doc_type === 'dimension_inspection') {
    return true
  }

  // 检查normalized_fields中的doc_type
  const normalizedFields = (invoice as any).normalized_fields
  if (normalizedFields?.doc_type === 'dimension_inspection') {
    return true
  }

  // 检查模型名称是否为尺寸/孔位类检验记录大模型
  if ((invoice as any).model_name === '尺寸/孔位类检验记录大模型') {
    return true
  }

  return false
}

/**
 * 导出尺寸检验记录为 Excel
 */
function exportDimensionInspectionToExcel(
  invoices: InvoiceExportData[],
  invoiceItems: InvoiceItemExportData[]
) {
  if (invoices.length === 0) {
    throw new Error('没有数据可导出')
  }

  const rows: DimensionInspectionRowData[] = []

  invoices.forEach((invoice) => {
    // 获取normalized_fields中的数据
    const normalizedFields = invoice.normalized_fields
    const inspectorName = normalizedFields?.inspector_name || ''
    const invoiceDate = normalizedFields?.date || invoice.invoice_date
    const items = normalizedFields?.items || []

    // 如果有normalized_fields中的items，使用这些数据
    if (items && Array.isArray(items) && items.length > 0) {
      items.forEach((item: any) => {
        rows.push({
          '票据编号': invoice.invoice_no || '',
          '审核员': inspectorName,
          '日期': formatDate(invoiceDate),
          '文档类型': 'dimension_inspection',
          '检验项': item.inspection_item || item.name || '',
          '要求': item.spec_requirement || item.requirement || '',
          '实际值': item.actual_value || item.value || '',
          '值范围': item.range_value || item.range || '',
          '检验结果': item.judgement === 'pass' ? '合格' : item.judgement === 'fail' ? '不合格' : item.judgement || '',
          '备注': item.notes || ''
        })
      })
    } else {
      // 备用：从invoiceItems中获取数据
      const invoiceItemsData = invoiceItems.filter(
        (item) => item.invoice_id === invoice.id
      )

      if (invoiceItemsData.length === 0) {
        // 如果都没有数据，至少创建一行抬头信息
        rows.push({
          '票据编号': invoice.invoice_no || '',
          '审核员': inspectorName,
          '日期': formatDate(invoiceDate),
          '文档类型': 'dimension_inspection',
          '检验项': '',
          '要求': '',
          '实际值': '',
          '值范围': '',
          '检验结果': '',
          '备注': ''
        })
      } else {
        // 为每个行项目创建一行
        invoiceItemsData.forEach((item) => {
          rows.push({
            '票据编号': invoice.invoice_no || '',
            '审核员': inspectorName,
            '日期': formatDate(invoiceDate),
            '文档类型': 'dimension_inspection',
            '检验项': item.inspection_item || item.name || '',
            '要求': item.spec_requirement || '',
            '实际值': item.actual_value || '',
            '值范围': '',
            '检验结果': item.judgement === 'pass' ? '合格' : item.judgement === 'fail' ? '不合格' : item.judgement || '',
            '备注': item.notes || ''
          })
        })
      }
    }
  })

  // 创建工作簿
  const wb = XLSX.utils.book_new()

  // 创建工作表
  const ws = XLSX.utils.json_to_sheet(rows)

  // 设置列宽
  const colWidths = [
    { wch: 20 }, // 票据编号
    { wch: 15 }, // 审核员
    { wch: 12 }, // 日期
    { wch: 15 }, // 文档类型
    { wch: 30 }, // 检验项
    { wch: 25 }, // 要求
    { wch: 15 }, // 实际值
    { wch: 15 }, // 值范围
    { wch: 12 }, // 检验结果
    { wch: 30 }  // 备注
  ]
  ws['!cols'] = colWidths

  // 添加工作表到工作簿
  XLSX.utils.book_append_sheet(wb, ws, 'Dimension Inspection')

  // 生成文件名
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const filename = `Dimension_Inspection_${timestamp}.xlsx`

  // 导出文件
  XLSX.writeFile(wb, filename)
}

/**
 * 导出发票数据为 Excel
 */
export function exportInvoicesToExcel(
  invoices: InvoiceExportData[],
  invoiceItems: InvoiceItemExportData[]
) {
  if (invoices.length === 0) {
    throw new Error('没有数据可导出')
  }

  // 检查是否所有发票都是尺寸检验记录
  const allDimensionInspection = invoices.every(invoice => isDimensionInspectionRecord(invoice))

  // 如果是尺寸检验记录，使用专门的导出格式
  if (allDimensionInspection) {
    exportDimensionInspectionToExcel(invoices, invoiceItems)
    return
  }

  // 原有的发票导出逻辑
  const rows: ExcelRowData[] = []

  invoices.forEach((invoice) => {
    // 获取该发票的所有行项目
    const items = invoiceItems.filter(
      (item) => item.invoice_id === invoice.id
    )

    // 如果没有行项目，至少创建一行发票信息
    if (items.length === 0) {
      rows.push({
        'COMPANY CODE': '', // 暂时留空，可能需要从其他字段获取
        'VENDORNO': invoice.supplier_tax_no || '',
        'VENDOR NAME': invoice.supplier_name || '',
        'BILLNO': invoice.invoice_no || '',
        'BILL DATE': formatDate(invoice.invoice_date),
        'PURCHASE ORDER': invoice.purchase_order || '',
        'GRAND TOTAL': formatNumber(invoice.total_amount),
        'VAT': formatNumber(invoice.tax_amount),
        'ITEM': '',
        'MATERIAL DESCRIPTION': '',
        'QUANTITY': '',
        'UNIT PRICE': '',
        'AMOUNT': ''
      })
    } else {
      // 为每个行项目创建一行
      items.forEach((item) => {
        rows.push({
          'COMPANY CODE': '', // 暂时留空，可能需要从其他字段获取
          'VENDORNO': invoice.supplier_tax_no || '',
          'VENDOR NAME': invoice.supplier_name || '',
          'BILLNO': invoice.invoice_no || '',
          'BILL DATE': formatDate(invoice.invoice_date),
          'PURCHASE ORDER': invoice.purchase_order || '',
          'GRAND TOTAL': formatNumber(invoice.total_amount),
          'VAT': formatNumber(invoice.tax_amount),
          'ITEM': item.line_no || '',
          'MATERIAL DESCRIPTION': item.name || '',
          'QUANTITY': formatNumber(item.quantity),
          'UNIT PRICE': formatNumber(item.unit_price),
          'AMOUNT': formatNumber(item.amount)
        })
      })
    }
  })

  // 创建工作簿
  const wb = XLSX.utils.book_new()

  // 创建工作表
  const ws = XLSX.utils.json_to_sheet(rows)

  // 设置列宽
  const colWidths = [
    { wch: 15 }, // COMPANY CODE
    { wch: 15 }, // VENDORNO
    { wch: 30 }, // VENDOR NAME
    { wch: 20 }, // BILLNO
    { wch: 12 }, // BILL DATE
    { wch: 20 }, // PURCHASE ORDER
    { wch: 15 }, // GRAND TOTAL
    { wch: 12 }, // VAT
    { wch: 8 },  // ITEM
    { wch: 40 }, // MATERIAL DESCRIPTION
    { wch: 12 }, // QUANTITY
    { wch: 15 }, // UNIT PRICE
    { wch: 15 }  // AMOUNT
  ]
  ws['!cols'] = colWidths

  // 添加工作表到工作簿
  XLSX.utils.book_append_sheet(wb, ws, 'Invoice Data')

  // 生成文件名
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const filename = `Invoice_Export_${timestamp}.xlsx`

  // 导出文件
  XLSX.writeFile(wb, filename)
}

