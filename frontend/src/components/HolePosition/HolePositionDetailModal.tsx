import { Box, Text, Flex, VStack, Badge, Grid, GridItem } from "@chakra-ui/react"
import { FiX } from "react-icons/fi"
import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import useCustomToast from '@/hooks/useCustomToast'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

ModuleRegistry.registerModules([AllCommunityModule])

interface HolePositionDetailModalProps {
  isOpen: boolean
  onClose: () => void
  recordId: string
}

interface HolePositionDetail {
  id: string
  record_no: string
  doc_type: string | null
  form_title: string | null
  drawing_no: string | null
  part_name: string | null
  part_no: string | null
  date: string | null
  inspector_name: string | null
  overall_result: string | null
  remarks: string | null
  file_id: string
  template_name: string | null
  template_version: string | null
  model_name: string | null
  recognition_accuracy: number | null
  recognition_status: string
  review_status: string
  reviewer_id: string | null
  review_time: string | null
  review_comment: string | null
  creator_id: string
  company_id: string | null
  create_time: string
  update_time: string | null
}

interface HolePositionItem {
  item_no: number | null
  inspection_item: string | null
  spec_requirement: string | null
  actual_value: string | null
  actual: number[] | null
  range_min: number | null
  range_max: number | null
  range_value: string | null
  judgement: string | null
  notes: string | null
}

interface InvoiceFileInfo {
  id: string
  file_name: string
  file_path: string
  file_hash: string
  mime_type: string
  file_type: string
}

