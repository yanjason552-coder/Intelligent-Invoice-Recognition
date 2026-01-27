import { Box, Text, Flex, Grid, Input, HStack } from "@chakra-ui/react"
import { FiSearch, FiRefreshCw, FiEye, FiCheck, FiX, FiDownload } from "react-icons/fi"
import { useState, useMemo, useEffect } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { Button } from "@/components/ui/button"
import useCustomToast from '@/hooks/useCustomToast'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"
import InvoiceDetailModal from './InvoiceDetailModal'
import { exportInvoicesToCSV } from '@/utils/invoiceExport'

// 调试日志（Debug Mode）
const DEBUG_ENDPOINT = 'http://127.0.0.1:7249/ingest/660b52e9-b46e-482a-a664-d0e8da08b78a'
const DEBUG_SESSION = 'debug-session'
const postDebugLog = (payload: {
  runId: string
  hypothesisId: string
  location: string
  message: string
  data?: Record<string, any>
}) => {
  // #region agent log
  fetch(DEBUG_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId: DEBUG_SESSION, timestamp: Date.now(), ...payload }),
  }).catch(() => {})
  // #endregion
}

ModuleRegistry.registerModules([AllCommunityModule])

interface ReviewTask {
  id: string
  invoiceNo: string
  invoiceType: string
  invoiceDate: string | null
  amount: number | null
  supplier: string | null
  submitTime: string
  submitter: string
  reviewStatus: 'pending' | 'approved' | 'rejected'
}

