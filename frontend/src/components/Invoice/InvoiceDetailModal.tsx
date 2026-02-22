import { Box, Text, Flex, VStack, Badge, Grid, GridItem, Table } from "@chakra-ui/react"
import { FiX, FiSave } from "react-icons/fi"
import { useState, useEffect, useMemo, useRef } from "react"
import { Button } from "@/components/ui/button"
import useCustomToast from '@/hooks/useCustomToast'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

ModuleRegistry.registerModules([AllCommunityModule])

interface InvoiceDetailModalProps {
  isOpen: boolean
  onClose: () => void
  invoiceId: string
}

interface InvoiceDetail {
  id: string
  invoice_no: string
  invoice_type: string
  invoice_date: string | null
  amount: number | null
  tax_amount: number | null
  total_amount: number | null
  currency: string | null
  supplier_name: string | null
  supplier_tax_no: string | null
  buyer_name: string | null
  buyer_tax_no: string | null
  recognition_accuracy: number | null
  recognition_status: string
  review_status: string
  create_time: string
  error_code?: string | null
  error_message?: string | null
  template_version_id?: string | null
  field_defs_snapshot?: Record<string, any> | null
  template_version?: string | null
  template_name?: string | null
  model_name?: string | null
  normalized_fields?: Record<string, any> | null
}

interface SchemaValidationStatus {
  is_valid: boolean
  errors: Array<{
    field: string
    message: string
    expected?: string
    actual?: string
  }>
  warnings: Array<{
    message: string
  }>
  validation_time: string
  schema_name?: string
  schema_version?: string
  repair_attempted: boolean
  repair_success: boolean
  fallback_type?: string
}

interface InvoiceFileInfo {
  id: string
  file_name: string
  file_path: string
  file_hash: string
  mime_type: string
  file_type: string
}

interface InvoiceItem {
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


const InvoiceDetailModal = ({ isOpen, onClose, invoiceId }: InvoiceDetailModalProps) => {
  const [invoiceDetail, setInvoiceDetail] = useState<InvoiceDetail | null>(null)
  const [invoiceItems, setInvoiceItems] = useState<InvoiceItem[]>([])
  const [editableItems, setEditableItems] = useState<InvoiceItem[]>([])
  const [invoiceFile, setInvoiceFile] = useState<InvoiceFileInfo | null>(null)
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null)
  const [schemaValidationStatus, setSchemaValidationStatus] = useState<SchemaValidationStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const gridRef = useRef<AgGridReact>(null)
  const { showErrorToast, showSuccessToast } = useCustomToast()

  useEffect(() => {
    if (isOpen && invoiceId) {
      fetchInvoiceDetail()
      fetchInvoiceItems()
      fetchInvoiceFile()
      fetchSchemaValidationStatus()
    }
    // 清理函数
    return () => {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl)
        setPdfBlobUrl(null)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, invoiceId])