const HolePositionDetailModal = ({ isOpen, onClose, recordId }: HolePositionDetailModalProps) => {
  const [recordDetail, setRecordDetail] = useState<HolePositionDetail | null>(null)
  const [recordItems, setRecordItems] = useState<HolePositionItem[]>([])
  const [invoiceFile, setInvoiceFile] = useState<InvoiceFileInfo | null>(null)
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { showErrorToast } = useCustomToast()

  useEffect(() => {
    if (isOpen && recordId) {
      fetchRecordDetail()
      fetchRecordItems()
    }
    // 清理函数
    return () => {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl)
        setPdfBlobUrl(null)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, recordId])

  useEffect(() => {
    if (recordDetail?.file_id) {
      fetchInvoiceFile()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordDetail?.file_id])

  const fetchRecordDetail = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      const response = await axios.get(
        `${apiBaseUrl}/api/v1/hole-position/${recordId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data) {
        setRecordDetail(response.data)
      }
    } catch (error: any) {
      console.error('获取孔位类记录详情失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '获取记录详情失败'
      showErrorToast(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchRecordItems = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      const response = await axios.get(
        `${apiBaseUrl}/api/v1/hole-position/${recordId}/items`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data && response.data.data) {
        setRecordItems(response.data.data)
      }
    } catch (error: any) {
      console.error('获取孔位类行项目失败:', error)
      setRecordItems([])
    }
  }

  const fetchInvoiceFile = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      // 使用发票文件的API端点（因为孔位类记录也使用invoice_file表）
      const response = await axios.get(
        `${apiBaseUrl}/api/v1/invoices/${recordDetail?.file_id}/file`,
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
      console.error('获取文件信息失败:', error)
      setInvoiceFile(null)
    }
  }

  const fetchPdfAsBlob = async () => {
    if (!recordDetail?.file_id) return
    
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      
      const response = await fetch(
        `${apiBaseUrl}/api/v1/invoices/${recordDetail.file_id}/file/download`,
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

  // 获取文件URL
  const getFileUrl = () => {
    if (invoiceFile?.mime_type === 'application/pdf' && pdfBlobUrl) {
      return pdfBlobUrl
    }
    if (!invoiceFile || !recordDetail) return null
    const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
    return `${apiBaseUrl}/api/v1/invoices/${recordDetail.file_id}/file/download`
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

  // 检验项目的列定义
  const inspectionItemColumnDefs: ColDef[] = useMemo(() => {
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
        headerName: '实测值数组',
        field: 'actual',
        width: 150,
        editable: false,
        cellRenderer: (params: any) => {
          if (params.value && Array.isArray(params.value)) {
            return params.value.join(', ')
          }
          return '-'
        }
      },
      {
        headerName: '范围最小值',
        field: 'range_min',
        width: 120,
        editable: false
      },
      {
        headerName: '范围最大值',
        field: 'range_max',
        width: 120,
        editable: false
      },
      {
        headerName: '范围值',
        field: 'range_value',
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
            return '合格'
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
  }, [])

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
            孔位类记录详情
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
        ) : recordDetail ? (
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

            {/* 右侧：记录详情 */}
            <Box flex="1" minW="0" overflow="auto">
              <VStack align="stretch" gap={6}>
                {/* 记录头信息 */}
                <Box>
                  <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                    记录头信息
                  </Text>
                  <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">记录编号</Text>
                      <Text fontWeight="medium">{recordDetail.record_no || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">文档类型</Text>
                      <Text fontWeight="medium">{recordDetail.doc_type || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">表单标题</Text>
                      <Text fontWeight="medium">{recordDetail.form_title || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">图号</Text>
                      <Text fontWeight="medium">{recordDetail.drawing_no || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">零件名称</Text>
                      <Text fontWeight="medium">{recordDetail.part_name || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">零件号</Text>
                      <Text fontWeight="medium">{recordDetail.part_no || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">日期</Text>
                      <Text fontWeight="medium">
                        {recordDetail.date 
                          ? new Date(recordDetail.date).toLocaleDateString('zh-CN') 
                          : '-'}
                      </Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">检验员</Text>
                      <Text fontWeight="medium">{recordDetail.inspector_name || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">总体结果</Text>
                      {recordDetail.overall_result ? (
                        <Badge colorScheme={recordDetail.overall_result === 'pass' ? 'green' : recordDetail.overall_result === 'fail' ? 'red' : 'gray'}>
                          {recordDetail.overall_result === 'pass' ? '合格' : recordDetail.overall_result === 'fail' ? '不合格' : '未知'}
                        </Badge>
                      ) : (
                        <Text fontWeight="medium">-</Text>
                      )}
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">识别状态</Text>
                      <Flex direction="column" gap={2}>
                        {getStatusBadge(recordDetail.recognition_status)}
                      </Flex>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">审核状态</Text>
                      {getStatusBadge(recordDetail.review_status)}
                    </GridItem>
                    <GridItem colSpan={2}>
                      <Text fontSize="sm" color="gray.600">备注</Text>
                      <Text fontWeight="medium">{recordDetail.remarks || '-'}</Text>
                    </GridItem>
                    <GridItem>
                      <Text fontSize="sm" color="gray.600">创建时间</Text>
                      <Text fontWeight="medium">
                        {recordDetail.create_time ? new Date(recordDetail.create_time).toLocaleString('zh-CN') : '-'}
                      </Text>
                    </GridItem>
                  </Grid>
                </Box>

                {/* 模板信息 */}
                {recordDetail.template_name && (
                  <Box>
                    <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                      识别模板信息
                    </Text>
                    <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                      <GridItem>
                        <Text fontSize="sm" color="gray.600">模板名称</Text>
                        <Text fontWeight="medium">{recordDetail.template_name}</Text>
                      </GridItem>
                      {recordDetail.template_version && (
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">模板版本</Text>
                          <Text fontWeight="medium">{recordDetail.template_version}</Text>
                        </GridItem>
                      )}
                      {recordDetail.model_name && (
                        <GridItem>
                          <Text fontSize="sm" color="gray.600">模型名称</Text>
                          <Text fontWeight="medium">{recordDetail.model_name}</Text>
                        </GridItem>
                      )}
                    </Grid>
                  </Box>
                )}

                <Box borderTop="1px solid" borderColor="gray.200" my={4} />

                {/* 检验项目信息 */}
                <Box>
                  <Text fontSize="lg" fontWeight="bold" mb={4} pb={2} borderBottom="2px solid" borderColor="gray.200">
                    检验项目信息 {recordItems.length > 0 ? `(共 ${recordItems.length} 项)` : ''}
                  </Text>
                  {recordItems.length > 0 ? (
                    <Box className="ag-theme-alpine" style={{ height: '400px', width: '100%' }}>
                      <AgGridReact
                        theme="legacy"
                        rowData={recordItems}
                        columnDefs={inspectionItemColumnDefs}
                        defaultColDef={{
                          resizable: true,
                          sortable: true
                        }}
                      />
                    </Box>
                  ) : (
                    <Text color="gray.500" textAlign="center" py={8}>
                      暂无检验项目数据
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

export default HolePositionDetailModal