const InvoiceReviewPending = () => {
  const [tableData, setTableData] = useState<ReviewTask[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [totalCount, setTotalCount] = useState(0)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const fetchData = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H12',
        location: 'InvoiceReviewPending.tsx:fetchData',
        message: 'fetch pending reviews (via /invoices/query)',
        data: { apiBaseUrl, skip: 0, limit: 100, review_status: 'pending' }
      })
      
      const response = await axios.get(
        // 兼容性：复用 /invoices/query 的筛选能力，避免 /review/pending 在部分环境下出现“有pending但列表为空”的问题
        `${apiBaseUrl}/api/v1/invoices/query`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          params: {
            skip: 0,
            limit: 100,
            review_status: 'pending'
          }
        }
      )

      if (response.data && response.data.data) {
        // 转换数据格式
        const transformedData: ReviewTask[] = response.data.data.map((item: any) => ({
          id: item.id,
          invoiceNo: item.invoice_no || '',
          invoiceType: item.invoice_type || '未知',
          invoiceDate: item.invoice_date ? new Date(item.invoice_date).toLocaleDateString('zh-CN') : null,
          amount: item.total_amount || item.amount || null,
          supplier: item.supplier_name || '',
          submitTime: item.create_time ? new Date(item.create_time).toLocaleString('zh-CN') : '',
          submitter: '系统', // 后端没有返回提交人信息，使用默认值
          reviewStatus: item.review_status || 'pending'
        }))
        
        setTableData(transformedData)
        setTotalCount(response.data.count || 0)
        showSuccessToast(`加载成功，共 ${transformedData.length} 条待审核记录`)
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H12',
          location: 'InvoiceReviewPending.tsx:fetchData',
          message: 'fetch pending reviews success',
          data: { returned: transformedData.length, totalCount: response.data.count || 0 }
        })
      } else {
        setTableData([])
        setTotalCount(0)
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H12',
          location: 'InvoiceReviewPending.tsx:fetchData',
          message: 'fetch pending reviews empty',
          data: { hasData: !!response.data }
        })
      }
    } catch (error: any) {
      console.error('加载数据失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '加载数据失败'
      showErrorToast(errorMessage)
      setTableData([])
      setTotalCount(0)
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H12',
        location: 'InvoiceReviewPending.tsx:fetchData',
        message: 'fetch pending reviews error',
        data: { error: errorMessage, status: error?.response?.status }
      })
    } finally {
      setIsLoading(false)
    }
  }

  // 组件加载时自动获取数据
  useEffect(() => {
    fetchData()
  }, [])

  const handleApprove = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/invoices/review/${id}/approve`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.data) {
        showSuccessToast(response.data.message || '审核通过')
        fetchData() // 刷新列表
      }
    } catch (error: any) {
      console.error('审核失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '审核失败'
      showErrorToast(errorMessage)
    }
  }

  const handleReject = async (id: string) => {
    // 弹出输入框让用户输入拒绝原因
    const comment = prompt('请输入拒绝原因（必填）:')
    if (!comment || comment.trim() === '') {
      showErrorToast('拒绝原因不能为空')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/invoices/review/${id}/reject`,
        {
          comment: comment.trim()
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.data) {
        showSuccessToast(response.data.message || '已拒绝')
        fetchData() // 刷新列表
      }
    } catch (error: any) {
      console.error('拒绝失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '操作失败'
      showErrorToast(errorMessage)
    }
  }

  const handleExport = async (invoiceIds?: string[]) => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      // 确定要导出的发票ID列表
      let idsToExport: string[] = []
      if (invoiceIds && invoiceIds.length > 0) {
        // 如果指定了发票ID列表，使用指定的ID
        idsToExport = invoiceIds
      } else {
        // 否则导出当前表格中的所有数据
        idsToExport = tableData.map(item => item.id)
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

      // 提取发票数据
      const invoices = invoiceResponses.map(res => res.data)
      
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

      // 导出为CSV
      exportInvoicesToCSV(invoices, allItems, `待审核发票数据_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.csv`)
      showSuccessToast(`成功导出 ${invoices.length} 条发票数据`)
    } catch (error: any) {
      console.error('导出失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '导出失败'
      showErrorToast(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const columnDefs: ColDef[] = [
    {
      headerName: '票据编号',
      field: 'invoiceNo',
      width: 150
    },
    { headerName: '票据类型', field: 'invoiceType', width: 150 },
    { headerName: '开票日期', field: 'invoiceDate', width: 120 },
    {
      headerName: '金额',
      field: 'amount',
      width: 120,
      cellRenderer: (params: any) => `¥${params.value?.toFixed(2) || '0.00'}`
    },
    { headerName: '供应商', field: 'supplier', width: 150 },
    { headerName: '提交时间', field: 'submitTime', width: 180 },
    { headerName: '提交人', field: 'submitter', width: 100 },
    {
      headerName: '操作',
      width: 200,
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
            colorPalette="green"
            onClick={() => handleApprove(params.data.id)}
          >
            <FiCheck />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            colorPalette="red"
            onClick={() => handleReject(params.data.id)}
          >
            <FiX />
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
      (item.companyCode && item.companyCode.toLowerCase().includes(keyword))
    )
  }, [tableData, searchKeyword])

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">
          待审核票据 {totalCount > 0 && `(共 ${totalCount} 条)`}
        </Text>
        <HStack gap={2}>
          <Button
            onClick={() => handleExport()}
            loading={isLoading}
            colorPalette="green"
          >
            <FiDownload style={{ marginRight: '8px' }} />
            导出全部
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

      <Grid templateColumns="1fr auto" gap={3} mb={4}>
        <Input
          placeholder="搜索票据编号或供应商..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && fetchData()}
        />
        <Button onClick={fetchData}>
          <FiSearch style={{ marginRight: '8px' }} />
          搜索
        </Button>
      </Grid>

      <Box className="ag-theme-alpine" style={{ height: '600px', width: '100%', overflow: 'hidden' }}>
        <AgGridReact
          theme="legacy"
          rowData={filteredData}
          columnDefs={columnDefs}
          defaultColDef={{
            resizable: true,
            sortable: true,
            filter: true
          }}
          onGridReady={() => fetchData()}
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

export default InvoiceReviewPending
