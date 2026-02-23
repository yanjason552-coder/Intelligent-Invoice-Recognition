import { Box, Text, Flex, Grid, Input, Badge, HStack } from "@chakra-ui/react"
import { FiSearch, FiRefreshCw, FiEye, FiDownload } from "react-icons/fi"
import { useState, useMemo, useEffect, useRef } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { Button } from "@/components/ui/button"
import useCustomToast from '@/hooks/useCustomToast'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"
import InvoiceDetailModal from './InvoiceDetailModal'
import { exportInvoicesToExcel } from '@/utils/invoiceExcelExport'

ModuleRegistry.registerModules([AllCommunityModule])

interface InvoiceRecord {
  id: string
  invoiceNo: string
  invoiceType: string
  invoiceDate: string | null
  amount: number | null
  taxAmount: number | null
  totalAmount: number | null
  supplier: string | null
  buyer: string | null
  status: string
  recognitionStatus: string
  reviewStatus: string
  createTime: string
  updateTime: string
  companyCode: string | null
  modelName: string | null
  templateName: string | null
  templateVersion: string | null
}

interface InvoiceQueryListProps {
  reviewStatus?: 'pending' | 'approved' | 'rejected' | null // 审核状态过滤
  title?: string // 自定义标题
}

const InvoiceQueryList = ({ reviewStatus, title }: InvoiceQueryListProps = {}) => {
  const [tableData, setTableData] = useState<InvoiceRecord[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [totalCount, setTotalCount] = useState(0)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null)
  const [selectedRows, setSelectedRows] = useState<InvoiceRecord[]>([]) // 选中的发票列表
  const gridRef = useRef<AgGridReact>(null) // AG Grid引用
  const [modelNameFilter, setModelNameFilter] = useState<string>('')
  const [templateNameFilter, setTemplateNameFilter] = useState<string>('')
  const [modelOptions, setModelOptions] = useState<string[]>([])
  const [templateOptions, setTemplateOptions] = useState<string[]>([])
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const fetchData = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      // 构建查询参数
      const params: any = {
        skip: 0,
        limit: 100
      }
      
      // 如果指定了审核状态，添加到查询参数
      if (reviewStatus) {
        params.review_status = reviewStatus
      }
      
      // 添加模型和模板筛选参数
      if (modelNameFilter) {
        params.model_name = modelNameFilter
      }
      if (templateNameFilter) {
        params.template_name = templateNameFilter
      }
      
      // 解析搜索关键词
      if (searchKeyword) {
        const keyword = searchKeyword.trim()
        // 优先作为票据编号查询
        params.invoice_no = keyword
        // 如果包含中文，同时作为供应商或采购方名称查询（后端会使用OR逻辑）
        // 注意：后端API使用AND关系，所以这里只设置invoice_no，供应商和采购方在前端过滤
      }

      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/query`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          params
        }
      )

      if (response.data && response.data.data) {
        // 转换数据格式
        const transformedData: InvoiceRecord[] = response.data.data.map((item: any) => ({
          id: item.id,
          invoiceNo: item.invoice_no || '',
          invoiceType: item.invoice_type || '未知',
          invoiceDate: item.invoice_date ? new Date(item.invoice_date).toLocaleDateString('zh-CN') : null,
          amount: item.amount,
          taxAmount: item.tax_amount,
          totalAmount: item.total_amount,
          supplier: item.supplier_name || '',
          buyer: item.buyer_name || '',
          status: item.review_status || 'pending',
          recognitionStatus: item.recognition_status || 'pending',
          reviewStatus: item.review_status || 'pending',
          createTime: item.create_time ? new Date(item.create_time).toLocaleString('zh-CN') : '',
          updateTime: item.update_time ? new Date(item.update_time).toLocaleString('zh-CN') : '',
          companyCode: item.company_code || null,
          modelName: item.model_name || null,
          templateName: item.template_name || null,
          templateVersion: item.template_version || null
        }))
        
        setTableData(transformedData)
        setTotalCount(response.data.count || 0)
        showSuccessToast(`加载成功，共 ${transformedData.length} 条记录`)
      } else {
        setTableData([])
        setTotalCount(0)
      }
    } catch (error: any) {
      console.error('加载数据失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '加载数据失败'
      showErrorToast(errorMessage)
      setTableData([])
      setTotalCount(0)
    } finally {
      setIsLoading(false)
    }
  }

  // 加载模型和模板选项
  const loadFilterOptions = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      // 并行加载模型和模板选项
      const [modelsResponse, templatesResponse] = await Promise.all([
        axios.get(`${apiBaseUrl}/api/v1/invoices/filter-options/models`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        axios.get(`${apiBaseUrl}/api/v1/invoices/filter-options/templates`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ])

      if (modelsResponse.data && modelsResponse.data.data) {
        setModelOptions(modelsResponse.data.data)
      }
      if (templatesResponse.data && templatesResponse.data.data) {
        setTemplateOptions(templatesResponse.data.data)
      }
    } catch (error: any) {
      console.error('加载筛选选项失败:', error)
      // 不显示错误提示，避免干扰用户体验
    }
  }

  // 组件加载时自动获取数据
  useEffect(() => {
    fetchData()
    loadFilterOptions()
  }, [])

  // 当筛选条件改变时，重新获取数据
  useEffect(() => {
    if (modelNameFilter || templateNameFilter) {
      fetchData()
    }
  }, [modelNameFilter, templateNameFilter])

  const handleExport = async (invoiceIds?: string[]) => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      // 确定要导出的发票ID列表
      let idsToExport: string[] = []
      if (invoiceIds && invoiceIds.length > 0) {
        // 如果指定了发票ID列表，使用指定的ID
        idsToExport = invoiceIds
      } else {
        // 否则导出当前表格中的所有数据（考虑搜索过滤）
        let dataToExport = filteredData
        idsToExport = dataToExport.map(item => item.id)
      }

      if (idsToExport.length === 0) {
        showErrorToast('没有数据可导出')
        return
      }

      // 批量获取发票详情和行项目
      const invoicePromises = idsToExport.map(id =>
        axios.get(`${apiBaseUrl}/api/v1/invoices/${id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      )

      const itemPromises = idsToExport.map(id =>
        axios.get(`${apiBaseUrl}/api/v1/invoices/${id}/items`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => ({ data: { data: [] } })) // 如果没有行项目，返回空数组
      )

      const [invoiceResponses, itemResponses] = await Promise.all([
        Promise.all(invoicePromises),
        Promise.all(itemPromises)
      ])

      // 提取发票数据（purchase_order 暂时留空，后续可以从识别结果中获取）
      const invoices = invoiceResponses.map(res => ({
        ...res.data,
        purchase_order: '' // 暂时留空，后续可以从识别结果中提取
      }))
      
      // 提取行项目数据并展平
      const allItems: any[] = []
      itemResponses.forEach((res, index) => {
        if (res.data && res.data.data && res.data.data.length > 0) {
          const items = res.data.data.map((item: any) => ({
            invoice_id: idsToExport[index],
            invoice_no: invoices[index]?.invoice_no || '',
            ...item
          }))
          allItems.push(...items)
        }
      })

      // 导出为 Excel
      exportInvoicesToExcel(invoices, allItems)
      showSuccessToast(`成功导出 ${invoices.length} 条发票数据`)
    } catch (error: any) {
      console.error('导出失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '导出失败'
      showErrorToast(errorMessage)
    } finally {
      setIsLoading(false)
    }
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


  const columnDefs: ColDef[] = [
    {
      headerName: '',
      field: 'select',
      width: 50,
      checkboxSelection: true,
      headerCheckboxSelection: true,
      pinned: 'left',
      lockPosition: true,
      sortable: false,
      filter: false
    },
    {
      headerName: '票据编号',
      field: 'invoiceNo',
      width: 150
    },
    { headerName: '公司代码', field: 'companyCode', width: 120 },
    { headerName: '模型名称', field: 'modelName', width: 150 },
    { headerName: '模板名称', field: 'templateName', width: 150 },
    { headerName: '模板版本', field: 'templateVersion', width: 120 },
    { headerName: '票据类型', field: 'invoiceType', width: 150 },
    { headerName: '开票日期', field: 'invoiceDate', width: 120 },
    {
      headerName: '金额',
      field: 'amount',
      width: 120,
      cellRenderer: (params: any) => `¥${params.value?.toFixed(2) || '0.00'}`
    },
    {
      headerName: '税额',
      field: 'taxAmount',
      width: 120,
      cellRenderer: (params: any) => `¥${params.value?.toFixed(2) || '0.00'}`
    },
    {
      headerName: '合计',
      field: 'totalAmount',
      width: 120,
      cellRenderer: (params: any) => `¥${params.value?.toFixed(2) || '0.00'}`
    },
    { headerName: '供应商', field: 'supplier', width: 150 },
    { headerName: '采购方', field: 'buyer', width: 150 },
    {
      headerName: '状态',
      field: 'status',
      width: 100,
      cellRenderer: (params: any) => getStatusBadge(params.value)
    },
    { headerName: '创建时间', field: 'createTime', width: 180 },
    {
      headerName: '操作',
      width: 150,
      cellRenderer: (params: any) => (
        <HStack gap={2}>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setSelectedInvoiceId(params.data.id)
              setIsDetailModalOpen(true)
            }}
          >
            <FiEye />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleExport([params.data.id])}
          >
            <FiDownload />
          </Button>
        </HStack>
      )
    }
  ]

  const filteredData = useMemo(() => {
    if (!searchKeyword) return tableData
    const keyword = searchKeyword.toLowerCase()
    return tableData.filter(item =>
      item.invoiceNo.toLowerCase().includes(keyword) ||
      (item.supplier && item.supplier.toLowerCase().includes(keyword)) ||
      (item.buyer && item.buyer.toLowerCase().includes(keyword)) ||
      (item.companyCode && item.companyCode.toLowerCase().includes(keyword))
    )
  }, [tableData, searchKeyword])

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">
          {title || '票据查询'} {totalCount > 0 && `(共 ${totalCount} 条)`}
        </Text>
        <HStack gap={2}>
          {selectedRows.length > 0 && (
            <Text fontSize="sm" color="gray.600">
              已选择 {selectedRows.length} 条
            </Text>
          )}
          <Button
            onClick={() => handleExport(selectedRows.length > 0 ? selectedRows.map(row => row.id) : undefined)}
            loading={isLoading}
            colorPalette="green"
          >
            <FiDownload style={{ marginRight: '8px' }} />
            {selectedRows.length > 0 ? `导出选中(${selectedRows.length})` : '导出全部'}
          </Button>
        <Button
          onClick={fetchData}
          loading={isLoading}
        >
          <FiRefreshCw style={{ marginRight: '8px' }} />
          刷新
        </Button>
        </HStack>
      </Flex>

      <Grid templateColumns="repeat(4, 1fr)" gap={3} mb={4}>
        <Input
          placeholder="搜索票据编号、供应商或采购方..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && fetchData()}
        />
        <select
          value={modelNameFilter}
          onChange={(e) => setModelNameFilter(e.target.value)}
          style={{ 
            width: '100%', 
            padding: '8px', 
            border: '1px solid #e2e8f0', 
            borderRadius: '4px',
            fontSize: '14px'
          }}
        >
          <option value="">全部模型</option>
          {modelOptions.map(model => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
        <select
          value={templateNameFilter}
          onChange={(e) => setTemplateNameFilter(e.target.value)}
          style={{ 
            width: '100%', 
            padding: '8px', 
            border: '1px solid #e2e8f0', 
            borderRadius: '4px',
            fontSize: '14px'
          }}
        >
          <option value="">全部模板</option>
          {templateOptions.map(template => (
            <option key={template} value={template}>{template}</option>
          ))}
        </select>
        <Button onClick={fetchData}>
          <FiSearch style={{ marginRight: '8px' }} />
          搜索
        </Button>
      </Grid>

      <Box className="ag-theme-alpine" style={{ height: '600px', width: '100%', overflow: 'hidden' }}>
        <AgGridReact
          ref={gridRef}
          theme="legacy"
          rowData={filteredData}
          columnDefs={columnDefs}
          rowSelection="multiple"
          suppressRowClickSelection={true}
          defaultColDef={{
            resizable: true,
            sortable: true,
            filter: true
          }}
          onGridReady={() => fetchData()}
          onSelectionChanged={() => {
            if (gridRef.current?.api) {
              const selectedRows = gridRef.current.api.getSelectedRows() as InvoiceRecord[]
              setSelectedRows(selectedRows || [])
            }
          }}
        />
      </Box>

      {/* 发票详情弹窗 */}
      {selectedInvoiceId && (
        <InvoiceDetailModal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedInvoiceId(null)
          }}
          invoiceId={selectedInvoiceId}
        />
      )}
    </Box>
  )
}

export default InvoiceQueryList
