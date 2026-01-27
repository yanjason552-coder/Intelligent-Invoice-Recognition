import { Box, Text, Flex, Grid, Input, Badge, HStack } from "@chakra-ui/react"
import { FiSearch, FiRefreshCw, FiEye, /* FiPlay, */ FiLayers, FiUpload } from "react-icons/fi"
import { useState, useMemo, useEffect, useRef } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { Button } from "@/components/ui/button"
import useCustomToast from '@/hooks/useCustomToast'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"
import RecognitionParamsModal from './RecognitionParamsModal'
import InvoiceDetailModal from './InvoiceDetailModal'

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
    body: JSON.stringify({
      sessionId: DEBUG_SESSION,
      timestamp: Date.now(),
      ...payload,
    }),
  }).catch(() => {})
  // #endregion
}

ModuleRegistry.registerModules([AllCommunityModule])

interface RecognitionTask {
  id: string
  fileId: string
  invoiceNo: string
  fileName: string
  uploadTime: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  templateName: string
  recognitionTime: string
  operator: string
  companyCode: string | null
}

const InvoiceRecognitionList = () => {
  const [tableData, setTableData] = useState<RecognitionTask[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [isParamsModalOpen, setIsParamsModalOpen] = useState(false)
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([])
  const [currentInvoiceId, setCurrentInvoiceId] = useState<string | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null)
  const [reuploadFileId, setReuploadFileId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const gridRef = useRef<AgGridReact>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const fetchData = async (searchTerm?: string) => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      // 构建查询参数
      const params: any = {
        skip: 0,
        limit: 100
      }
      
      if (searchTerm) {
        // 如果搜索关键词是票据编号格式，使用invoice_no参数
        if (searchTerm.toUpperCase().startsWith('INV-')) {
          params.invoice_no = searchTerm
        } else {
          // 否则使用file_name参数
          params.file_name = searchTerm
        }
      }

      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/files/list`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          params
        }
      )

      if (response.data && response.data.data) {
        // 转换数据格式
        const transformedData: RecognitionTask[] = response.data.data
          .map((item: any) => ({
          id: item.invoice_id || item.file_id,
          fileId: item.file_id,
          invoiceNo: item.invoice_no || '',
          fileName: item.file_name || '',
          uploadTime: item.upload_time ? new Date(item.upload_time).toLocaleString('zh-CN') : '',
          status: item.recognition_status || 'pending',
          templateName: item.template_name || '未匹配',
          recognitionTime: item.recognition_time ? new Date(item.recognition_time).toLocaleString('zh-CN') : '-',
          operator: item.uploader_name || item.creator_name || '-',
          companyCode: item.company_code || null
        }))
          // 过滤掉识别已完成的数据
          .filter((item: RecognitionTask) => item.status !== 'completed')
        
        setTableData(transformedData)
        showSuccessToast(`加载成功，共 ${transformedData.length} 条记录`)
      } else {
        setTableData([])
      }
    } catch (error: any) {
      console.error('加载数据失败:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || '加载数据失败'
      showErrorToast(errorMessage)
      setTableData([])
    } finally {
      setIsLoading(false)
    }
  }

  // 组件加载时自动获取数据
  useEffect(() => {
    fetchData()
  }, [])

  const handleSearch = () => {
    fetchData(searchKeyword)
  }

  const handleStartRecognition = async (invoiceId: string, params?: any) => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H4',
          location: 'InvoiceRecognitionList.tsx:handleStartRecognition',
          message: 'token missing',
          data: { invoiceId }
        })
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H4',
        location: 'InvoiceRecognitionList.tsx:handleStartRecognition',
        message: 'start recognition invoked',
        data: { invoiceId, hasParams: !!params, apiBaseUrl }
      })

      if (params) {
        // 创建任务并启动
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H4',
          location: 'InvoiceRecognitionList.tsx:handleStartRecognition',
          message: 'creating recognition task',
          data: { invoiceId, recognitionMode: params?.recognition_mode, modelConfigId: params?.model_config_id }
        })
        const createResponse = await axios.post(
          `${apiBaseUrl}/api/v1/invoices/recognition-tasks`,
          {
            invoice_id: invoiceId,
            params: params,
            priority: 0
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        )

        if (createResponse.data) {
          const taskId = createResponse.data.id
          postDebugLog({
            runId: 'pre-run',
            hypothesisId: 'H4',
            location: 'InvoiceRecognitionList.tsx:handleStartRecognition',
            message: 'task created; starting',
            data: { invoiceId, taskId }
          })
          // 启动任务
          await axios.post(
            `${apiBaseUrl}/api/v1/invoices/recognition-tasks/${taskId}/start`,
            {},
            {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            }
          )
          showSuccessToast('识别任务已启动')
          postDebugLog({
            runId: 'pre-run',
            hypothesisId: 'H4',
            location: 'InvoiceRecognitionList.tsx:handleStartRecognition',
            message: 'task start request success',
            data: { invoiceId, taskId }
          })
          fetchData()
        }
      } else {
        // 打开参数选择弹窗
        setCurrentInvoiceId(invoiceId)
        setIsParamsModalOpen(true)
      }
    } catch (error: any) {
      console.error('启动识别失败:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || '启动识别失败'
      showErrorToast(errorMessage)
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H4',
        location: 'InvoiceRecognitionList.tsx:handleStartRecognition',
        message: 'start recognition error',
        data: { invoiceId, error: errorMessage, status: error?.response?.status }
      })
    }
  }

  const handleBatchStart = () => {
    // 获取选中的行
    const selectedRows = gridRef.current?.api.getSelectedRows() || []
    postDebugLog({
      runId: 'pre-run',
      hypothesisId: 'H8',
      location: 'InvoiceRecognitionList.tsx:handleBatchStart',
      message: 'batch start clicked',
      data: {
        selectedCount: selectedRows.length,
        statuses: selectedRows.reduce((acc: Record<string, number>, r: any) => {
          const s = r?.status || 'unknown'
          acc[s] = (acc[s] || 0) + 1
          return acc
        }, {})
      }
    })
    if (selectedRows.length === 0) {
      showErrorToast('请先选择要识别的记录')
      return
    }

    // 过滤出可重新识别的记录：pending + failed（processing/completed 不允许重复启动）
    const runnableRows = selectedRows.filter((row: any) => row.status === 'pending' || row.status === 'failed')
    if (runnableRows.length === 0) {
      showErrorToast('所选记录中没有可启动的记录（仅支持：待处理/失败）')
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H8',
        location: 'InvoiceRecognitionList.tsx:handleBatchStart',
        message: 'no runnable rows; batch start blocked',
        data: {
          selectedCount: selectedRows.length,
          selectedStatuses: selectedRows.map((r: any) => r?.status || 'unknown').slice(0, 20),
        }
      })
      return
    }

    // 提取文件ID，确保每个ID都存在且有效
    const fileIds = runnableRows
      .map((row: any) => row.fileId)
      .filter((id: string) => id && id.trim() !== '')

    if (fileIds.length === 0) {
      showErrorToast('无法获取有效的文件ID')
      return
    }

    console.log('批量启动，选中的文件ID:', fileIds)
    setSelectedFileIds(fileIds)
    setCurrentInvoiceId(null) // 批量操作时设为null
    setIsParamsModalOpen(true)
  }

  const handleParamsConfirm = async (params: any) => {
    setIsParamsModalOpen(false)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H4',
          location: 'InvoiceRecognitionList.tsx:handleParamsConfirm',
          message: 'token missing',
          data: { currentInvoiceId, selectedFileIdsCount: selectedFileIds?.length || 0 }
        })
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H4',
        location: 'InvoiceRecognitionList.tsx:handleParamsConfirm',
        message: 'params confirmed',
        data: { currentInvoiceId, selectedFileIdsCount: selectedFileIds?.length || 0, apiBaseUrl }
      })

      if (currentInvoiceId) {
        // 单个任务
        await handleStartRecognition(currentInvoiceId, params)
      } else if (selectedFileIds && selectedFileIds.length > 0) {
        // 批量任务 - 验证文件ID
        const validFileIds = selectedFileIds.filter((id: string) => id && id.trim() !== '')
        if (validFileIds.length === 0) {
          showErrorToast('没有有效的文件ID，请重新选择')
          return
        }

        console.log('批量创建任务，文件ID列表:', validFileIds)
        console.log('参数:', params)

        const response = await axios.post(
          `${apiBaseUrl}/api/v1/invoices/recognition-tasks/batch`,
          {
            uploaded_file_ids: validFileIds,
            params: params
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )

        if (response.data) {
          showSuccessToast(`成功创建 ${response.data.count} 个识别任务`)
          postDebugLog({
            runId: 'pre-run',
            hypothesisId: 'H4',
            location: 'InvoiceRecognitionList.tsx:handleParamsConfirm',
            message: 'batch created',
            data: { count: response.data.count, taskIdsCount: response.data.task_ids?.length || 0 }
          })
          
          // 自动启动所有创建的任务
          if (response.data.task_ids && response.data.task_ids.length > 0) {
            let startedCount = 0
            let failedCount = 0
            
            for (const taskId of response.data.task_ids) {
              try {
                await axios.post(
                  `${apiBaseUrl}/api/v1/invoices/recognition-tasks/${taskId}/start`,
                  {},
                  {
                    headers: {
                      'Authorization': `Bearer ${token}`
                    }
                  }
                )
                startedCount++
                postDebugLog({
                  runId: 'pre-run',
                  hypothesisId: 'H4',
                  location: 'InvoiceRecognitionList.tsx:handleParamsConfirm',
                  message: 'batch start success',
                  data: { taskId }
                })
              } catch (error: any) {
                console.error(`启动任务 ${taskId} 失败:`, error)
                failedCount++
                const errMsg = error?.response?.data?.detail || error?.message || '启动失败'
                postDebugLog({
                  runId: 'pre-run',
                  hypothesisId: 'H4',
                  location: 'InvoiceRecognitionList.tsx:handleParamsConfirm',
                  message: 'batch start failed',
                  data: { taskId, error: errMsg, status: error?.response?.status }
                })
              }
            }
            
            if (startedCount > 0) {
              showSuccessToast(`已启动 ${startedCount} 个识别任务${failedCount > 0 ? `，${failedCount} 个失败` : ''}`)
            }
          }
          
          setSelectedFileIds([])
          fetchData()
        }
      } else {
        // 既没有单个发票ID，也没有选中的文件ID
        showErrorToast('请先选择要识别的文件')
      }
    } catch (error: any) {
      console.error('创建任务失败:', error)
      console.error('错误详情:', error?.response?.data)
      const errorMessage = error?.response?.data?.detail || error?.message || '创建任务失败'
      showErrorToast(errorMessage)
    }
  }

  const handleReupload = (fileId: string) => {
    setReuploadFileId(fileId)
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !reuploadFileId) return

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const formData = new FormData()
      formData.append('file', file)

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/invoices/upload`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      if (response.data) {
        showSuccessToast('文件上传成功')
        fetchData()
      }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '上传失败'
      showErrorToast(`上传失败: ${errorMessage}`)
    } finally {
      setReuploadFileId(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'gray', text: '待处理' },
      processing: { color: 'blue', text: '识别中' },
      completed: { color: 'green', text: '已完成' },
      failed: { color: 'red', text: '失败' }
    }
    const statusInfo = statusMap[status] || statusMap.pending
    return <Badge colorScheme={statusInfo.color}>{statusInfo.text}</Badge>
  }

  const columnDefs: ColDef[] = [
    {
      headerName: '票据编号',
      field: 'invoiceNo',
      width: 150,
      // checkboxSelection: true,
      headerCheckboxSelection: true
    },
    { headerName: '文件名', field: 'fileName', width: 200 },
    { headerName: '上传时间', field: 'uploadTime', width: 180 },
    {
      headerName: '状态',
      field: 'status',
      width: 100,
      cellRenderer: (params: any) => getStatusBadge(params.value)
    },
    { headerName: '模板名称', field: 'templateName', width: 150 },
    { headerName: '识别时间', field: 'recognitionTime', width: 180 },
    { headerName: '操作人', field: 'operator', width: 100 },
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
            查看
          </Button>
          <Button
            size="sm"
            variant="ghost"
            colorPalette="blue"
            onClick={() => handleReupload(params.data.fileId)}
          >
            再次上传
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
      item.fileName.toLowerCase().includes(keyword) ||
      (item.companyCode && item.companyCode.toLowerCase().includes(keyword))
    )
  }, [tableData, searchKeyword])

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">
          票据识别任务
        </Text>
        <HStack gap={2}>
          <Button
            onClick={handleBatchStart}
            colorPalette="blue"
          >
            <FiLayers style={{ marginRight: '8px' }} />
            批量启动
          </Button>
          <Button
            onClick={() => fetchData()}
            loading={isLoading}
          >
            <FiRefreshCw style={{ marginRight: '8px' }} />
            刷新
          </Button>
        </HStack>
      </Flex>

      {/* 搜索栏 */}
      <Grid templateColumns="1fr auto" gap={3} mb={4}>
        <Input
          placeholder="搜索票据编号或文件名..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button onClick={handleSearch}>
          <FiSearch style={{ marginRight: '8px' }} />
          搜索
        </Button>
      </Grid>

      {/* 表格 */}
      <Box className="ag-theme-alpine" style={{ height: '600px', width: '100%', overflow: 'hidden' }}>
        <AgGridReact
          theme="legacy"
          ref={gridRef}
          rowData={filteredData}
          columnDefs={columnDefs}
          defaultColDef={{
            resizable: true,
            sortable: true,
            filter: true
          }}
          rowSelection={{ mode: 'multiRow' }}
        />
      </Box>

      {/* 参数选择弹窗 */}
      <RecognitionParamsModal
        isOpen={isParamsModalOpen}
        onClose={() => {
          setIsParamsModalOpen(false)
          setCurrentInvoiceId(null)
          setSelectedFileIds([])
        }}
        onConfirm={handleParamsConfirm}
      />

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

      {/* 隐藏的文件输入，用于再次上传 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        style={{ display: 'none' }}
        onChange={handleFileSelect}
      />
    </Box>
  )
}

export default InvoiceRecognitionList
