import React, { useState, useEffect, useMemo } from "react"
import { 
  Box, 
  Text, 
  Flex, 
  Grid, 
  GridItem, 
  Input, 
  Button,
  VStack
} from "@chakra-ui/react"
import { FiSave, FiPlus, FiTrash2, FiSearch, FiEdit, FiX } from "react-icons/fi"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import useCustomToast from "../../hooks/useCustomToast"
import { getApiUrl, getAuthHeaders } from "../../client/unifiedTypes"
import { generateGUID } from "../../utils"

// 注册AG-Grid模块
ModuleRegistry.registerModules([AllCommunityModule])

// SurfaceTechnology 数据接口 - 与后端模型字段完全一致
interface SurfaceTechnology {
  surfaceTechnologyId: string
  surfaceCode: string
  surfaceDesc: string
  remark: string
  creator: string
  createDate: string
  modifierLast: string
  modifyDateLast: string
  approveStatus: string
  approver: string
  approveDate: string
  surfaceTechnologyDList?: SurfaceTechnologyD[]
}

// SurfaceTechnologyD 数据接口 - 明细数据
interface SurfaceTechnologyD {
  surfaceTechnologyDId: string
  surfaceId: string
  operationId: string
  operationCode?: string
  operationName?: string
  remark?: string
  creator: string
  createDate: string
  modifierLast?: string
  modifyDateLast?: string
  approveStatus: string
  approver?: string
  approveDate?: string
}

interface SurfaceTechnologyEditProps {
  surfaceTechnologyId?: string
  surfaceTechnologyData?: any
}