  const fetchInvoiceDetail = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      console.log('🔍 DEBUG: 前端发送请求，invoiceId:', invoiceId, '类型:', typeof invoiceId)

      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/${invoiceId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data) {
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/afa6fab0-66d4-4499-8b93-5ccac21fa749',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'InvoiceDetailModal.tsx:140',message:'API响应接收',data:{invoiceId,status:response.status,hasNormalizedFields:!!response.data.normalized_fields,normalizedFieldsType:typeof response.data.normalized_fields,normalizedFieldsIsNull:response.data.normalized_fields === null,normalizedFieldsIsUndefined:response.data.normalized_fields === undefined,normalizedFieldsKeys:response.data.normalized_fields ? Object.keys(response.data.normalized_fields) : null,normalizedFieldsItemsLength:response.data.normalized_fields?.items?.length || 0},timestamp:Date.now(),runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
        console.log('=== 发票详情 API 响应 ===')
        console.log('响应状态:', response.status)
        console.log('响应头:', response.headers)
        console.log('响应数据:', response.data)
        console.log('模型名称:', response.data.model_name)
        console.log('normalized_fields:', response.data.normalized_fields)
        console.log('normalized_fields 类型:', typeof response.data.normalized_fields)
        console.log('normalized_fields 是否为 null:', response.data.normalized_fields === null)
        console.log('normalized_fields 是否为 undefined:', response.data.normalized_fields === undefined)
        console.log('normalized_fields.items:', response.data.normalized_fields?.items)
        console.log('完整响应 JSON 字符串:', JSON.stringify(response.data, null, 2))
        console.log('=== 响应结束 ===')
        setInvoiceDetail(response.data)
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/afa6fab0-66d4-4499-8b93-5ccac21fa749',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'InvoiceDetailModal.tsx:153',message:'设置invoiceDetail状态',data:{hasNormalizedFields:!!response.data.normalized_fields,normalizedFieldsType:typeof response.data.normalized_fields},timestamp:Date.now(),runId:'run1',hypothesisId:'E'})}).catch(()=>{});
        // #endregion
      }
    } catch (error: any) {
      console.error('获取发票详情失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '获取发票详情失败'
      showErrorToast(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchInvoiceItems = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/${invoiceId}/items`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data && response.data.data) {
        setInvoiceItems(response.data.data)
        setEditableItems(response.data.data.map((item: any) => ({ ...item })))
      }
    } catch (error: any) {
      console.error('获取发票行项目失败:', error)
      // 如果接口不存在或没有数据，不显示错误，只显示空列表
      setInvoiceItems([])
    }
  }

  const fetchInvoiceFile = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/${invoiceId}/file`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data) {
        setInvoiceFile(response.data)
        // 如果是PDF文件，获取文件内容并创建blob URL
        if (response.data.mime_type === 'application/pdf') {
          await fetchPdfAsBlob()
        }
      }
    } catch (error: any) {
      console.error('获取发票文件信息失败:', error)
      // 如果接口不存在或没有数据，不显示错误
      setInvoiceFile(null)
    }
  }

  const fetchSchemaValidationStatus = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''

      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/${invoiceId}/schema-validation-status`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data) {
        setSchemaValidationStatus(response.data)
      }
    } catch (error: any) {
      console.error('获取Schema验证状态失败:', error)
      // 如果接口不存在或没有数据，不显示错误
      setSchemaValidationStatus(null)
    }
  }

  const fetchPdfAsBlob = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      // 使用fetch获取文件，可以设置Authorization header
      const response = await fetch(
        `${apiBaseUrl}/api/v1/invoices/${invoiceId}/file/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const blob = await response.blob()
        const blobUrl = URL.createObjectURL(blob)
        setPdfBlobUrl(blobUrl)
      }
    } catch (error: any) {
      console.error('获取PDF文件失败:', error)
    }
  }

  // 获取文件URL（优先使用blob URL，否则使用直接URL）
  const getFileUrl = () => {
    if (invoiceFile?.mime_type === 'application/pdf' && pdfBlobUrl) {
      return pdfBlobUrl
    }
    if (!invoiceFile) return null
    // 使用相对路径，让Vite proxy处理，避免跨域问题
    const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
    return `${apiBaseUrl}/api/v1/invoices/${invoiceId}/file/download`
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'gray', text: '待审核' },
      approved: { color: 'green', text: '已通过' },
      rejected: { color: 'red', text: '已拒绝' },
      completed: { color: 'blue', text: '已完成' },
      processing: { color: 'yellow', text: '处理中' },
      failed: { color: 'red', text: '失败' }
    }
    const statusInfo = statusMap[status] || { color: 'gray', text: status || '未知' }
    return <Badge colorScheme={statusInfo.color}>{statusInfo.text}</Badge>
  }

  // 将货币代码转换为货币符号
  const getCurrencySymbol = (currency: string | null | undefined): string => {
    if (!currency) return ''
    const currencyMap: Record<string, string> = {
      'CNY': '¥',
      'USD': '$',
      'EUR': '€',
      'GBP': '£',
      'JPY': '¥',
      'HKD': 'HK$',
      'SGD': 'S$',
      'AUD': 'A$',
      'CAD': 'C$',
      'CHF': 'CHF',
      'KRW': '₩',
      'RUB': '₽',
      'INR': '₹',
      'BRL': 'R$',
      'MXN': 'Mex$',
      'ZAR': 'R'
    }
    return currencyMap[currency.toUpperCase()] || currency
  }

  // 格式化金额显示
  const formatAmount = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '-'
    const symbol = getCurrencySymbol(invoiceDetail?.currency)
    return `${symbol}${value.toFixed(2)}`
  }

  const handleSaveItems = async () => {
    if (!invoiceId) return

    setIsSaving(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      // 获取所有行数据
      const allRowData: InvoiceItem[] = []
      if (gridRef.current && gridRef.current.api) {
        gridRef.current.api.forEachNode((node) => {
          if (node.data) {
            allRowData.push(node.data)
          }
        })
      }

      // 转换为更新格式
      const itemsToUpdate = allRowData.map(item => ({
        line_no: item.line_no,
        name: item.name || null,
        part_no: item.part_no || null,
        supplier_partno: item.supplier_partno || null,
        unit: item.unit || null,
        quantity: item.quantity !== null && item.quantity !== undefined ? parseFloat(item.quantity.toString()) : null,
        unit_price: item.unit_price !== null && item.unit_price !== undefined ? parseFloat(item.unit_price.toString()) : null,
        amount: item.amount !== null && item.amount !== undefined ? parseFloat(item.amount.toString()) : null,
        tax_rate: item.tax_rate || null,
        tax_amount: item.tax_amount !== null && item.tax_amount !== undefined ? parseFloat(item.tax_amount.toString()) : null,
      }))

      const response = await axios.put(
        `${apiBaseUrl}/api/v1/invoices/${invoiceId}/items`,
        { items: itemsToUpdate },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.data) {
        showSuccessToast('行项目保存成功')
        // 重新加载数据
        await fetchInvoiceItems()
      }
    } catch (error: any) {
      console.error('保存行项目失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '保存失败'
      showErrorToast(errorMessage)
    } finally {
      setIsSaving(false)
    }
  }

  // 判断是否是尺寸/孔位类检验记录大模型
  const isDimensionInspectionModel = useMemo(() => {
    const modelName = invoiceDetail?.model_name
    const isMatch = modelName === '尺寸/孔位类检验记录大模型'
    console.log('模型名称检查:', { modelName, isMatch, invoiceDetail })
    return isMatch
  }, [invoiceDetail?.model_name, invoiceDetail])
  
  // 判断是否是检验记录表（根据模型名称或数据字段）
  const isInspectionRecord = useMemo(() => {
    // 如果模型名称是"尺寸/孔位类检验记录大模型"，直接返回 true
    if (isDimensionInspectionModel) {
      console.log('isInspectionRecord: 通过模型名称判断为 true')
      return true
    }
    // 否则根据数据字段判断
    if (!invoiceDetail?.normalized_fields) {
      console.log('isInspectionRecord: normalized_fields 不存在，返回 false')
      return false
    }
    const fields = invoiceDetail.normalized_fields
    // 检查是否是检验记录表的关键字段
    const hasInspectionFields = (
      (fields.doc_type && (
        fields.doc_type === '检验记录表' ||
        fields.doc_type === '零件检验记录表' ||
        fields.doc_type === 'dimension_inspection' ||
        (typeof fields.doc_type === 'string' && (
          fields.doc_type.includes('检验记录表') ||
          fields.doc_type.includes('inspection') ||
          fields.doc_type.includes('检验')
        ))
      )) ||
      fields.drawing_no !== undefined ||
      fields.part_name !== undefined ||
      fields.part_no !== undefined ||
      fields.form_title !== undefined ||
      fields.inspector_name !== undefined
    )
    // 检查 items 数组中的第一个元素是否包含检验记录表的字段
    const hasInspectionItems = (
      Array.isArray(fields.items) && 
      fields.items.length > 0 && 
      fields.items[0] && 
      typeof fields.items[0] === 'object' &&
      ('inspection_item' in fields.items[0] || 'spec_requirement' in fields.items[0] || 'judgement' in fields.items[0])
    )
    const result = hasInspectionFields || hasInspectionItems
    console.log('isInspectionRecord: 通过数据字段判断为', result, { 
      hasInspectionFields, 
      hasInspectionItems, 
      fields,
      items: fields.items,
      firstItem: fields.items?.[0]
    })
    return result
  }, [invoiceDetail?.normalized_fields, isDimensionInspectionModel])

  // 检验记录表的列定义（根据模型类型动态调整）
  const inspectionItemColumnDefs: ColDef[] = useMemo(() => {
    // 如果是尺寸/孔位类检验记录大模型，使用特定的列定义
    if (isDimensionInspectionModel) {
      return [
        { 
          headerName: '检验项', 
          field: 'inspection_item', 
          width: 200,
          editable: false
        },
        { 
          headerName: '要求', 
          field: 'spec_requirement', 
          width: 200,
          editable: false
        },
        { 
          headerName: '实际值', 
          field: 'actual_value', 
          width: 150,
          editable: false
        },
        { 
          headerName: '值范围', 
          field: 'range_value', 
          width: 150,
          editable: false
        },
        { 
          headerName: '检验结果', 
          field: 'judgement', 
          width: 120,
          editable: false,
          cellRenderer: (params: any) => {
            const value = params.value
            if (value === 'pass') {
              return '<span style="color: green; font-weight: bold;">合格</span>'
            } else if (value === 'fail') {
              return '<span style="color: red; font-weight: bold;">不合格</span>'
            } else if (value === 'unknown') {
              return '<span style="color: gray;">未知</span>'
            }
            return value || '-'
          }
        },
        { 
          headerName: '备注', 
          field: 'notes', 
          width: 200,
          editable: false
        }
      ]
    }
    // 其他检验记录表使用默认列定义
    return [
      { headerName: '序号', field: 'item_no', width: 80, editable: false },
      { 
        headerName: '检验项目', 
        field: 'inspection_item', 
        width: 200,
        editable: false
      },
      { 
        headerName: '规格要求', 
        field: 'spec_requirement', 
        width: 200,
        editable: false
      },
      { 
        headerName: '实测值', 
        field: 'actual_value', 
        width: 150,
        editable: false
      },
      { 
        headerName: '判定', 
        field: 'judgement', 
        width: 100,
        editable: false,
        cellRenderer: (params: any) => {
          const value = params.value
          if (value === 'pass') {
            return '<span style="color: green; font-weight: bold;">合格</span>'
          } else if (value === 'fail') {
            return '<span style="color: red; font-weight: bold;">不合格</span>'
          }
          return value || '-'
        }
      },
      { 
        headerName: '备注', 
        field: 'notes', 
        width: 200,
        editable: false
      }
    ]
  }, [isDimensionInspectionModel])

  const itemColumnDefs: ColDef[] = useMemo(() => {
    const currencySymbol = getCurrencySymbol(invoiceDetail?.currency)
    return [
      { headerName: '行号', field: 'line_no', width: 80, editable: false },
      { 
        headerName: '零件号', 
        field: 'part_no', 
        width: 120,
        editable: true,
        cellEditor: 'agTextCellEditor'
      },
      { 
        headerName: '供应商零件号', 
        field: 'supplier_partno', 
        width: 150,
        editable: true,
        cellEditor: 'agTextCellEditor'
      },
      { 
        headerName: '单位', 
        field: 'unit', 
        width: 80,
        editable: true,
        cellEditor: 'agTextCellEditor'
      },
      {
        headerName: '数量',
        field: 'quantity',
        width: 100,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          precision: 2,
          min: 0
        },
        cellRenderer: (params: any) => {
          if (params.value !== null && params.value !== undefined) {
            return typeof params.value === 'number' ? params.value.toFixed(2) : params.value
          }
          return '-'
        }
      },
      {
        headerName: '单价',
        field: 'unit_price',
        width: 120,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          precision: 2,
          min: 0
        },
        cellRenderer: (params: any) => {
          if (params.value === null || params.value === undefined) return '-'
          const value = typeof params.value === 'number' ? params.value : parseFloat(params.value)
          return isNaN(value) ? '-' : `${currencySymbol}${value.toFixed(2)}`
        }
      },
      {
        headerName: '金额',
        field: 'amount',
        width: 120,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          precision: 2,
          min: 0
        },
        cellRenderer: (params: any) => {
          if (params.value === null || params.value === undefined) return '-'
          const value = typeof params.value === 'number' ? params.value : parseFloat(params.value)
          return isNaN(value) ? '-' : `${currencySymbol}${value.toFixed(2)}`
        }
      },
      { 
        headerName: '税率', 
        field: 'tax_rate', 
        width: 100,
        editable: true,
        cellEditor: 'agTextCellEditor'
      },
      {
        headerName: '税额',
        field: 'tax_amount',
        width: 120,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          precision: 2,
          min: 0
        },
        cellRenderer: (params: any) => {
          if (params.value === null || params.value === undefined) return '-'
          const value = typeof params.value === 'number' ? params.value : parseFloat(params.value)
          return isNaN(value) ? '-' : `${currencySymbol}${value.toFixed(2)}`
        }
      }
    ]
  }, [invoiceDetail?.currency])

  if (!isOpen) return null

  return (
    <Box
      position="fixed"
      top={0}
      left={0}
      right={0}
      bottom={0}
      bg="blackAlpha.600"
      zIndex={1000}
      display="flex"
      alignItems="center"
      justifyContent="center"
      onClick={onClose}
    >
      <Box
        bg="white"
        borderRadius="md"
        p={6}
        maxW="95vw"
        maxH="95vh"
        w="1600px"
        overflow="hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 */}
        <Flex justify="space-between" align="center" mb={4}>
          <Text fontSize="xl" fontWeight="bold">
            {isDimensionInspectionModel ? '详情' : '发票详情'}
          </Text>
          <Button
            size="sm"
            variant="ghost"
            onClick={onClose}
          >
            <FiX />
          </Button>
        </Flex>

        {isLoading ? (
          <Text>加载中...</Text>
        ) : invoiceDetail ? (
          <Flex gap={6} h="calc(95vh - 100px)" overflow="hidden">
            {/* 左侧：PDF预览 */}
            <Box flex="1" minW="0" border="1px solid" borderColor="gray.200" borderRadius="md" overflow="hidden">
              <Box bg="gray.50" p={2} borderBottom="1px solid" borderColor="gray.200">
                <Text fontSize="sm" fontWeight="medium" color="gray.700">
                  PDF预览 {invoiceFile?.file_name && `- ${invoiceFile.file_name}`}
                </Text>
              </Box>
              <Box h="calc(100% - 40px)" overflow="auto" position="relative">
                {invoiceFile && invoiceFile.mime_type === 'application/pdf' ? (
                  pdfBlobUrl ? (
                    <iframe
                      src={pdfBlobUrl}
                      style={{
                        width: '100%',
                        height: '100%',
                        border: 'none'
                      }}
                      title="PDF预览"
                    />
                  ) : (
                    <Box display="flex" alignItems="center" justifyContent="center" h="100%">
                      <Text color="gray.500">正在加载PDF...</Text>
                    </Box>
                  )
                ) : invoiceFile && invoiceFile.mime_type?.startsWith('image/') ? (
                  <Box display="flex" alignItems="center" justifyContent="center" h="100%" bg="gray.50">
                    <img
                      src={getFileUrl() || ''}
                      alt={invoiceFile.file_name}
                      style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain'
                      }}
                      onError={(e) => {
                        console.error('图片加载失败')
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                  </Box>
                ) : invoiceFile ? (
                  <Box display="flex" alignItems="center" justifyContent="center" h="100%" p={4}>
                    <VStack gap={4}>
                      <Text color="gray.500" textAlign="center">
                        不支持预览此文件类型: {invoiceFile.mime_type}
                      </Text>
                      <Button
                        onClick={() => {
                          const url = getFileUrl()
                          if (url) {
                            window.open(url, '_blank', 'noopener,noreferrer')
                          }
                        }}
                        colorScheme="blue"
                      >
                        下载文件
                      </Button>
                    </VStack>
                  </Box>
                ) : (
                  <Box display="flex" alignItems="center" justifyContent="center" h="100%">
                    <Text color="gray.500">暂无文件</Text>
                  </Box>
                )}
              </Box>
            </Box>

            {/* 右侧：发票详情 */}
            <Box flex="1" minW="0" overflow="auto">
              <VStack align="stretch" gap={6}>
                {/* 发票抬头信息 / 检验记录表头信息 */}
                <Box>
              <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                {isInspectionRecord ? '检验记录表信息' : '发票抬头信息'}
              </Text>
              {(() => {
                // #region agent log
                fetch('http://127.0.0.1:7244/ingest/afa6fab0-66d4-4499-8b93-5ccac21fa749',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'InvoiceDetailModal.tsx:776',message:'渲染头信息检查',data:{isInspectionRecord,isDimensionInspectionModel,hasNormalizedFields:!!invoiceDetail.normalized_fields,normalizedFieldsType:typeof invoiceDetail.normalized_fields,normalizedFieldsIsNull:invoiceDetail.normalized_fields === null,normalizedFieldsKeys:invoiceDetail.normalized_fields ? Object.keys(invoiceDetail.normalized_fields) : null,normalizedFieldsItemsLength:invoiceDetail.normalized_fields?.items?.length || 0},timestamp:Date.now(),runId:'run1',hypothesisId:'E'})}).catch(()=>{});
                // #endregion
                console.log('渲染头信息检查:', {
                  isInspectionRecord,
                  isDimensionInspectionModel,
                  hasNormalizedFields: !!invoiceDetail.normalized_fields,
                  normalizedFields: invoiceDetail.normalized_fields
                })
                return null
              })()}
              <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                {isInspectionRecord ? (
                  <>
                    {/* 如果是尺寸/孔位类检验记录大模型，显示特定字段 */}
                    {isDimensionInspectionModel ? (
                      <>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">票据编号</Text>
                          <Text fontWeight="medium">{invoiceDetail.invoice_no || '-'}</Text>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">日期</Text>
                          <Text fontWeight="medium">
                            {invoiceDetail.normalized_fields?.date 
                              ? (typeof invoiceDetail.normalized_fields.date === 'string' 
                                  ? invoiceDetail.normalized_fields.date 
                                  : new Date(invoiceDetail.normalized_fields.date).toLocaleDateString('zh-CN'))
                              : '-'}
                          </Text>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">识别状态</Text>
                          <Flex direction="column" gap={2}>
                            {getStatusBadge(invoiceDetail.recognition_status)}
                            {invoiceDetail.recognition_status === 'failed' && (invoiceDetail.error_code || invoiceDetail.error_message) && (
                              <Box bg="red.50" p={2} borderRadius="sm" border="1px" borderColor="red.200">
                                <Text fontSize="xs" fontWeight="medium" color="red.700" mb={1}>
                                  失败原因:
                                </Text>
                                {invoiceDetail.error_code && (
                                  <Text fontSize="xs" color="red.600" mb={0.5}>
                                    错误代码: {invoiceDetail.error_code}
                                  </Text>
                                )}
                                {invoiceDetail.error_message && (
                                  <Text fontSize="xs" color="red.600">
                                    {invoiceDetail.error_message}
                                  </Text>
                                )}
                              </Box>
                            )}
                          </Flex>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">审核状态</Text>
                          <Badge colorScheme={invoiceDetail.review_status === 'approved' ? 'green' : invoiceDetail.review_status === 'rejected' ? 'red' : 'gray'}>
                            {invoiceDetail.review_status === 'approved' ? '成功' : invoiceDetail.review_status === 'rejected' ? '失败' : '待审核'}
                          </Badge>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">审核员</Text>
                          <Text fontWeight="medium">{invoiceDetail.normalized_fields?.inspector_name || '-'}</Text>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">文档类型</Text>
                          <Text fontWeight="medium">{invoiceDetail.normalized_fields?.doc_type || '-'}</Text>
                        </GridItem>
                      </>
                    ) : (
                      <>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">日期</Text>
                          <Text fontWeight="medium">
                            {invoiceDetail.normalized_fields?.date 
                              ? new Date(invoiceDetail.normalized_fields.date).toLocaleDateString('zh-CN') 
                              : '-'}
                          </Text>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">文档类型</Text>
                          <Text fontWeight="medium">{invoiceDetail.normalized_fields?.doc_type || '-'}</Text>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">图号</Text>
                          <Text fontWeight="medium">{invoiceDetail.normalized_fields?.drawing_no || '-'}</Text>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">表单标题</Text>
                          <Text fontWeight="medium">{invoiceDetail.normalized_fields?.form_title || '-'}</Text>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">检验员</Text>
                          <Text fontWeight="medium">{invoiceDetail.normalized_fields?.inspector_name || '-'}</Text>
                        </GridItem>
                        {invoiceDetail.normalized_fields?.part_name && (
                          <GridItem>
                            <Text fontSize="sm" color="gray.600">零件名称</Text>
                            <Text fontWeight="medium">{invoiceDetail.normalized_fields.part_name}</Text>
                          </GridItem>
                        )}
                        {invoiceDetail.normalized_fields?.part_no && (
                          <GridItem>
                            <Text fontSize="sm" color="gray.600">零件号</Text>
                            <Text fontWeight="medium">{invoiceDetail.normalized_fields.part_no}</Text>
                          </GridItem>
                        )}
                        {invoiceDetail.normalized_fields?.overall_result && (
                          <GridItem>
                            <Text fontSize="sm" color="gray.600">总体结果</Text>
                            <Badge colorScheme={invoiceDetail.normalized_fields.overall_result === 'pass' ? 'green' : 'red'}>
                              {invoiceDetail.normalized_fields.overall_result === 'pass' ? '合格' : '不合格'}
                            </Badge>
                          </GridItem>
                        )}
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">识别状态</Text>
                          <Flex direction="column" gap={2}>
                            {getStatusBadge(invoiceDetail.recognition_status)}
                            {invoiceDetail.recognition_status === 'failed' && (invoiceDetail.error_code || invoiceDetail.error_message) && (
                              <Box bg="red.50" p={2} borderRadius="sm" border="1px" borderColor="red.200">
                                <Text fontSize="xs" fontWeight="medium" color="red.700" mb={1}>
                                  失败原因:
                                </Text>
                                {invoiceDetail.error_code && (
                                  <Text fontSize="xs" color="red.600" mb={0.5}>
                                    错误代码: {invoiceDetail.error_code}
                                  </Text>
                                )}
                                {invoiceDetail.error_message && (
                                  <Text fontSize="xs" color="red.600">
                                    {invoiceDetail.error_message}
                                  </Text>
                                )}
                              </Box>
                            )}
                          </Flex>
                        </GridItem>
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">审核状态</Text>
                          {getStatusBadge(invoiceDetail.review_status)}
                        </GridItem>
                      </>
                    )}
                  </>
                ) : (
                  <>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">票据编号</Text>
                      <Text fontWeight="medium">{invoiceDetail.invoice_no || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">票据类型</Text>
                      <Text fontWeight="medium">{invoiceDetail.invoice_type || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">开票日期</Text>
                      <Text fontWeight="medium">
                        {invoiceDetail.invoice_date ? new Date(invoiceDetail.invoice_date).toLocaleDateString('zh-CN') : '-'}
                      </Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">识别状态</Text>
                      <Flex direction="column" gap={2}>
                        {getStatusBadge(invoiceDetail.recognition_status)}
                        {invoiceDetail.recognition_status === 'failed' && (invoiceDetail.error_code || invoiceDetail.error_message) && (
                          <Box bg="red.50" p={2} borderRadius="sm" border="1px" borderColor="red.200">
                            <Text fontSize="xs" fontWeight="medium" color="red.700" mb={1}>
                              失败原因:
                            </Text>
                            {invoiceDetail.error_code && (
                              <Text fontSize="xs" color="red.600" mb={0.5}>
                                错误代码: {invoiceDetail.error_code}
                              </Text>
                            )}
                            {invoiceDetail.error_message && (
                              <Text fontSize="xs" color="red.600">
                                {invoiceDetail.error_message}
                              </Text>
                            )}
                          </Box>
                        )}
                      </Flex>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">审核状态</Text>
                      {getStatusBadge(invoiceDetail.review_status)}
                    </GridItem>
                    <GridItem colSpan={2}>
                      <Text fontSize="sm" color="gray.600">供应商名称</Text>
                      <Text fontWeight="medium">{invoiceDetail.supplier_name || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">供应商税号</Text>
                      <Text fontWeight="medium">{invoiceDetail.supplier_tax_no || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">采购方名称</Text>
                      <Text fontWeight="medium">{invoiceDetail.buyer_name || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">采购方税号</Text>
                      <Text fontWeight="medium">{invoiceDetail.buyer_tax_no || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">金额（不含税）</Text>
                      <Text fontWeight="medium" color="blue.600">
                        {formatAmount(invoiceDetail.amount)}
                      </Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">税额</Text>
                      <Text fontWeight="medium" color="blue.600">
                        {formatAmount(invoiceDetail.tax_amount)}
                      </Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">合计金额</Text>
                      <Text fontWeight="bold" fontSize="md" color="red.600">
                        {formatAmount(invoiceDetail.total_amount)}
                      </Text>
                    </GridItem>
                  </>
                )}
                <GridItem>
                  <Text fontSize="sm" color="gray.600">创建时间</Text>
                  <Text fontWeight="medium">
                    {invoiceDetail.create_time ? new Date(invoiceDetail.create_time).toLocaleString('zh-CN') : '-'}
                  </Text>
                </GridItem>
              </Grid>
            </Box>

            {/* 模板信息 */}
            {invoiceDetail.template_name && (
              <Box>
                <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                  识别模板信息
                </Text>
                <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                  <GridItem>
                    <Text fontSize="sm" color="gray.600">模板名称</Text>
                    <Text fontWeight="medium">{invoiceDetail.template_name}</Text>
                  </GridItem>
                  {invoiceDetail.template_version && (
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">模板版本</Text>
                      <Text fontWeight="medium">{invoiceDetail.template_version}</Text>
                    </GridItem>
                  )}
                </Grid>
              </Box>
            )}

            {/* 动态字段渲染 - 兼容发票和检验记录表两种类型 */}
            {false && invoiceDetail.normalized_fields && (() => {
              // 字段名称映射（用于显示友好的中文名称）
              const fieldNameMap: Record<string, string> = {
                // 发票字段
                invoice_no: '发票号码',
                invoice_type: '发票类型',
                invoice_date: '开票日期',
                amount: '金额（不含税）',
                tax_amount: '税额',
                total_amount: '合计金额',
                currency: '币种',
                supplier_name: '供应商名称',
                supplier_tax_no: '供应商税号',
                buyer_name: '采购方名称',
                buyer_tax_no: '采购方税号',
                remark: '备注',
                // 检验记录表字段
                doc_type: '文档类型',
                form_title: '表单标题',
                drawing_no: '图号',
                part_name: '零件名称',
                part_no: '零件号',
                date: '日期',
                inspector_name: '检验员',
                overall_result: '总体结果',
                remarks: '备注',
                // 不显示 items，因为它在行项目部分单独显示
              }
              
              let fields: any[] = []
              
              // 如果有 field_defs_snapshot，优先使用它（发票类型通常有这个）
              if (invoiceDetail.field_defs_snapshot) {
                let fieldsArray: any[] = []
                
                if (Array.isArray(invoiceDetail.field_defs_snapshot)) {
                  fieldsArray = invoiceDetail.field_defs_snapshot
                } else if (typeof invoiceDetail.field_defs_snapshot === 'object') {
                  fieldsArray = Object.entries(invoiceDetail.field_defs_snapshot)
                    .map(([fieldKey, fieldDef]: [string, any]) => ({
                      field_key: fieldKey,
                      field_name: fieldDef.field_name || fieldKey,
                      data_type: fieldDef.data_type || 'string',
                      is_required: fieldDef.is_required || false,
                      description: fieldDef.description || '',
                      sort_order: fieldDef.sort_order || 0
                    }))
                }
                
                fields = fieldsArray
                  .map((fieldDef: any) => ({
                    field_key: fieldDef.field_key || '',
                    field_name: fieldDef.field_name || fieldDef.field_key || '',
                    data_type: fieldDef.data_type || 'string',
                    is_required: fieldDef.is_required || false,
                    description: fieldDef.description || '',
                    sort_order: fieldDef.sort_order || 0
                  }))
                  .sort((a, b) => a.sort_order - b.sort_order)
              } else {
                // 如果没有 field_defs_snapshot，直接从 normalized_fields 生成字段列表（检验记录表通常没有 field_defs_snapshot）
                fields = Object.keys(invoiceDetail.normalized_fields)
                  .filter(key => {
                    // 排除 items 数组（它在行项目部分单独显示）
                    if (key === 'items') return false
                    // 排除已经是 null 或 undefined 的字段
                    const value = invoiceDetail.normalized_fields![key]
                    return value !== null && value !== undefined
                  })
                  .map((key, index) => ({
                    field_key: key,
                    field_name: fieldNameMap[key] || key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
                    data_type: Array.isArray(invoiceDetail.normalized_fields![key]) ? 'array' : typeof invoiceDetail.normalized_fields![key],
                    is_required: false,
                    description: '',
                    sort_order: index
                  }))
              }
              
              // 过滤掉 items 字段（它在行项目部分单独显示）
              fields = fields.filter(field => field.field_key !== 'items')

              if (fields.length === 0) {
                return null
              }

              return (
                <Box>
                  <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                    {isInspectionRecord ? '检验记录表字段详情' : '识别字段详情'} ({fields.length} 个字段)
                  </Text>
                  <Box overflowX="auto" border="1px solid" borderColor="gray.200" borderRadius="md">
                    <Table.Root size="sm">
                      <Table.Header bg="gray.50">
                        <Table.Row>
                          <Table.ColumnHeader fontSize="sm" fontWeight="600" color="gray.700">字段名称</Table.ColumnHeader>
                          <Table.ColumnHeader fontSize="sm" fontWeight="600" color="gray.700">字段标识</Table.ColumnHeader>
                          <Table.ColumnHeader fontSize="sm" fontWeight="600" color="gray.700">字段值</Table.ColumnHeader>
                          <Table.ColumnHeader fontSize="sm" fontWeight="600" color="gray.700">数据类型</Table.ColumnHeader>
                          {invoiceDetail.field_defs_snapshot && (
                            <Table.ColumnHeader fontSize="sm" fontWeight="600" color="gray.700">是否必填</Table.ColumnHeader>
                          )}
                        </Table.Row>
                      </Table.Header>
                      <Table.Body>
                        {fields.map((field) => {
                          const fieldValue = invoiceDetail.normalized_fields?.[field.field_key]
                          const displayValue = (() => {
                            if (fieldValue === null || fieldValue === undefined) return null
                            if (typeof fieldValue === 'object' && !Array.isArray(fieldValue)) {
                              return JSON.stringify(fieldValue, null, 2)
                            }
                            if (Array.isArray(fieldValue)) {
                              return `[数组，${fieldValue.length} 项]`
                            }
                            return String(fieldValue)
                          })()
                          
                          return (
                            <Table.Row key={field.field_key} _hover={{ bg: 'gray.50' }}>
                              <Table.Cell>
                                <VStack align="start" gap={1}>
                                  <Text fontWeight="medium" fontSize="sm">{field.field_name}</Text>
                                  {field.description && (
                                    <Text fontSize="xs" color="gray.500">{field.description}</Text>
                                  )}
                                </VStack>
                              </Table.Cell>
                              <Table.Cell>
                                <Text fontFamily="mono" fontSize="xs" color="gray.600">{field.field_key}</Text>
                              </Table.Cell>
                              <Table.Cell>
                                {displayValue !== null ? (
                                  <Text fontSize="sm" whiteSpace="pre-wrap" wordBreak="break-word">
                                    {displayValue}
                                  </Text>
                                ) : (
                                  <Text color="gray.400" fontStyle="italic" fontSize="sm">-</Text>
                                )}
                              </Table.Cell>
                              <Table.Cell>
                                <Badge colorScheme="blue" fontSize="xs">{field.data_type}</Badge>
                              </Table.Cell>
                              {invoiceDetail.field_defs_snapshot && (
                                <Table.Cell>
                                  {field.is_required ? (
                                    <Badge colorScheme="red" fontSize="xs">必填</Badge>
                                  ) : (
                                    <Badge colorScheme="gray" fontSize="xs">可选</Badge>
                                  )}
                                </Table.Cell>
                              )}
                            </Table.Row>
                          )
                        })}
                      </Table.Body>
                    </Table.Root>
                  </Box>
                </Box>
              )
            })()}

            {/* Schema验证状态 */}
            {false && schemaValidationStatus && (
              <Box>
                <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                  Schema验证状态
                </Text>
                <Box p={4} borderRadius="md" bg={schemaValidationStatus.is_valid ? 'green.50' : 'red.50'} border="1px" borderColor={schemaValidationStatus.is_valid ? 'green.200' : 'red.200'}>
                  <Flex align="center" gap={3} mb={3}>
                    <Badge colorScheme={schemaValidationStatus.is_valid ? 'green' : 'red'} fontSize="sm">
                      {schemaValidationStatus.is_valid ? '验证通过' : '验证失败'}
                    </Badge>
                    {schemaValidationStatus.schema_name && (
                      <Text fontSize="sm" color="gray.600">
                        Schema: {schemaValidationStatus.schema_name} (v{schemaValidationStatus.schema_version})
                      </Text>
                    )}
                  </Flex>

                  {schemaValidationStatus.errors.length > 0 && (
                    <Box mb={3}>
                      <Text fontSize="sm" fontWeight="medium" color="red.700" mb={2}>
                        验证错误 ({schemaValidationStatus.errors.length}个):
                      </Text>
                      <VStack align="stretch" gap={1}>
                        {schemaValidationStatus.errors.slice(0, 5).map((error, index) => (
                          <Text key={index} fontSize="xs" color="red.600" bg="red.25" p={2} borderRadius="sm">
                            • {error.field}: {error.message}
                          </Text>
                        ))}
                        {schemaValidationStatus.errors.length > 5 && (
                          <Text fontSize="xs" color="red.600" fontStyle="italic">
                            ... 还有 {schemaValidationStatus.errors.length - 5} 个错误
                          </Text>
                        )}
                      </VStack>
                    </Box>
                  )}

                  {schemaValidationStatus.warnings.length > 0 && (
                    <Box mb={3}>
                      <Text fontSize="sm" fontWeight="medium" color="orange.700" mb={2}>
                        验证警告 ({schemaValidationStatus.warnings.length}个):
                      </Text>
                      <VStack align="stretch" gap={1}>
                        {schemaValidationStatus.warnings.slice(0, 3).map((warning, index) => (
                          <Text key={index} fontSize="xs" color="orange.600" bg="orange.25" p={2} borderRadius="sm">
                            • {warning.message}
                          </Text>
                        ))}
                        {schemaValidationStatus.warnings.length > 3 && (
                          <Text fontSize="xs" color="orange.600" fontStyle="italic">
                            ... 还有 {schemaValidationStatus.warnings.length - 3} 个警告
                          </Text>
                        )}
                      </VStack>
                    </Box>
                  )}

                  {schemaValidationStatus.repair_attempted && (
                    <Box mb={3}>
                      <Text fontSize="sm" fontWeight="medium" color="blue.700" mb={2}>
                        自动修复: {schemaValidationStatus.repair_success ? '成功' : '失败'}
                      </Text>
                      {schemaValidationStatus.fallback_type && (
                        <Text fontSize="xs" color="blue.600">
                          降级策略: {schemaValidationStatus.fallback_type}
                        </Text>
                      )}
                    </Box>
                  )}

                  <Text fontSize="xs" color="gray.500">
                    验证时间: {new Date(schemaValidationStatus.validation_time).toLocaleString('zh-CN')}
                  </Text>
                </Box>
              </Box>
            )}

            <Box borderTop="1px solid" borderColor="gray.200" my={4} />

            {/* 发票行项目信息 / 检验记录表项目信息 */}
            <Box>
              <Flex justify="space-between" align="center" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                <Text fontSize="lg" fontWeight="bold">
                  {isInspectionRecord 
                    ? `检验项目信息 ${invoiceDetail.normalized_fields?.items?.length ? `(共 ${invoiceDetail.normalized_fields.items.length} 项)` : ''}`
                    : `发票行项目信息 ${invoiceItems.length > 0 ? `(共 ${invoiceItems.length} 项)` : ''}`}
                </Text>
                {!isInspectionRecord && invoiceItems.length > 0 && (
                  <Button
                    colorScheme="blue"
                    size="sm"
                    onClick={handleSaveItems}
                    loading={isSaving}
                  >
                    <FiSave style={{ marginRight: '8px' }} />
                    保存行项目
                  </Button>
                )}
              </Flex>
              {isInspectionRecord ? (
                // 显示检验记录表的 items 数组
                (() => {
                  // #region agent log
                  const items = invoiceDetail.normalized_fields?.items || []
                  fetch('http://127.0.0.1:7244/ingest/afa6fab0-66d4-4499-8b93-5ccac21fa749',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'InvoiceDetailModal.tsx:1290',message:'渲染检验项目表格',data:{isInspectionRecord,hasNormalizedFields:!!invoiceDetail.normalized_fields,itemsLength:items.length,itemsType:typeof items,itemsIsArray:Array.isArray(items),firstItem:items[0] || null},timestamp:Date.now(),runId:'run1',hypothesisId:'E'})}).catch(()=>{});
                  // #endregion
                  return (
                    <Box className="ag-theme-alpine" style={{ height: '400px', width: '100%' }}>
                      <AgGridReact
                        theme="legacy"
                        rowData={items}
                        columnDefs={inspectionItemColumnDefs}
                        defaultColDef={{
                          resizable: true,
                          sortable: true
                        }}
                      />
                    </Box>
                  )
                })()
              ) : editableItems.length > 0 ? (
                // 显示发票行项目
                <Box className="ag-theme-alpine" style={{ height: '400px', width: '100%' }}>
                  <AgGridReact
                    theme="legacy"
                    ref={gridRef}
                    rowData={editableItems}
                    columnDefs={itemColumnDefs}
                    defaultColDef={{
                      resizable: true,
                      sortable: true
                    }}
                    stopEditingWhenCellsLoseFocus={true}
                  />
                </Box>
              ) : (
                <Text color="gray.500" textAlign="center" py={8}>
                  暂无行项目数据
                </Text>
              )}
            </Box>

                {/* 关闭按钮 */}
                <Flex justify="flex-end" mt={4}>
                  <Button onClick={onClose}>
                    关闭
                  </Button>
                </Flex>
              </VStack>
            </Box>
          </Flex>
        ) : (
          <Text>加载失败</Text>
        )}
      </Box>
    </Box>
  )
}

export default InvoiceDetailModal

