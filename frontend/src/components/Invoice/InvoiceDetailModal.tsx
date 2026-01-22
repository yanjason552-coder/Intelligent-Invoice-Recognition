import { Box, Text, Flex, VStack, Badge, Grid, GridItem, HStack } from "@chakra-ui/react"
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

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/${invoiceId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data) {
        setInvoiceDetail(response.data)
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

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
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

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
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

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
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
    const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
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

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
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
            发票详情
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
                    <Text color="gray.500" textAlign="center">
                      不支持预览此文件类型: {invoiceFile.mime_type}
                      <br />
                      <a 
                        href={getFileUrl() || ''} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        style={{ color: 'blue', textDecoration: 'underline', marginTop: '8px', display: 'inline-block' }}
                      >
                        点击下载
                      </a>
                    </Text>
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
                {/* 发票抬头信息 */}
                <Box>
              <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                发票抬头信息
              </Text>
              <Grid templateColumns="repeat(2, 1fr)" gap={4}>
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
                  {getStatusBadge(invoiceDetail.recognition_status)}
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
                <GridItem>
                  <Text fontSize="sm" color="gray.600">创建时间</Text>
                  <Text fontWeight="medium">
                    {invoiceDetail.create_time ? new Date(invoiceDetail.create_time).toLocaleString('zh-CN') : '-'}
                  </Text>
                </GridItem>
              </Grid>
            </Box>

            {/* Schema验证状态 */}
            {schemaValidationStatus && (
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

            {/* 发票行项目信息 */}
            <Box>
              <Flex justify="space-between" align="center" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                <Text fontSize="lg" fontWeight="bold">
                  发票行项目信息 {invoiceItems.length > 0 && `(共 ${invoiceItems.length} 项)`}
                </Text>
                {invoiceItems.length > 0 && (
                  <Button
                    leftIcon={<FiSave />}
                    colorScheme="blue"
                    size="sm"
                    onClick={handleSaveItems}
                    loading={isSaving}
                  >
                    保存行项目
                  </Button>
                )}
              </Flex>
              {editableItems.length > 0 ? (
                <Box className="ag-theme-alpine" style={{ height: '400px', width: '100%' }}>
                  <AgGridReact
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

