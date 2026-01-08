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
 * 导出发票数据为 Excel
 */
export function exportInvoicesToExcel(
  invoices: InvoiceExportData[],
  invoiceItems: InvoiceItemExportData[]
) {
  if (invoices.length === 0) {
    throw new Error('没有数据可导出')
  }

  // 创建行数据：每个行项目一行，发票信息重复
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