const SurfaceTechnologyEdit = ({ surfaceTechnologyId, surfaceTechnologyData: initialSurfaceTechnologyData }: SurfaceTechnologyEditProps) => {
  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  // 表面要求数据状态
  const [surfaceTechnologyData, setSurfaceTechnologyData] = useState<SurfaceTechnology>({
    surfaceTechnologyId: "",
    surfaceCode: "",
    surfaceDesc: "",
    remark: "",
    creator: "",
    createDate: "",
    modifierLast: "",
    modifyDateLast: "",
    approveStatus: "N",
    approver: "",
    approveDate: "",
    surfaceTechnologyDList:[]
  })

  // 状态管理
  const [isLoading, setIsLoading] = useState(false)
  
  // 明细数据状态
  const [detailData, setDetailData] = useState<SurfaceTechnologyD[]>([])
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [gridApi, setGridApi] = useState<any>(null)
  
  // Operation数据状态
  const [operationList, setOperationList] = useState<any[]>([])
  const [isLoadingOperations, setIsLoadingOperations] = useState(false)
  
  // Operation选择对话框状态
  const [operationDialog, setOperationDialog] = useState<{
    visible: boolean
    x: number
    y: number
    selectedOperation: any | null
    currentRowData: any | null
    isDragging: boolean
    dragOffset: { x: number; y: number }
    searchText: string
  }>({
    visible: false,
    x: 0,
    y: 0,
    selectedOperation: null,
    currentRowData: null,
    isDragging: false,
    dragOffset: { x: 0, y: 0 },
    searchText: ""
  })
  // 数据变更跟踪状态
  const [dataChanges, setDataChanges] = useState({
    headerModified: false,
    newDetails: [] as string[],
    updatedDetails: [] as string[],
    deletedDetails: [] as string[]
  })

  // 审批状态选项
  const approveStatusOptions = [
    { value: "N", label: "未审批" },
    { value: "Y", label: "已审批" },
    { value: "U", label: "审批中" },
    { value: "V", label: "审批失败" }
  ]

  // 检查是否有变更
  const hasChanges = () => {
    return dataChanges.headerModified
  }

  // 查询功能
  const handleSearch = () => {
    showInfoToast("查询功能开发中...")
  }

  // 修改功能
  const handleEdit = () => {
    if (!surfaceTechnologyData.surfaceTechnologyId) {
      showErrorToast("请先选择要修改的数据")
      return
    }
    showInfoToast("修改功能开发中...")
  }

  // 新增功能 - 创建空的 SurfaceTechnology 对象
  const newOne = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      const response = await fetch(getApiUrl('/surface-technology/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'create',
          module: 'surface-technology',
          data: { create_empty: true },
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success && result.data) {
        // 使用从后端返回的空 SurfaceTechnology 对象
        setSurfaceTechnologyData({
          ...result.data
        })
        
        // 重置变更跟踪状态
        setDataChanges({
          headerModified: true, // 标记为已修改，因为这是新增
          newDetails: [],
          updatedDetails: [],
          deletedDetails: []
        })
        
        showSuccessToast('成功创建新的 SurfaceTechnology 对象')
      } else {
        showErrorToast(result.message || '创建 SurfaceTechnology 对象失败')
      }
    } catch (error) {
      console.error('创建 SurfaceTechnology 对象失败:', error)
      showErrorToast('创建 SurfaceTechnology 对象失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 保存数据
  const save = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      // 构建保存数据
      const saveData = {
        ...surfaceTechnologyData
      }
      
      const response = await fetch(getApiUrl('/surface-technology/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'save',
          module: 'surface-technology',
          data: saveData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("保存成功")
        // 重置变更跟踪
        setDataChanges({
          headerModified: false,
          newDetails: [],
          updatedDetails: [],
          deletedDetails: []
        })
      } else {
        showErrorToast(result.message || "保存失败")
      }
    } catch (error) {
      console.error('保存失败:', error)
      showErrorToast("保存失败：" + error)
    } finally {
      setIsLoading(false)
    }
  }

  // 删除整个 SurfaceTechnology
  const handleDeleteSurfaceTechnology = async () => {
    if (!surfaceTechnologyId) {
      showErrorToast("没有可删除的数据")
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      const response = await fetch(getApiUrl('/surface-technology/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'delete',
          module: 'surface-technology',
          data: surfaceTechnologyData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("删除成功")
        // 清空数据
        setSurfaceTechnologyData({
          surfaceTechnologyId: "",
          surfaceCode: "",
          surfaceDesc: "",
          remark: "",
          creator: "",
          createDate: "",
          modifierLast: "",
          modifyDateLast: "",
          approveStatus: "N",
          approver: "",
          approveDate: ""
        })
        setDataChanges({
          headerModified: false,
          newDetails: [],
          updatedDetails: [],
          deletedDetails: []
        })
      } else {
        showErrorToast(result.message || "删除失败")
      }
    } catch (error) {
      console.error('删除失败:', error)
      showErrorToast("删除失败，请重试")
    } finally {
      setIsLoading(false)
    }
  }

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      // 调用 read 接口获取数据
      if (surfaceTechnologyId) {
        try {
          setIsLoading(true)
          
          const response = await fetch(getApiUrl('/surface-technology/unified'), {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              action: 'read',
              module: 'surface-technology',
              data: {
                surfaceTechnologyId: surfaceTechnologyId
              }
            })
          })
          
          if (response.ok) {
            const result = await response.json()
            if (result.success && result.data) {
              // 设置表面要求数据
              setSurfaceTechnologyData(result.data)
              
              console.log('页面数据初始化成功:', result.data)
              showSuccessToast('页面数据初始化成功')
            } else {
              console.error('初始化数据失败:', result.message)
              showErrorToast(`初始化数据失败: ${result.message}`)
            }
          } else {
            console.error('初始化数据请求失败:', response.status)
            showErrorToast(`初始化数据请求失败: ${response.status}`)
          }
        } catch (error) {
          console.error('初始化数据异常:', error)
          showErrorToast(`初始化数据异常: ${error}`)
        } finally {
          setIsLoading(false)
        }
      }
    }
    
    initializeData()
  }, [surfaceTechnologyId, initialSurfaceTechnologyData])

  // 加载Operation数据
  useEffect(() => {
    loadOperationList()
  }, [])

  // 处理对话框拖拽功能
  useEffect(() => {
    if (operationDialog.isDragging) {
      const handleMouseMove = (e: MouseEvent) => {
        dragOperationDialog(e)
      }
      
      const handleMouseUp = () => {
        endDragOperationDialog()
      }
      
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [operationDialog.isDragging])

  // 处理对话框外部点击关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (operationDialog.visible) {
        const operationDialogElement = document.querySelector('[data-operation-dialog]')
        if (operationDialogElement && !operationDialogElement.contains(event.target as Node)) {
          closeOperationDialog()
        }
      }
    }

    if (operationDialog.visible) {
      document.addEventListener('click', handleClickOutside)
      return () => {
        document.removeEventListener('click', handleClickOutside)
      }
    }
  }, [operationDialog.visible])

  // 监控operationDialog状态变化
  useEffect(() => {
    console.log('Operation dialog state changed:', operationDialog)
  }, [operationDialog])

  // 监听主表数据变化，自动设置明细数据到AG-Grid
  useEffect(() => {
    if (surfaceTechnologyData.surfaceTechnologyDList) {
      setDetailData(surfaceTechnologyData.surfaceTechnologyDList)
      console.log('明细数据已更新到AG-Grid:', surfaceTechnologyData.surfaceTechnologyDList)
    }
  }, [surfaceTechnologyData.surfaceTechnologyDList])

  // 表面要求数据变更处理
  const handleHeaderChange = (field: keyof SurfaceTechnology, value: any) => {
    setSurfaceTechnologyData(prev => ({
      ...prev,
      [field]: value
    }))
    setDataChanges(prev => ({
      ...prev,
      headerModified: true
    }))
  }

  // 新增明细行
  const addDetailRow = () => {
    const newDetail: SurfaceTechnologyD = {
      surfaceTechnologyDId: generateGUID(),
      surfaceId: surfaceTechnologyData.surfaceTechnologyId,
      operationId: "",
      operationCode: "",
      operationName: "",
      remark: "",
      creator: "admin",
      createDate: new Date().toISOString(),
      approveStatus: "N"
    }
    setDetailData([...detailData, newDetail])
    
    // 跟踪新增的记录
    setDataChanges(prev => ({
      ...prev,
      newDetails: [...prev.newDetails, newDetail.surfaceTechnologyDId]
    }))
    
    // 显示成功提示
    console.log("新增明细行成功，ID:", newDetail.surfaceTechnologyDId)
    showSuccessToast(`新增明细行成功，ID: ${newDetail.surfaceTechnologyDId}`)
    
    // 滚动到表格底部以显示新行
    setTimeout(() => {
      if (gridApi) {
        gridApi.ensureIndexVisible(detailData.length, 'bottom')
      }
    }, 100)
  }

  // 删除选中的明细行
  const deleteSelectedRows = () => {
    if (selectedRows.length === 0) {
      showErrorToast("请先选择要删除的行")
      return
    }

    const newDetailData = detailData.filter(item => !selectedRows.includes(item.surfaceTechnologyDId))
    setDetailData(newDetailData)
    
    // 跟踪删除的记录
    setDataChanges(prev => ({
      ...prev,
      deletedDetails: [...prev.deletedDetails, ...selectedRows]
    }))
    
    setSelectedRows([])
    showSuccessToast(`成功删除 ${selectedRows.length} 条记录`)
  }

  // 明细数据变更处理
  const handleDetailChange = (rowIndex: number, field: string, value: any) => {
    const newDetailData = [...detailData]
    newDetailData[rowIndex] = {
      ...newDetailData[rowIndex],
      [field]: value
    }
    setDetailData(newDetailData)
    
    // 跟踪更新的记录
    const detailId = newDetailData[rowIndex].surfaceTechnologyDId
    setDataChanges(prev => ({
      ...prev,
      updatedDetails: prev.updatedDetails.includes(detailId) 
        ? prev.updatedDetails 
        : [...prev.updatedDetails, detailId]
    }))
  }

  // AG-Grid 事件处理
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api)
    console.log("AG-Grid准备就绪")
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedNodes = gridApi.getSelectedNodes()
      const selectedIds = selectedNodes.map((node: any) => node.data.surfaceTechnologyDId)
      setSelectedRows(selectedIds)
    }
  }

  const onCellValueChanged = (params: any) => {
    const rowIndex = params.rowIndex
    const field = params.colDef.field
    const value = params.newValue
    
    handleDetailChange(rowIndex, field, value)
  }

  // 加载Operation数据
  const loadOperationList = async () => {
    setIsLoadingOperations(true)
    try {
      const response = await fetch(getApiUrl('/operation/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'operation',
          data: {}
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.success) {
        setOperationList(result.data || [])
        console.log(`成功加载 ${result.data?.length || 0} 条Operation数据`)
      } else {
        throw new Error(result.message || '加载Operation数据失败')
      }
    } catch (error) {
      console.error('加载Operation数据失败:', error)
      showErrorToast("无法加载Operation数据")
      
      // 添加测试数据，确保对话框有内容显示
      const testOperations = [
        { operationId: 'TEST001', operationCode: 'CUT', operationName: '切割工艺' },
        { operationId: 'TEST002', operationCode: 'WELD', operationName: '焊接工艺' },
        { operationId: 'TEST003', operationCode: 'PAINT', operationName: '喷涂工艺' }
      ]
      setOperationList(testOperations)
      console.log('使用测试Operation数据')
    } finally {
      setIsLoadingOperations(false)
    }
  }

  // 校验Operation Code是否存在
  const validateOperationCode = (operationCode: string): boolean => {
    return operationList.some(operation => operation.operationCode === operationCode)
  }

  // 根据Operation Code获取Operation ID
  const getOperationIdByCode = (operationCode: string): string => {
    const operation = operationList.find(o => o.operationCode === operationCode)
    return operation ? operation.operationId : ''
  }

  // 打开Operation选择对话框
  const openOperationDialog = (event: any, cellData: any) => {
    console.log('openOperationDialog called', { event, cellData })
    
    let rect: DOMRect
    
    // 如果是编辑状态，使用编辑输入框的位置
    if (event.target.classList && event.target.classList.contains('ag-cell-edit-input')) {
      rect = event.target.getBoundingClientRect()
    } else {
      // 否则使用点击元素的位置
      rect = event.target.getBoundingClientRect()
    }
    
    console.log('Dialog position:', { left: rect.left, top: rect.bottom + 5 })
    
    setOperationDialog({
      visible: true,
      x: rect.left,
      y: rect.bottom + 5,
      selectedOperation: null,
      currentRowData: cellData,
      isDragging: false,
      dragOffset: { x: 0, y: 0 },
      searchText: ""
    })
    
    console.log('Operation dialog state set to visible')
  }

  // 关闭Operation选择对话框
  const closeOperationDialog = () => {
    setOperationDialog(prev => ({ ...prev, visible: false }))
  }

  // 开始拖拽对话框
  const startDragOperationDialog = (e: React.MouseEvent) => {
    e.preventDefault()
    const rect = e.currentTarget.getBoundingClientRect()
    setOperationDialog(prev => ({
      ...prev,
      isDragging: true,
      dragOffset: {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
    }))
  }

  // 拖拽对话框
  const dragOperationDialog = (e: MouseEvent) => {
    if (operationDialog.isDragging) {
      setOperationDialog(prev => ({
        ...prev,
        x: e.clientX - prev.dragOffset.x,
        y: e.clientY - prev.dragOffset.y
      }))
    }
  }

  // 结束拖拽对话框
  const endDragOperationDialog = () => {
    setOperationDialog(prev => ({ ...prev, isDragging: false }))
  }

  // 选择Operation
  const selectOperation = (operation: any) => {
    console.log('selectOperation called with:', operation)
    setOperationDialog(prev => ({ ...prev, selectedOperation: operation }))
    
    // 更新当前点击的行数据
    if (operationDialog.currentRowData) {
      const currentRowData = operationDialog.currentRowData
      const rowIndex = detailData.findIndex(item => item.surfaceTechnologyDId === currentRowData.surfaceTechnologyDId)
      
      if (rowIndex !== -1) {
        const updatedDetailData = [...detailData]
        updatedDetailData[rowIndex] = {
          ...updatedDetailData[rowIndex],
          operationCode: operation.operationCode,
          operationId: operation.operationId,
          operationName: operation.operationName
        }
        
        setDetailData(updatedDetailData)
        
        // 跟踪更新的记录
        const detailId = updatedDetailData[rowIndex].surfaceTechnologyDId
        setDataChanges(prev => ({
          ...prev,
          updatedDetails: prev.updatedDetails.includes(detailId) 
            ? prev.updatedDetails 
            : [...prev.updatedDetails, detailId]
        }))
        
        console.log('Updated detailData:', updatedDetailData)
        showSuccessToast(`已选择Operation: ${operation.operationCode} - ${operation.operationName}`)
      } else {
        console.log('Row not found in detailData')
        showErrorToast("无法找到要更新的行")
      }
    } else {
      console.log('No current row data')
      showErrorToast("没有当前行数据")
    }
    
    closeOperationDialog()
  }

  // 表面要求字段定义
  const surfaceFields = [
    { key: 'surfaceCode', label: '表面代码', placeholder: '请输入表面代码' },
    { key: 'surfaceDesc', label: '表面描述', placeholder: '请输入表面描述' },
    { key: 'remark', label: '备注', placeholder: '请输入备注信息' }
  ]

    // AG-Grid 列定义
    const columnDefs: ColDef[] = useMemo(() => [
      {
        headerName: '',
        field: 'select',
        width: 60,
        checkboxSelection: true,
        headerCheckboxSelection: true
      },
      {
        headerName: '工艺编码',
        field: 'operationCode',
        width: 120,
        editable: true,
        cellEditor: 'agTextCellEditor',
        onCellClicked: (params: any) => {
          console.log('Cell clicked:', params)
          console.log('gridApi exists:', !!gridApi)
          
          // 打开对话框 - 不管gridApi是否存在
          const cellElement = params.event.target
          console.log('About to call openOperationDialog with:', { cellElement, data: params.data })
          openOperationDialog({ target: cellElement }, params.data)
          console.log('openOperationDialog called')
          
          // 如果gridApi存在，选中该行
          if (gridApi) {
            console.log('Inside gridApi check')
            // 清除之前的选择
            gridApi.deselectAll()
            // 选中当前行 - 使用正确的API
            params.node.setSelected(true)
          } else {
            console.log('gridApi is null or undefined - 对话框仍然会打开')
          }
        },
      },
      {
        headerName: '工艺描述',
        field: 'operationName',
        width: 150,
        editable: true,
        cellEditor: 'agTextCellEditor'
      },    
      {
        headerName: '备注',
        field: 'remark',
        width: 150,
        editable: true,
        cellEditor: 'agTextCellEditor'
      }
    ], [])

  // 过滤Operation列表
  const filteredOperationList = useMemo(() => {
    if (!operationDialog.searchText) {
      return operationList
    }
    return operationList.filter(operation => 
      operation.operationCode?.toLowerCase().includes(operationDialog.searchText.toLowerCase()) ||
      operation.operationName?.toLowerCase().includes(operationDialog.searchText.toLowerCase())
    )
  }, [operationList, operationDialog.searchText])

  // 处理搜索文本变化
  const handleSearchTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setOperationDialog(prev => ({ ...prev, searchText: e.target.value }))
  }
  // 分页变更事件处理
  const onPaginationChanged = (params:any) => {
    console.log('当前页码:', params.api.paginationGetCurrentPage() + 1);
    console.log('每页行数:', params.api.paginationGetPageSize());
    // TODO: 实现分页变更逻辑
  };

  return (
    <Box p={1} h="100%" display="flex" flexDirection="column">
      {/* 工具栏 */}
      <Flex 
        bg="white" 
        p={1} 
        borderRadius="lg" 
        mt={0}
        mb={1}
        border="1px"
        borderColor="e2e8f0"
        justify="flex-start"
        align="center"
        gap={3}
        boxShadow="0 1px 3px rgba(0,0,0,0.1)"
        flexShrink={0}  // 防止工具栏被压缩
      >
        <Button
          colorScheme="blue"
          variant="outline"
          size="sm"
          onClick={handleSearch}
          title="查询"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiSearch />
        </Button>
        <Button
          colorScheme="green"
          variant="outline"
          size="sm"
          onClick={newOne}
          title="新增"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
          loading={isLoading}
          loadingText="创建中..."
        >
          <FiPlus />
        </Button>
        <Button
          colorScheme="blue"
          variant="outline"
          size="sm"
          onClick={handleEdit}
          title="修改"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiEdit />
        </Button>
        <Button
          colorScheme="purple"
          variant="outline"
          size="sm"
          onClick={save}
          title="保存"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
          disabled={!hasChanges()}
          opacity={hasChanges() ? 1 : 0.5}
        >
          <FiSave />
        </Button>
        <Button
          colorScheme="red"
          variant="outline"
          size="sm"
          onClick={handleDeleteSurfaceTechnology}
          title="删除"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiTrash2 />
        </Button>
      </Flex>
       
      {/* 表头部分 */}
      <Box 
        bg="white" 
        p={1} 
        borderRadius="lg" 
        border="1px" 
        borderColor="gray.200"
        mb={1}
        flexShrink={0}
      >
        {/* 主要字段 */}
        <Grid templateColumns="repeat(3, 1fr)" gap={1} mb={1}>
          {surfaceFields.map((field) => (
            <GridItem key={field.key}>
              <Flex align="center" gap={2}>
                <Text fontSize="sm" fontWeight="medium" minW="80px">{field.label}</Text>
                <Input
                  value={typeof surfaceTechnologyData[field.key as keyof SurfaceTechnology] === 'string' 
                    ? (surfaceTechnologyData[field.key as keyof SurfaceTechnology] as string) || '' 
                    : ''}
                  onChange={(e) => handleHeaderChange(field.key as keyof SurfaceTechnology, e.target.value)}
                  placeholder={field.placeholder}
                  size="sm"
                  flex="1"
                />
              </Flex>
            </GridItem>
          ))}
        </Grid>
        
      </Box>

      {/* 明细数据操作工具栏 */}
      <Flex 
        bg="gray.50" 
        p={1} 
        borderRadius="md" 
        mb={1}
        border="1px"
        borderColor="gray.200"
        justify="space-between"
        align="center"
        flexShrink={0}
      >
        <Flex align="center" gap={2}>
          <Text fontSize="sm" fontWeight="medium" color="gray.700">
            明细数据
          </Text>
          <Text fontSize="xs" color="gray.500">
            ({detailData.length} 条)
          </Text>
          {selectedRows.length > 0 && (
            <Flex align="center" gap={1} px={1.5} py={0.5} bg="blue.100" borderRadius="sm">
              <Text fontSize="xs" color="blue.700" fontWeight="medium">
                已选 {selectedRows.length}
              </Text>
            </Flex>
          )}
          {hasChanges() && (
            <Flex align="center" gap={1} px={1.5} py={0.5} bg="orange.100" borderRadius="sm">
              <Text fontSize="xs" color="orange.700" fontWeight="medium">
                有变更
              </Text>
            </Flex>
          )}
        </Flex>
        
        <Flex gap={1.5} align="center">
          {isLoading && (
            <Flex align="center" gap={1} px={1.5} py={0.5} bg="blue.50" borderRadius="sm">
              <Box
                width="2"
                height="2"
                borderRadius="full"
                bg="blue.500"
                animation="pulse 1.5s infinite"
              />
              <Text fontSize="xs" color="blue.600">处理中</Text>
            </Flex>
          )}
          <Button
            colorScheme="green"
            variant="outline"
            size="sm"
            onClick={addDetailRow}
            title="新增"
            minW="36px"
            height="26px"
            fontSize="11px"
            px={1.5}
            borderRadius="md"
          >
            <FiPlus size={11} />
          </Button>
          
          <Button
            colorScheme="red"
            variant="outline"
            size="sm"
            onClick={deleteSelectedRows}
            title="删除"
            minW="36px"
            height="26px"
            fontSize="11px"
            px={1.5}
            borderRadius="md"
            disabled={selectedRows.length === 0}
            opacity={selectedRows.length === 0 ? 0.5 : 1}
          >
            <FiTrash2 size={11} />
          </Button>
        </Flex>
      </Flex>

      {/* AG-Grid 数据表格 */}
      <Box
        className="ag-theme-alpine"
        width="100%"
        flex="0.90"
        minH="0"
        position="relative"
        overflow="hidden"
        border="1px"
        borderColor="gray.200"
        borderRadius="md"
      >
        {isLoading && (
          <Box
            position="absolute"
            top="50%"
            left="50%"
            transform="translate(-50%, -50%)"
            zIndex={10}
            bg="white"
            p={4}
            borderRadius="md"
            boxShadow="lg"
            border="1px"
            borderColor="gray.200"
          >
            <Flex align="center" gap={2}>
              <Box
                width="4"
                height="4"
                borderRadius="full"
                bg="blue.500"
                animation="pulse 1.5s infinite"
              />
              <Text fontSize="sm" color="gray.600">加载明细数据中...</Text>
            </Flex>
          </Box>
        )}
        <AgGridReact
          theme="legacy"
          columnDefs={columnDefs}
          rowData={detailData}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          onCellValueChanged={onCellValueChanged}
          rowSelection={{ mode: 'multiRow' }}
          pagination={true}
          paginationPageSize={10}
          suppressRowClickSelection={true}
          animateRows={true}
          editType="fullRow"
          stopEditingWhenCellsLoseFocus={true}
          paginationPageSizeSelector={[10, 20, 50]}
          onPaginationChanged={onPaginationChanged}
        />
      </Box>

      {/* Operation选择对话框 */}
      {operationDialog.visible && (
        <Box
          position="fixed"
          left={operationDialog.x}
          top={operationDialog.y}
          bg="white"
          border="1px"
          borderColor="gray.200"
          borderRadius="md"
          boxShadow="lg"
          zIndex={9999}
          minW="400px"
          maxH="300px"
          overflow="hidden"
          data-operation-dialog
          style={{ pointerEvents: 'auto' }}
        >
          <Flex 
            bg="gray.50" 
            p={2} 
            borderBottom="1px" 
            borderColor="gray.200"
            justify="space-between"
            align="center"
            cursor="move"
            onMouseDown={startDragOperationDialog}
            userSelect="none"
          >
            <Text fontSize="sm" fontWeight="medium">选择Operation</Text>
            <Button
              size="xs"
              variant="ghost"
              onClick={closeOperationDialog}
              onMouseDown={(e) => e.stopPropagation()}
            >
              <FiX />
            </Button>
          </Flex>
          
          <Box p={2} borderBottom="1px" borderColor="gray.200">
            <Input
              placeholder="搜索工艺编码或描述..."
              value={operationDialog.searchText}
              onChange={handleSearchTextChange}
              size="sm"
              borderRadius="md"
              borderColor="gray.300"
              _focus={{ borderColor: "blue.300", boxShadow: "0 0 0 1px blue.300" }}
            />
          </Box>
          
          <Box maxH="200px" overflowY="auto">
            <VStack align="stretch" gap={0}>
              {isLoadingOperations ? (
                <Flex justify="center" align="center" h="50px">
                  <VStack gap={2}>
                    <Box
                      width="4"
                      height="4"
                      borderRadius="full"
                      bg="blue.500"
                      animation="pulse 1.5s infinite"
                    />
                    <Text fontSize="sm" color="gray.600">加载Operation数据中...</Text>
                  </VStack>
                </Flex>
              ) : filteredOperationList.length === 0 ? (
                <Flex justify="center" align="center" h="50px">
                  <Text fontSize="sm" color="gray.500">暂无Operation数据</Text>
                </Flex>
              ) : (
                filteredOperationList.map((operation) => (
                  <Flex
                    key={operation.operationId}
                    p={2}
                    cursor="pointer"
                    _hover={{ bg: "blue.50" }}
                    onClick={() => selectOperation(operation)}
                    borderBottom="1px"
                    borderColor="gray.100"
                  >
                    <Text fontSize="sm" flex="1" fontWeight="medium">
                      {operation.operationCode}
                    </Text>
                    <Text fontSize="sm" flex="2" color="gray.600">
                      {operation.operationName}
                    </Text>
                  </Flex>
                ))
              )}
            </VStack>
          </Box>
        </Box>
      )}
    </Box>
  )
}

export default SurfaceTechnologyEdit 