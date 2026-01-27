import { Box, Text, Flex, VStack, HStack, Input, Badge, IconButton } from "@chakra-ui/react"
import { FiPlus, FiEdit, FiTrash2, FiCopy, FiUpload, FiDownload, FiSearch, FiCheckCircle, FiXCircle, FiClock } from "react-icons/fi"
import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Checkbox } from "@/components/ui/checkbox"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { ColDef, GridReadyEvent, SelectionChangedEvent } from 'ag-grid-community'

interface Template {
  id: string
  name: string
  template_type: string
  description?: string
  status: string
  current_version?: string
  accuracy?: number
  schema_id?: string
  schema_name?: string
  schema_version?: string
  matching_rules_count?: number
  create_time?: string
  update_time?: string
}

interface TemplateField {
  id?: string
  field_key: string
  field_name: string
  data_type: string
  is_required: boolean
  description?: string
  example?: string
  validation?: any
  normalize?: any
  prompt_hint?: string
  confidence_threshold?: number
  parent_field_id?: string
  sort_order?: number
}

const TemplateConfig = () => {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedRows, setSelectedRows] = useState<Template[]>([])
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalCount, setTotalCount] = useState(0)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
  const gridRef = useRef<AgGridReact>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // AG Grid 列定义
  const columnDefs: ColDef[] = [
    {
      headerName: '模板名称',
      field: 'name',
      width: 200,
      pinned: 'left',
      checkboxSelection: true,
      headerCheckboxSelection: true,
    },
    {
      headerName: '模板类型',
      field: 'template_type',
      width: 150,
      cellRenderer: (params: any) => {
        const type = params.value || '未知'
        const colors: Record<string, string> = {
          '增值税发票': 'blue',
          '普通发票': 'green',
          '采购订单': 'purple',
          '收据': 'orange',
          '其他': 'gray'
        }
        return (
          <Badge colorScheme={colors[type] || 'gray'}>{type}</Badge>
        )
      }
    },
    {
      headerName: '描述',
      field: 'description',
      width: 200,
      tooltipField: 'description',
    },
    {
      headerName: '绑定 Schema',
      field: 'schema_name',
      width: 180,
      cellRenderer: (params: any) => {
        const schemaName = params.data?.schema_name
        const schemaVersion = params.data?.schema_version
        if (!schemaName) {
          return <Text fontSize="sm" color="gray.500">未绑定</Text>
        }
        return (
          <VStack spacing={0} align="start">
            <Badge colorScheme="blue">{schemaName}</Badge>
            {schemaVersion && (
              <Text fontSize="xs" color="gray.500">v{schemaVersion}</Text>
            )}
          </VStack>
        )
      }
    },
    {
      headerName: '匹配规则',
      field: 'matching_rules_count',
      width: 100,
      cellRenderer: (params: any) => {
        const count = params.data?.matching_rules_count || 0
        return count > 0 ? (
          <Badge colorScheme="green">{count} 条</Badge>
        ) : (
          <Text fontSize="sm" color="gray.500">-</Text>
        )
      }
    },
    {
      headerName: '状态',
      field: 'status',
      width: 100,
      cellRenderer: (params: any) => {
        const status = params.value || 'enabled'
        const statusMap: Record<string, { label: string; color: string }> = {
          'enabled': { label: '启用', color: 'green' },
          'disabled': { label: '停用', color: 'gray' },
          'deprecated': { label: '废弃', color: 'red' }
        }
        const statusInfo = statusMap[status] || statusMap['enabled']
        return (
          <Badge colorScheme={statusInfo.color}>{statusInfo.label}</Badge>
        )
      }
    },
    {
      headerName: '当前版本',
      field: 'current_version',
      width: 120,
      cellRenderer: (params: any) => {
        return params.value ? (
          <Badge colorScheme="blue">{params.value}</Badge>
        ) : (
          <Text fontSize="sm" color="gray.500">无版本</Text>
        )
      }
    },
    {
      headerName: '准确率',
      field: 'accuracy',
      width: 100,
      cellRenderer: (params: any) => {
        const accuracy = params.value
        if (accuracy === null || accuracy === undefined) {
          return <Text fontSize="sm" color="gray.500">-</Text>
        }
        const percentage = (accuracy * 100).toFixed(1)
        const color = accuracy >= 0.9 ? 'green' : accuracy >= 0.7 ? 'orange' : 'red'
        return (
          <Badge colorScheme={color}>{percentage}%</Badge>
        )
      }
    },
    {
      headerName: '创建时间',
      field: 'create_time',
      width: 180,
      cellRenderer: (params: any) => {
        if (!params.value) return '-'
        const date = new Date(params.value)
        return date.toLocaleString('zh-CN')
      }
    },
    {
      headerName: '更新时间',
      field: 'update_time',
      width: 180,
      cellRenderer: (params: any) => {
        if (!params.value) return '-'
        const date = new Date(params.value)
        return date.toLocaleString('zh-CN')
      }
    },
    {
      headerName: '操作',
      field: 'actions',
      width: 200,
      pinned: 'right',
      cellRenderer: (params: any) => {
        const template = params.data as Template
        return (
          <HStack spacing={2}>
            <IconButton
              aria-label="编辑"
              icon={<FiEdit />}
              size="sm"
              variant="ghost"
              onClick={() => handleEdit(template)}
            />
            <IconButton
              aria-label="复制"
              icon={<FiCopy />}
              size="sm"
              variant="ghost"
              onClick={() => handleCopy(template)}
            />
            <IconButton
              aria-label={template.status === 'enabled' ? '停用' : '启用'}
              icon={template.status === 'enabled' ? <FiXCircle /> : <FiCheckCircle />}
              size="sm"
              variant="ghost"
              colorScheme={template.status === 'enabled' ? 'red' : 'green'}
              onClick={() => handleToggleStatus(template)}
            />
          </HStack>
        )
      }
    }
  ]

  // 加载模板列表
  const loadTemplates = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const params: any = {
        skip: (currentPage - 1) * pageSize,
        limit: pageSize
      }
      
      if (searchText) {
        params.q = searchText
      }
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      if (typeFilter !== 'all') {
        params.template_type = typeFilter
      }

      const response = await axios.get('/api/v1/templates', {
        params,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      if (response.data) {
        setTemplates(response.data.data || [])
        setTotalCount(response.data.count || 0)
      }
    } catch (error: any) {
      console.error('加载模板列表失败:', error)
      showErrorToast(error.response?.data?.detail || '加载模板列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTemplates()
  }, [currentPage, pageSize, searchText, statusFilter, typeFilter])

  // 监听模板列表刷新事件
  useEffect(() => {
    const handleRefresh = () => {
      loadTemplates()
    }
    window.addEventListener('refreshTemplateList', handleRefresh)
    return () => {
      window.removeEventListener('refreshTemplateList', handleRefresh)
    }
  }, [])

  // 处理选择变化
  const onSelectionChanged = (event: SelectionChangedEvent) => {
    const selectedNodes = event.api.getSelectedNodes()
    const selectedData = selectedNodes.map(node => node.data as Template)
    setSelectedRows(selectedData)
  }

  // 处理编辑
  const handleEdit = (template: Template) => {
    setEditingTemplate(template)
    setShowEditModal(true)
    // 触发打开编辑页面的自定义事件
    const event = new CustomEvent('openTab', {
      detail: {
        type: 'template-edit',
        data: {
          templateId: template.id,
          templateData: template
        }
      }
    })
    window.dispatchEvent(event)
  }

  // 处理复制
  const handleCopy = async (template: Template) => {
    try {
      const token = localStorage.getItem('access_token')
      // 先获取模板详情
      const detailResponse = await axios.get(`/api/v1/templates/${template.id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      // 创建新模板（复制）
      const newTemplate = {
        name: `${template.name}_副本`,
        template_type: template.template_type,
        description: template.description,
        status: 'disabled' // 复制的模板默认停用
      }

      await axios.post('/api/v1/templates', newTemplate, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      showSuccessToast('模板复制成功')
      loadTemplates()
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '复制模板失败')
    }
  }

  // 处理启用/停用
  const handleToggleStatus = async (template: Template) => {
    try {
      const token = localStorage.getItem('access_token')
      const newStatus = template.status === 'enabled' ? 'disabled' : 'enabled'
      
      await axios.put(`/api/v1/templates/${template.id}`, {
        status: newStatus
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      showSuccessToast(`模板已${newStatus === 'enabled' ? '启用' : '停用'}`)
      loadTemplates()
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '操作失败')
    }
  }

  // 处理新建
  const handleNew = () => {
    setEditingTemplate(null)
    setShowEditModal(true)
    // 触发打开新建页面的自定义事件
    const event = new CustomEvent('openTab', {
      detail: {
        type: 'template-edit',
        data: {
          templateId: null,
          templateData: null
        }
      }
    })
    window.dispatchEvent(event)
  }

  // 处理导入
  const handleImport = () => {
    // 触发打开导入页面的自定义事件
    const event = new CustomEvent('openTab', {
      detail: {
        type: 'template-import',
        data: undefined
      }
    })
    window.dispatchEvent(event)
  }

  // 处理导出
  const handleExport = async () => {
    if (selectedRows.length === 0) {
      showErrorToast('请选择要导出的模板')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      // TODO: 实现导出功能
      showErrorToast('导出功能开发中')
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '导出失败')
    }
  }

  // 处理批量删除
  const handleBatchDelete = async () => {
    if (selectedRows.length === 0) {
      showErrorToast('请选择要删除的模板')
      return
    }

    if (!confirm(`确定要删除选中的 ${selectedRows.length} 个模板吗？`)) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      // TODO: 实现批量删除
      showErrorToast('批量删除功能开发中')
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '删除失败')
    }
  }

  // 获取状态选项
  const statusOptions = [
    { value: 'all', label: '全部状态' },
    { value: 'enabled', label: '启用' },
    { value: 'disabled', label: '停用' },
    { value: 'deprecated', label: '废弃' }
  ]

  // 获取类型选项
  const typeOptions = [
    { value: 'all', label: '全部类型' },
    { value: '增值税发票', label: '增值税发票' },
    { value: '普通发票', label: '普通发票' },
    { value: '采购订单', label: '采购订单' },
    { value: '收据', label: '收据' },
    { value: '其他', label: '其他' }
  ]

  return (
    <Box p={4} h="100vh" display="flex" flexDirection="column" overflow="auto">
      {/* 标题栏 */}
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">单据模板配置</Text>
        <HStack spacing={2}>
          <Button onClick={handleNew} leftIcon={<FiPlus />} colorScheme="blue">
            新建模板
          </Button>
          <Button onClick={handleImport} leftIcon={<FiUpload />} variant="outline">
            导入模板
          </Button>
          <Button 
            onClick={handleExport} 
            leftIcon={<FiDownload />} 
            variant="outline"
            isDisabled={selectedRows.length === 0}
          >
            导出模板
          </Button>
          {selectedRows.length > 0 && (
            <Button 
              onClick={handleBatchDelete} 
              leftIcon={<FiTrash2 />} 
              colorScheme="red"
              variant="outline"
            >
              批量删除 ({selectedRows.length})
            </Button>
          )}
        </HStack>
      </Flex>

      {/* 搜索和筛选栏 */}
      <Box bg="white" p={4} borderRadius="md" mb={4} border="1px" borderColor="gray.200">
        <Flex gap={4} align="center" flexWrap="wrap">
          <Box flex="1" minW="200px" position="relative">
            <Field label="搜索">
              <Box position="relative">
                <FiSearch style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', zIndex: 1, color: '#718096' }} />
                <Input
                  placeholder="搜索模板名称或描述..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  pl="10"
                />
              </Box>
            </Field>
          </Box>
          <Box minW="150px">
            <Field label="状态">
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '4px' }}
              >
                {statusOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </Field>
          </Box>
          <Box minW="150px">
            <Field label="类型">
              <select
                id="type-filter"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '4px' }}
              >
                {typeOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </Field>
          </Box>
          <Button onClick={loadTemplates} variant="outline">
            刷新
          </Button>
        </Flex>
      </Box>

      {/* 数据表格 */}
      <Box flex="1" minH="0" overflow="hidden" className="ag-theme-alpine" style={{ height: '100%', width: '100%' }}>
        <AgGridReact
          theme="legacy"
          ref={gridRef}
          rowData={templates}
          columnDefs={columnDefs}
          rowSelection={{ mode: 'multiRow' }}
          onSelectionChanged={onSelectionChanged}
          onRowDoubleClicked={(event) => {
            // 双击行时打开模板详情
            handleEdit(event.data as Template)
          }}
          onGridReady={(params: GridReadyEvent) => {
            params.api.sizeColumnsToFit()
          }}
          defaultColDef={{
            resizable: true,
            sortable: true,
            filter: true
          }}
          pagination={true}
          paginationPageSize={pageSize}
          paginationPageSizeSelector={[10, 20, 50, 100]}
          animateRows={true}
          loading={loading}
        />
      </Box>

      {/* 分页信息 */}
      <Flex justify="space-between" align="center" mt={4}>
        <Text fontSize="sm" color="gray.600">
          共 {totalCount} 条记录，第 {currentPage} 页，每页 {pageSize} 条
        </Text>
        <HStack spacing={2}>
          <Button
            size="sm"
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            isDisabled={currentPage === 1}
          >
            上一页
          </Button>
          <Text fontSize="sm">
            {currentPage} / {Math.ceil(totalCount / pageSize) || 1}
          </Text>
          <Button
            size="sm"
            onClick={() => setCurrentPage(prev => prev + 1)}
            isDisabled={currentPage >= Math.ceil(totalCount / pageSize)}
          >
            下一页
          </Button>
        </HStack>
      </Flex>
    </Box>
  )
}

export default TemplateConfig

