import { 
  Box, 
  Text, 
  Flex, 
  VStack, 
  Button, 
  Icon,
  Grid,
  GridItem,
  Input
} from "@chakra-ui/react"
import { 
  FiPlus, 
  FiEdit, 
  FiTrash2,
  FiFolder,
  FiChevronRight,
  FiChevronDown,
  FiSave,
  FiX
} from "react-icons/fi"
import { useState, useEffect, useMemo, useCallback } from "react"
import useCustomToast from '../../hooks/useCustomToast'
import { UnifiedResponse, MaterialClassListRequest, MaterialClassRequest, MaterialClassDeleteRequest } from '@/client/unifiedTypes'
import SelectInput from '../Common/SelectInput'
import TableSelectDialog, { TableColumn, TableDataRow } from '../Common/TableSelectDialog'

import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { generateGUID } from "@/utils"

// 注册AG-Grid模块 - 包含所有社区功能
ModuleRegistry.registerModules([AllCommunityModule])

// 树节点接口
interface TreeNode {
  id: string
  parentId: string | null
  name: string
  description: string
  children?: TreeNode[]
  isExpanded?: boolean
}

// 表头数据接口 - 对应 material_class 表
interface MaterialClass {
  materialClassId: string
  materialClassPId: string
  classCode: string
  classDesc: string
  remark?: string
  creator: string
  createDate: string
  modifierLast?: string
  modifyDateLast?: string
  approveStatus: string
  approver?: string
  approveDate?: string
  materialClassDList: MaterialClassD[]
  materialClassPCode: string
  materialClassPDesc: string
}

// 明细数据接口 - 对应 material_class_d 表
interface MaterialClassD {
  materialClassDId: string
  materialClassId: string
  featureId: string
  featureCode: string // 新增字段，用于显示和编辑
  featureValue: string
  position: number
  remark?: string
  creator: string
  createDate: string
  modifierLast?: string
  modifyDateLast?: string
  approveStatus: string
  approver?: string
  approveDate?: string
}

// 右键菜单项接口（暂时保留，可能在未来使用）
// interface ContextMenuItem {
//   label: string
//   icon: React.ReactElement
//   action: () => void
// }

const MaterialClassEdit = () => {
  const [treeData, setTreeData] = useState<TreeNode[]>([])
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null)
  const [contextMenu, setContextMenu] = useState<{
    visible: boolean
    x: number
    y: number
    node: TreeNode | null
  }>({
    visible: false,
    x: 0,
    y: 0,
    node: null
  })
  
  // 表头数据状态
  const [materialClassData, setMaterialClassData] = useState<MaterialClass>({
    materialClassId: "",
    materialClassPId: "",
    materialClassPCode: "",
    materialClassPDesc: "",
    classCode: "",
    classDesc: "",
    remark: "",
    creator: "",
    createDate: "",
    modifierLast: "",
    modifyDateLast: "",
    approveStatus: "N",
    approver: "",
    approveDate: "",
    materialClassDList: []
  })

  // 明细数据状态
  const [detailData, setDetailData] = useState<MaterialClassD[]>([])
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [gridApi, setGridApi] = useState<any>(null)
  
  // Feature数据状态
  const [featureList, setFeatureList] = useState<any[]>([])
  const [isLoadingFeatures, setIsLoadingFeatures] = useState(false)
  
  // Feature选择对话框状态
  const [featureDialog, setFeatureDialog] = useState<{
    visible: boolean
    x: number
    y: number
    selectedFeature: any | null
    isDragging: boolean
    dragOffset: { x: number; y: number }
  }>({
    visible: false,
    x: 0,
    y: 0,
    selectedFeature: null,
    isDragging: false,
    dragOffset: { x: 0, y: 0 }
  })
  
  // 通用表格选择对话框状态
  const [tableDialog, setTableDialog] = useState<{
    visible: boolean
    x: number
    y: number
    isDragging: boolean
    dragOffset: { x: number; y: number }
    currentEditingCell: any | null
  }>({
    visible: false,
    x: 0,
    y: 0,
    isDragging: false,
    dragOffset: { x: 0, y: 0 },
    currentEditingCell: null
  })
  
  // 表格对话框的配置状态
  const [tableDialogConfig, setTableDialogConfig] = useState<{
    data?: TableDataRow[]
    columns: TableColumn[]
    apiConfig?: any
    filterConfig?: any
    displayConfig?: any
    returnConfig?: any
    loading: boolean
  }>({
    columns: [],
    loading: false
  })
  
  // 使用真实的toast
  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  const showToast = (_title: string, description: string, type: 'success' | 'info' | 'warning' | 'error' = 'info') => {
    switch (type) {
      case 'success':
        showSuccessToast(description)
        break
      case 'error':
        showErrorToast(description)
        break
      case 'warning':
      case 'info':
      default:
        showInfoToast(description)
        break
    }
  }

  // 创建初始化的MaterialClass对象
  const createInitialMaterialClass = (nodeId: string, parentId: string | null, nodeType: 'root' | 'sibling' | 'child'): MaterialClass => {
    const typePrefix = nodeType === 'root' ? '新根' : nodeType === 'sibling' ? '新同级' : '新子'
    
    return {
      materialClassId: nodeId,
      materialClassPId: parentId || "",
      classCode: `${typePrefix}编码`,
      classDesc: `${typePrefix}描述`,
      remark: "",
      creator: "",
      createDate: new Date().toISOString(),
      modifierLast: "",
      modifyDateLast: "",
      approveStatus: "N",
      approver: "",
      approveDate: "",
      materialClassDList: [],
      materialClassPCode: "",
      materialClassPDesc: ""
    }
  }

  // 从后端获取树数据的函数
  const loadTreeData = async () => {
    setIsLoading(true)
    try {
      // 获取access token
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('未登录，请先登录')
      }

      const requestData: MaterialClassListRequest = {
        action: 'list',
        module: 'material-class',
        data: {}
      }

      const response = await fetch('/api/v1/material-class/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result: UnifiedResponse<MaterialClass[]> = await response.json()
      
      if (result.success && result.data) {
        // 将后端数据转换为树节点格式
        const treeNodes: TreeNode[] = result.data.map((item: MaterialClass) => ({
          id: item.materialClassId,
          parentId: item.materialClassPId || null,
          name: item.classCode,
          description: item.classDesc
        }))
        
        const tree = buildTreeStructure(treeNodes)
        setTreeData(tree)
        showToast("加载成功", `成功加载 ${treeNodes.length} 条物料类别数据`, "success")
      } else {
        throw new Error(result.message || '加载数据失败')
      }
    } catch (error) {
      console.error('加载树数据失败:', error)
      
      if (error instanceof Error && error.message === '未登录，请先登录') {
        showToast("认证失败", "请先登录系统", "error")
      } else {
        showToast("加载失败", "无法从后端加载物料类别数据", "error")
      }
    } finally {
      setIsLoading(false)
    }
  }

  // 构建树结构
  const buildTreeStructure = (flatData: TreeNode[]): TreeNode[] => {
    const map = new Map<string, TreeNode>()
    const roots: TreeNode[] = []

    flatData.forEach(item => {
      map.set(item.id, { ...item, children: [], isExpanded: false })
    })

    flatData.forEach(item => {
      const node = map.get(item.id)!
      if (item.parentId && map.has(item.parentId)) {
        const parent = map.get(item.parentId)!
        parent.children!.push(node)
      } else {
        roots.push(node)
      }
    })

    return roots
  }

  // 切换节点展开状态
  const toggleNode = (nodeId: string, nodes: TreeNode[]): TreeNode[] => {
    return nodes.map(node => {
      if (node.id === nodeId) {
        return { ...node, isExpanded: !node.isExpanded }
      }
      if (node.children) {
        return { ...node, children: toggleNode(nodeId, node.children) }
      }
      return node
    })
  }

  // 选择节点
  const selectNode = (node: TreeNode) => {
    setSelectedNode(node)
    setContextMenu(prev => ({ ...prev, visible: false }))
    
    // 加载对应的表头数据
    loadMaterialClassData(node.id)
  }

  // 加载表头数据
  const loadMaterialClassData = async (nodeId: string) => {
    setIsLoading(true)
    try {
      // 获取access token
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('未登录，请先登录')
      }

      // 调用API加载指定节点的数据
      const requestData: MaterialClassDeleteRequest = {
        action: 'read',
        module: 'material-class',
        data: {
          materialClassId: nodeId
        }
      }

      const response = await fetch('/api/v1/material-class/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result: UnifiedResponse<MaterialClass> = await response.json()
      console.log('getOneByKey API响应:', result)
      
      if (result.success && result.data) {
        // getOneByKey返回的是单个MaterialClass对象
        const materialClass: MaterialClass = result.data
        
        console.log('完整的API响应数据:', materialClass)
        console.log('materialClass.materialClassDList:', materialClass.materialClassDList)
        console.log('materialClass.materialClassDList类型:', typeof materialClass.materialClassDList)
        console.log('materialClass.materialClassDList是否为数组:', Array.isArray(materialClass.materialClassDList))
        
        // 直接使用返回的数据，因为它已经包含了materialClassDList
        setMaterialClassData(materialClass)
        
        // 同时设置明细数据
        const detailList = materialClass.materialClassDList || []
        console.log('设置明细数据:', detailList)
        console.log('明细数据类型:', typeof detailList)
        console.log('明细数据长度:', detailList.length)
        if (detailList.length > 0) {
          console.log('第一条明细数据:', detailList[0])
        }
        setDetailData(detailList)
        
        showToast("加载成功", `成功加载物料类别: ${materialClass.classCode}`, "success")
      } else {
        console.error('API返回失败:', result)
        throw new Error(result.message || '未找到指定的物料类别数据')
      }
      
    } catch (error) {
      console.error('加载表头数据失败:', error)
      
      if (error instanceof Error && error.message === '未登录，请先登录') {
        showToast("认证失败", "请先登录系统", "error")
      } else if (error instanceof Error && error.message === '未找到指定的物料类别数据') {
        showToast("数据不存在", "未找到指定的物料类别数据", "warning")
      } else {
        showToast("加载失败", "无法加载物料类别数据", "error")
      }
    } finally {
      setIsLoading(false)
    }
  }

  // 加载Feature数据
  const loadFeatureList = async () => {
    setIsLoadingFeatures(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('未登录，请先登录')
      }

      const response = await fetch('/api/v1/feature/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          action: 'list',
          module: 'feature',
          data: {}
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.success) {
        setFeatureList(result.data || [])
        console.log(`成功加载 ${result.data?.length || 0} 条Feature数据`)
      } else {
        throw new Error(result.message || '加载Feature数据失败')
      }
    } catch (error) {
      console.error('加载Feature数据失败:', error)
      showToast("加载失败", "无法加载Feature数据", "error")
      
      // 添加测试数据，确保对话框有内容显示
      const testFeatures = [
        { featureId: 'TEST001', featureCode: 'COLOR', featureDesc: '颜色属性' },
        { featureId: 'TEST002', featureCode: 'SIZE', featureDesc: '尺寸属性' },
        { featureId: 'TEST003', featureCode: 'MATERIAL', featureDesc: '材质属性' }
      ]
      setFeatureList(testFeatures)
      console.log('使用测试Feature数据')
    } finally {
      setIsLoadingFeatures(false)
    }
  }

  // 校验Feature Code是否存在
  const validateFeatureCode = (featureCode: string): boolean => {
    return featureList.some(feature => feature.featureCode === featureCode)
  }

  // 根据Feature Code获取Feature ID
  const getFeatureIdByCode = (featureCode: string): string => {
    const feature = featureList.find(f => f.featureCode === featureCode)
    return feature ? feature.featureId : ''
  }

  // 打开Feature选择对话框（暂时未使用，保留以备后用）
  // const openFeatureDialog = (event: any, cellData: any) => {
  //   console.log('openFeatureDialog called', { event, cellData })
  //   
  //   let rect: DOMRect
  //   
  //   // 如果是编辑状态，使用编辑输入框的位置
  //   if (event.target.classList && event.target.classList.contains('ag-cell-edit-input')) {
  //     rect = event.target.getBoundingClientRect()
  //   } else {
  //     // 否则使用点击元素的位置
  //     rect = event.target.getBoundingClientRect()
  //   }
  //   
  //   console.log('Dialog position:', { left: rect.left, top: rect.bottom + 5 })
  //   
  //   setFeatureDialog({
  //     visible: true,
  //     x: rect.left,
  //     y: rect.bottom + 5,
  //     selectedFeature: null,
  //     isDragging: false,
  //     dragOffset: { x: 0, y: 0 }
  //   })
  //   
  //   console.log('Feature dialog state set to visible')
  // }

  // 关闭Feature选择对话框
  const closeFeatureDialog = () => {
    setFeatureDialog(prev => ({ ...prev, visible: false }))
  }

  // 开始拖拽对话框
  const startDragDialog = (e: React.MouseEvent) => {
    e.preventDefault()
    const rect = e.currentTarget.getBoundingClientRect()
    setFeatureDialog(prev => ({
      ...prev,
      isDragging: true,
      dragOffset: {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
    }))
  }

  // 拖拽对话框
  const dragDialog = (e: MouseEvent) => {
    if (featureDialog.isDragging) {
      setFeatureDialog(prev => ({
        ...prev,
        x: e.clientX - prev.dragOffset.x,
        y: e.clientY - prev.dragOffset.y
      }))
    }
  }

  // 结束拖拽对话框
  const endDragDialog = () => {
    setFeatureDialog(prev => ({ ...prev, isDragging: false }))
  }

  // 选择Feature
  const selectFeature = (feature: any) => {
    console.log('selectFeature called with:', feature)
    setFeatureDialog(prev => ({ ...prev, selectedFeature: feature }))
    
    // 简化逻辑：直接更新第一行数据
    if (detailData.length > 0) {
      const firstRow = detailData[0]
      const updatedData = { ...firstRow }
      updatedData.featureCode = feature.featureCode
      updatedData.featureId = feature.featureId
      
      const updatedDetailData = detailData.map((item, index) => {
        if (index === 0) {
          return updatedData
        }
        return item
      })
      setDetailData(updatedDetailData)
      
      console.log('Updated detailData:', updatedDetailData)
      
      // 尝试刷新AG-Grid显示（如果可用）
      if (gridApi && typeof gridApi.setRowData === 'function') {
        try {
          gridApi.setRowData(updatedDetailData)
          console.log('AG-Grid data updated successfully')
        } catch (error) {
          console.log('AG-Grid update failed:', error)
        }
      } else {
        console.log('AG-Grid API not available, only local state updated')
      }
      
      showToast("选择成功", `已选择Feature: ${feature.featureCode} - ${feature.featureDesc}`, "success")
    } else {
      console.log('No detail data available')
      showToast("选择失败", "没有可更新的数据行", "error")
    }
    
    closeFeatureDialog()
  }

  // 表格对话框相关函数
  
  // 打开表格选择对话框（新版本，支持配置）
  const openTableDialogWithConfig = (event: any, cellData: any, config: any) => {
    let rect: DOMRect
    
    // 使用视窗中心作为对话框位置
    rect = {
      left: window.innerWidth / 2 - 300,
      top: window.innerHeight / 2 - 200,
      bottom: window.innerHeight / 2 + 200,
      right: window.innerWidth / 2 + 300,
      width: 600,
      height: 400
    } as DOMRect
    
    console.log('使用视窗中心位置:', rect)
    
    // 设置对话框配置
    setTableDialogConfig({
      data: config.data,
      columns: config.columns,
      apiConfig: config.apiConfig,
      filterConfig: config.filterConfig,
      displayConfig: config.displayConfig,
      returnConfig: config.returnConfig,
      loading: false
    })
    
    // 直接使用视窗中心位置，确保对话框可见
    const dialogX = Math.max(50, Math.min(rect.left, window.innerWidth - 650))
    const dialogY = Math.max(50, Math.min(rect.top, window.innerHeight - 450))
    
    console.log('对话框位置:', { dialogX, dialogY, windowWidth: window.innerWidth, windowHeight: window.innerHeight })
    
    setTableDialog({
      visible: true,
      x: dialogX,
      y: dialogY,
      isDragging: false,
      dragOffset: { x: 0, y: 0 },
      currentEditingCell: cellData
    })
  }

  // 打开表格选择对话框（旧版本，保持兼容性）
  const openTableDialog = (event: any, cellData: any, data: TableDataRow[], columns: TableColumn[]) => {
    let rect: DOMRect
    
    // 使用视窗中心作为对话框位置
    rect = {
      left: window.innerWidth / 2 - 300,
      top: window.innerHeight / 2 - 200,
      bottom: window.innerHeight / 2 + 200,
      right: window.innerWidth / 2 + 300,
      width: 600,
      height: 400
    } as DOMRect
    
    console.log('使用视窗中心位置:', rect)
    
    // 设置对话框数据和列
    setTableDialogConfig({
      data: data,
      columns: columns,
      loading: false
    })
    
    // 直接使用视窗中心位置，确保对话框可见
    const dialogX = Math.max(50, Math.min(rect.left, window.innerWidth - 650))
    const dialogY = Math.max(50, Math.min(rect.top, window.innerHeight - 450))
    
    console.log('对话框位置:', { dialogX, dialogY, windowWidth: window.innerWidth, windowHeight: window.innerHeight })
    
    setTableDialog({
      visible: true,
      x: dialogX,
      y: dialogY,
      isDragging: false,
      dragOffset: { x: 0, y: 0 },
      currentEditingCell: cellData
    })
  }

  // 关闭表格选择对话框
  const closeTableDialog = () => {
    setTableDialog(prev => ({ ...prev, visible: false, currentEditingCell: null }))
  }

  // 开始拖拽表格对话框
  const startDragTableDialog = (e: React.MouseEvent) => {
    e.preventDefault()
    const rect = e.currentTarget.getBoundingClientRect()
    setTableDialog(prev => ({
      ...prev,
      isDragging: true,
      dragOffset: {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
    }))
  }

  // 拖拽表格对话框
  const dragTableDialog = (e: MouseEvent) => {
    if (tableDialog.isDragging) {
      setTableDialog(prev => ({
        ...prev,
        x: e.clientX - prev.dragOffset.x,
        y: e.clientY - prev.dragOffset.y
      }))
    }
  }

  // 结束拖拽表格对话框
  const endDragTableDialog = () => {
    setTableDialog(prev => ({ ...prev, isDragging: false }))
  }

  // 处理表格对话框选择
  const handleTableDialogSelect = (selectedRows: TableDataRow[], selectedRow?: TableDataRow) => {
    console.log('handleTableDialogSelect called', { selectedRows, selectedRow })
    
    if (selectedRow && tableDialog.currentEditingCell) {
      // 获取当前编辑的单元格信息
      const editingCell = tableDialog.currentEditingCell
      const columnId = editingCell.column.getColId()
      
      // 根据返回值配置获取要设置的值
      let valueToAssign = selectedRow
      if (tableDialogConfig.returnConfig?.returnTransformer) {
        valueToAssign = tableDialogConfig.returnConfig.returnTransformer(selectedRow)
      } else if (tableDialogConfig.returnConfig?.returnFields) {
        const result: any = {}
        tableDialogConfig.returnConfig.returnFields.forEach((field: string) => {
          result[field] = selectedRow[field]
        })
        valueToAssign = result
      }
      
      console.log('Assigning value to cell:', valueToAssign)
      
      // 更新 AG-Grid 中的单元格值
      if (gridApi) {
        const rowNode = editingCell.node
        const newData = { ...rowNode.data }
        
        // 根据列ID设置相应的值
        if (columnId === 'featureCode') {
          newData.featureCode = valueToAssign.featureCode || valueToAssign.code || valueToAssign
          newData.featureId = valueToAssign.featureId || valueToAssign.id
          newData.featureDesc = valueToAssign.featureDesc || valueToAssign.description
        }
        
        // 更新行数据
        rowNode.setData(newData)
        
        // 刷新单元格显示
        gridApi.refreshCells({ 
          rowNodes: [rowNode], 
          columns: [columnId],
          force: true 
        })
        
        showToast("选择成功", `已选择特征: ${newData.featureCode}`, "success")
      } else {
        console.log('AG-Grid API not available, only local state updated')
        showToast("选择成功", `已选择数据`, "success")
      }
    }
    
    closeTableDialog()
  }

  // 处理表格对话框双击
  const handleTableDialogDoubleClick = (row: TableDataRow, index: number) => {
    console.log('handleTableDialogDoubleClick called', { row, index })
    handleTableDialogSelect([row], row)
  }

  // 保存数据
  const saveData = async () => {
    if (!selectedNode) {
      showToast("保存失败", "请先选择一个物料类别", "error")
      return
    }

    setIsLoading(true)
    try {
      // 获取access token
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('未登录，请先登录')
      }

      // 创建要保存的数据对象，不直接修改状态
      const saveData = {
        ...materialClassData,
        materialClassDList: detailData
      }
      
      console.log('保存数据:', saveData)
      console.log('materialClassDList类型:', typeof saveData.materialClassDList)
      console.log('materialClassDList长度:', saveData.materialClassDList?.length)
      console.log('materialClassDList内容:', saveData.materialClassDList)

      const requestData: MaterialClassRequest = {
        action: 'save',
        module: 'material-class',
        data: saveData
      }

      const response = await fetch('/api/v1/material-class/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result: UnifiedResponse<MaterialClass> = await response.json()
      console.log('保存API响应:', result)
      
      if (result.success && result.data) {
        showToast("保存成功", result.message || "数据保存成功", "success")
        
        // 如果保存成功，重新加载数据以获取最新的ID
        if (selectedNode) {
          await loadMaterialClassData(selectedNode.id)
        }
      } else {
        throw new Error(result.message || '保存失败')
      }
      
    } catch (error) {
      console.error('保存数据失败:', error)
      
      if (error instanceof Error && error.message === '未登录，请先登录') {
        showToast("认证失败", "请先登录系统", "error")
      } else {
        showToast("保存失败", error instanceof Error ? error.message : "保存数据时发生错误", "error")
      }
    } finally {
      setIsLoading(false)
    }
  }

  

  // 处理表头数据变更
  const handleHeaderChange = (field: keyof MaterialClass, value: any) => {
    setMaterialClassData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // AG-Grid列定义
  const columnDefs: ColDef[] = useMemo(() => [
    {
      headerName: '选择',
      field: 'select',
      width: 40,
      checkboxSelection: true,
      headerCheckboxSelection: true,
      sortable: false,
      filter: false,
      resizable: false,
      editable: false
    },
    {
      headerName: '属性ID',
      field: 'featureId',
      width: 0,
      hide: true,
      editable: false,
      suppressMenu: true,
      suppressMovable: true,
      suppressSizeToFit: true,
      suppressAutoSize: true
    },
    { 
      headerName: '行号', 
      field: 'seq', 
      width: 70,   
      valueGetter: (params) => {
        // 获取行号，格式化为4位数字（0001, 0002, ...）
        const rowIndex = params.node?.rowIndex || 0;
        return String(rowIndex + 1).padStart(4, '0');
      }
    },
    { 
      headerName: '属性代码', 
      field: 'featureCode',
      width: 80,
      sortable: true,
      filter: true,
      editable: true,
      cellEditor: 'agTextCellEditor',
      cellEditorParams: {
        maxLength: 10
      },
           
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '属性描述', 
      field: 'featureDesc',
      width: 100,
      cellEditor: 'agTextCellEditor',
      cellEditorParams: {
        maxLength: 50
      }
    },
    { 
      headerName: '属性值', 
      field: 'featureValue', 
      width: 120,
      sortable: true,
      filter: true,
      editable: true,
      cellEditor: 'agTextCellEditor',
      cellEditorParams: {
        maxLength: 100
      },
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '位置', 
      field: 'position', 
      width: 80,
      sortable: true,
      filter: true,
      editable: true,
      cellEditor: 'agNumberCellEditor',
      filterParams: {
        filterOptions: ['equals', 'greaterThan', 'lessThan']
      }
    },
    { 
      headerName: '备注', 
      field: 'remark', 
      width: 150,
      sortable: true,
      filter: true,
      editable: true,
      cellEditor: 'agTextCellEditor',
      cellEditorParams: {
        maxLength: 200
      },
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    }
  ], [])

  // AG-Grid事件处理
  const onGridReady = (params: GridReadyEvent) => {
    console.log('AG-Grid ready, API:', params.api)
    console.log('AG-Grid API methods:', Object.getOwnPropertyNames(params.api))
    console.log('AG-Grid rowData:', params.api.getRenderedNodes())
    console.log('AG-Grid rowCount:', params.api.getDisplayedRowCount())
    setGridApi(params.api)
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedRows = gridApi.getSelectedRows()
      const selectedIds = selectedRows.map((row: any) => row.materialClassDId)
      setSelectedRows(selectedIds)
    }
  }

  // 单元格编辑完成事件
  const onCellValueChanged = (event: any) => {
    const { data, field, newValue } = event
    
    // 如果是featureCode字段，进行校验并自动设置featureId
    if (field === 'featureCode' && newValue) {
      if (!validateFeatureCode(newValue)) {
        showToast("校验失败", `Feature Code "${newValue}" 不存在，请选择有效的属性代码`, "warning")
        // 可以选择是否回滚到原值
        // event.api.undoCellEditing()
      } else {
        // 获取对应的featureId并设置
        const featureId = getFeatureIdByCode(newValue)
        if (featureId) {
          // 更新featureId字段
          const updatedData = detailData.map(item => {
            if (item.materialClassDId === data.materialClassDId) {
              return { ...item, featureCode: newValue, featureId: featureId }
            }
            return item
          })
          setDetailData(updatedData)
          
          // 刷新AG-Grid以显示更新后的featureId
          if (gridApi) {
            gridApi.refreshCells({ force: true })
          }
          
          showToast("校验成功", `Feature Code "${newValue}" 验证通过，已设置Feature ID: ${featureId}`, "success")
        }
        return // 提前返回，避免重复更新
      }
    }
    
    // 更新本地数据
    const updatedData = detailData.map(item => {
      if (item.materialClassDId === data.materialClassDId) {
        return { ...item, [field]: newValue }
      }
      return item
    })
    setDetailData(updatedData)
  }

  // 添加明细行
  const addDetailRow = () => {
    const newDetail: MaterialClassD = {
      materialClassDId: `new-${generateGUID()}`, // 使用GUID生成唯一ID
      materialClassId: materialClassData.materialClassId,
      featureId: "",
      featureCode: "",
      featureValue: "",
      position: detailData.length + 1,
      remark: "",
      creator: "admin",
      createDate: new Date().toISOString(),
      modifierLast: "",
      modifyDateLast: "",
      approveStatus: "N",
      approver: "",
      approveDate: ""
    }
    setDetailData([...detailData, newDetail])
    
    // 显示成功提示
    console.log("新增明细行成功，ID:", newDetail.materialClassDId)
    showToast("新增明细行", `新增明细行成功，ID: ${newDetail.materialClassDId}`, "success")
    
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
      console.log("请先选择要删除的行")
      showToast("删除", "请先选择要删除的行", "info")
      return
    }
    
    const newDetailData = detailData.filter(item => !selectedRows.includes(item.materialClassDId))
    setDetailData(newDetailData)
    setSelectedRows([])
    
    console.log(`已删除 ${selectedRows.length} 行明细数据`)
    showToast("删除", `已删除 ${selectedRows.length} 行明细数据`, "success")
  }

  // 右键菜单处理
  const handleContextMenu = (e: React.MouseEvent, node?: TreeNode) => {
    e.preventDefault()
    console.log("右键菜单处理", { node: node?.name || "空白区域" })
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      node: node || null
    })
  }

  // 关闭右键菜单
  const closeContextMenu = () => {
    setContextMenu(prev => ({ ...prev, visible: false }))
  }

  // 新增同级节点
  const addNode = () => {
    console.log("addNode函数被调用")
    console.log("contextMenu.node:", contextMenu.node)
    
    if (!contextMenu.node) {
      console.log("contextMenu.node为空，函数返回")
      return
    }
    
    const newNode: TreeNode = {
      id: `new-${Date.now()}`, // 使用new-前缀标识新节点
      parentId: contextMenu.node.parentId, // 与当前节点同级
      name: "新同级节点",
      description: "新同级节点描述",
      children: [],
      isExpanded: false
    }

    // 初始化新的MaterialClass对象
    const newMaterialClass = createInitialMaterialClass(newNode.id, contextMenu.node.parentId, 'sibling')
    
    // 在父节点的children中添加新节点
    const addToParentChildren = (nodes: TreeNode[], parentId: string | null, newNode: TreeNode): TreeNode[] => {
      if (parentId === null) {
        // 根级别节点
        return [...nodes, newNode]
      }
      
      return nodes.map(node => {
        if (node.id === parentId) {
          // 找到父节点，添加子节点
          return {
            ...node,
            children: [...(node.children || []), newNode]
          }
        } else if (node.children && node.children.length > 0) {
          // 递归查找子节点
          return {
            ...node,
            children: addToParentChildren(node.children, parentId, newNode)
          }
        }
        return node
      })
    }

    // 更新树数据
    setTreeData(prevTreeData => {
      const updatedTree = addToParentChildren(prevTreeData, contextMenu.node!.parentId, newNode)
      console.log("树数据已更新，同级节点已添加")
      return updatedTree
    })

    // 选中新节点并设置数据
    setSelectedNode(newNode)
    setMaterialClassData(newMaterialClass)
    setDetailData(newMaterialClass.materialClassDList)

    showToast("新增同级节点", `在 ${contextMenu.node.name} 同级新增节点`, "success")

    closeContextMenu()
  }

  // 新增子节点
  const addSubNode = () => {
    console.log("addSubNode函数被调用")
    console.log("contextMenu.node:", contextMenu.node)
    
    if (!contextMenu.node) {
      console.log("contextMenu.node为空，函数返回")
      return
    }
    
    const newNode: TreeNode = {
      id: `new-${Date.now()}`, // 使用new-前缀标识新节点
      parentId: contextMenu.node.id,
      name: "新子节点",
      description: "新子节点描述",
      children: [],
      isExpanded: false
    }

    // 初始化新的MaterialClass对象
    const newMaterialClass = createInitialMaterialClass(newNode.id, contextMenu.node.id, 'child')

    // 更新树数据，添加新节点
    const addNodeToTree = (nodes: TreeNode[], parentId: string, newNode: TreeNode): TreeNode[] => {
      return nodes.map(node => {
        if (node.id === parentId) {
          // 找到父节点，添加子节点
          const updatedNode = {
            ...node,
            children: [...(node.children || []), newNode],
            isExpanded: true // 自动展开父节点以显示新子节点
          }
          console.log("在节点", node.name, "下添加子节点:", newNode.name)
          return updatedNode
        } else if (node.children && node.children.length > 0) {
          // 递归查找子节点
          return {
            ...node,
            children: addNodeToTree(node.children, parentId, newNode)
          }
        }
        return node
      })
    }

    // 更新树数据
    setTreeData(prevTreeData => {
      const updatedTree = addNodeToTree(prevTreeData, contextMenu.node!.id, newNode)
      console.log("树数据已更新，新节点已添加")
      return updatedTree
    })

    // 选中新节点并设置数据
    setSelectedNode(newNode)
    setMaterialClassData(newMaterialClass)
    setDetailData(newMaterialClass.materialClassDList)

    // 显示成功消息
    showToast("新增子节点", `在 ${contextMenu.node.name} 下新增子节点`, "success")

    closeContextMenu()
  }

  // 新增根节点
  const addRootNode = () => {
    console.log("执行新增根节点")
    const newNode: TreeNode = {
      id: `new-${Date.now()}`, // 使用new-前缀标识新节点
      parentId: null,
      name: "新根节点",
      description: "新根节点描述",
      children: [],
      isExpanded: false
    }

    // 初始化新的MaterialClass对象
    const newMaterialClass = createInitialMaterialClass(newNode.id, null, 'root')

    // 直接添加到根级别
    setTreeData(prevTreeData => {
      const updatedTree = [...prevTreeData, newNode]
      console.log("根节点已添加，当前根节点数量:", updatedTree.length)
      return updatedTree
    })

    // 选中新节点并设置数据
    setSelectedNode(newNode)
    setMaterialClassData(newMaterialClass)
    setDetailData(newMaterialClass.materialClassDList)

    showToast("新增根节点", "在根级别新增节点", "success")

    closeContextMenu()
  }

  // 编辑节点
  const editNode = () => {
    console.log("editNode函数被调用")
    console.log("要编辑的节点:", contextMenu.node)
    
    if (!contextMenu.node) {
      console.log("contextMenu.node为空，函数返回")
      return
    }
    
    // 选中要编辑的节点
    setSelectedNode(contextMenu.node)
    
    // 加载该节点的数据
    loadMaterialClassData(contextMenu.node.id)
    
    showToast("编辑节点", `正在编辑节点: ${contextMenu.node.name}`, "info")
    
    closeContextMenu()
  }

  // 删除节点
  const deleteNode = async () => {
    console.log("deleteNode函数被调用")
    console.log("要删除的节点:", contextMenu.node)
    
    if (!contextMenu.node) {
      console.log("contextMenu.node为空，函数返回")
      return
    }

    // 如果是新创建的节点（以'new-'开头），直接从树中删除
    if (contextMenu.node.id.startsWith('new-')) {
      console.log("删除新创建的节点，直接从树中移除")
      removeNodeFromTree(contextMenu.node.id)
      showToast("删除节点", `已删除新节点: ${contextMenu.node.name}`, "success")
      closeContextMenu()
      return
    }

    // 调用后端delete接口
    setIsLoading(true)
    try {
      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) {
        throw new Error('未登录，请先登录')
      }

      console.log("调用删除API，节点ID:", contextMenu.node.id)

      const requestData: MaterialClassDeleteRequest = {
        action: 'delete',
        module: 'material-class',
        data: {
          materialClassId: contextMenu.node.id
        }
      }

      const response = await fetch('/api/v1/material-class/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result: UnifiedResponse<{deletedId: string, deletedDetailsCount: number}> = await response.json()
      console.log('删除API响应:', result)
      
      if (result.success && result.data) {
        // 删除成功，从树中移除节点
        removeNodeFromTree(contextMenu.node.id)
        showToast("删除成功", `已删除节点: ${contextMenu.node.name}`, "success")
      } else {
        throw new Error(result.message || '删除失败')
      }
      
    } catch (error) {
      console.error('删除节点失败:', error)
      
      if (error instanceof Error && error.message === '未登录，请先登录') {
        showToast("认证失败", "请先登录系统", "error")
      } else {
        showToast("删除失败", error instanceof Error ? error.message : "删除节点时发生错误", "error")
      }
    } finally {
      setIsLoading(false)
      closeContextMenu()
    }
  }

  // 从树数据中删除节点的辅助函数
  const removeNodeFromTree = (nodeId: string) => {
    const removeNodeFromTreeRecursive = (nodes: TreeNode[], nodeId: string): TreeNode[] => {
      return nodes.map(node => {
        if (node.id === nodeId) {
          // 找到要删除的节点，返回null（将被过滤掉）
          console.log("删除节点:", node.name)
          return null
        } else if (node.children && node.children.length > 0) {
          // 递归处理子节点
          const updatedChildren = removeNodeFromTreeRecursive(node.children, nodeId)
          return {
            ...node,
            children: updatedChildren
          }
        }
        return node
      }).filter(node => node !== null) as TreeNode[]
    }

    // 更新树数据
    setTreeData(prevTreeData => {
      console.log("删除前的树数据节点数量:", prevTreeData.length)
      const updatedTree = removeNodeFromTreeRecursive(prevTreeData, nodeId)
      console.log("删除后的树数据节点数量:", updatedTree.length)
      console.log("删除后的树数据:", updatedTree)
      return updatedTree
    })

    // 如果删除的是当前选中的节点，清除选中状态
    if (selectedNode && selectedNode.id === nodeId) {
      setSelectedNode(null)
      // 清空表头和明细数据
      setMaterialClassData({
        materialClassId: "",
        materialClassPId: "",
        classCode: "",
        classDesc: "",
        remark: "",
        creator: "",
        createDate: "",
        modifierLast: "",
        modifyDateLast: "",
        approveStatus: "N",
        approver: "",
        approveDate: "",
        materialClassDList: [],
        materialClassPCode: "",
        materialClassPDesc: ""
      })
      setDetailData([])
    }
  }

  // 渲染树节点
  const renderTreeNode = (node: TreeNode, level: number = 0) => {
    const hasChildren = node.children && node.children.length > 0
    const isSelected = selectedNode?.id === node.id

    return (
      <Box key={node.id}>
        <Flex
          align="center"
          px={2}
          py={1}
          cursor="pointer"
          bg={isSelected ? "blue.50" : "transparent"}
          _hover={{ bg: isSelected ? "blue.100" : "gray.50" }}
          onClick={() => selectNode(node)}
          onContextMenu={(e) => {
            e.stopPropagation()
            handleContextMenu(e, node)
          }}
          pl={level * 20 + 2}
        >
          {hasChildren ? (
            <Button
              size="xs"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation()
                setTreeData(prev => toggleNode(node.id, prev))
              }}
            >
              {node.isExpanded ? <FiChevronDown /> : <FiChevronRight />}
            </Button>
          ) : (
            <Box w={6} />
          )}
          <Icon 
            as={FiFolder} 
            mr={2} 
            color="blue.500"
          />
          <Text fontSize="sm" flex={1}>
            [{node.name}] {node.description}
          </Text>
        </Flex>
        {hasChildren && node.isExpanded && (
          <Box>
            {node.children!.map(child => renderTreeNode(child, level + 1))}
          </Box>
        )}
      </Box>
    )
  }

  // 初始化数据
  useEffect(() => {
    loadTreeData()
    loadFeatureList() // 同时加载Feature数据
  }, [])

  // 监听detailData变化
  useEffect(() => {
    
  }, [detailData])

  // 点击其他地方关闭右键菜单和Feature对话框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // 如果正在拖拽，不关闭对话框
      if (featureDialog.isDragging) {
        return
      }
      
      // 检查是否点击了Feature对话框内部
      const featureDialogElement = document.querySelector('[data-feature-dialog]')
      if (featureDialogElement && featureDialogElement.contains(event.target as Node)) {
        return
      }
      
      closeContextMenu()
      closeFeatureDialog()
    }

    document.addEventListener('click', handleClickOutside)
    return () => {
      document.removeEventListener('click', handleClickOutside)
    }
  }, [featureDialog.isDragging])

  // 监控featureDialog状态变化
  useEffect(() => {
    
  }, [featureDialog])

  // 监控Feature数据状态
  useEffect(() => {
    console.log('Feature data state:', { 
      isLoadingFeatures, 
      featureListLength: featureList.length,
      featureList: featureList.slice(0, 3) // 只显示前3个
    })
  }, [isLoadingFeatures, featureList])

  // 添加拖拽事件监听器
  useEffect(() => {
    if (featureDialog.isDragging) {
      const handleMouseMove = (e: MouseEvent) => dragDialog(e)
      const handleMouseUp = () => endDragDialog()
      
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [featureDialog.isDragging])

  // 添加表格对话框拖拽事件监听器
  useEffect(() => {
    if (tableDialog.isDragging) {
      const handleMouseMove = (e: MouseEvent) => dragTableDialog(e)
      const handleMouseUp = () => endDragTableDialog()
      
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [tableDialog.isDragging])

  const handleCellEditingStarted = useCallback((params: any) =>{
    if (params.column && params.column.getColId() === 'featureCode')
    {
      console.log("属性代码编辑开始:", params)
      
      // 配置表格对话框的API、过滤条件、显示字段等
      const tableDialogConfig = {
        // API 配置 - 调用feature的list接口
        apiConfig: {
          endpoint: '/api/v1/feature/unified',
          method: 'POST' as const,
          headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
            'Content-Type': 'application/json'
          },
          params: {
            action: 'list',
            module: 'feature',
            data: {}
          },
          transform: (response: any) => {
            // 转换API响应数据，提取feature列表
            console.log('Feature API 响应:', response)
            if (response && response.data && Array.isArray(response.data)) {
              return response.data.map((item: any) => ({
                featureId: item.featureId,
                featureCode: item.featureCode,
                featureDesc: item.featureDesc
             
              }))
            }
            return []
          },
          onError: (error: any) => {
            console.error('获取特征数据失败:', error)
            showToast("获取失败", "无法加载特征数据", "error")
          }
        },
        
        // 过滤配置
        filterConfig: {
          searchFields: ['featureCode', 'featureDesc'],
          preFilters: {
            // 可以根据需要添加预过滤条件，比如只显示激活的特征
            // status: 'active'
          },
          customFilter: (row: TableDataRow, searchText: string) => {
            // 自定义过滤逻辑
            const searchLower = searchText.toLowerCase()
            return row.featureCode?.toLowerCase().includes(searchLower) ||
                   row.featureDesc?.toLowerCase().includes(searchLower)
          }
        },
        
        // 显示配置
        displayConfig: {
          primaryKey: 'featureId',
          displayFields: ['featureCode', 'featureDesc']
        },
        
        // 返回值配置
        returnConfig: {
          returnFields: ['featureCode', 'featureId', 'featureDesc'],
          returnTransformer: (row: TableDataRow) => ({
            featureCode: row.featureCode,
            featureId: row.featureId,
            featureDesc: row.featureDesc
          })
        },
        
        // 列定义
        columns: [
          { key: 'featureCode', title: '特征代码', width: 120 },
          { key: 'featureDesc', title: '特征描述', width: 200 }
        ] as TableColumn[]
      }
      
      console.log("准备打开表格对话框...")
      console.log("表格对话框配置:", tableDialogConfig)
      
      // 打开表格对话框，传递配置信息
      openTableDialogWithConfig(null, params, tableDialogConfig)
    }
  },[])

  const handleCellEditingStopped = useCallback((params: any) =>{
    if (params.column && params.column.getColId() === 'featureCode')
      {
        console.log("属性代码编辑结束:", params)
      }
  },[])

  return (
    <Box h="100vh" bg="gray.50" position="relative">
      {/* 树控件容器 */}
      <Box w="300px" bg="white" borderRight="1px" borderColor="gray.200" h="100%">
        {/* 树内容 */}
        <Box 
          flex={1} 
          overflowY="auto" 
          p={2}
          onContextMenu={(e) => {
            console.log("空白区域右键点击")
            handleContextMenu(e)
          }}
          minH="200px"
          bg="gray.50"
        >
          {isLoading ? (
            <Flex justify="center" align="center" h="100px">
              <VStack gap={2}>
                <Box
                  width="6"
                  height="6"
                  borderRadius="full"
                  bg="blue.500"
                  animation="pulse 1.5s infinite"
                />
                <Text fontSize="sm" color="gray.600">加载物料类别数据中...</Text>
              </VStack>
            </Flex>
          ) : (
            <>
              <VStack align="stretch" gap={0}>
                {treeData.map(node => renderTreeNode(node))}
              </VStack>
              {/* 确保有足够的空白区域 */}
              <Box h="50px" />
            </>
          )}
        </Box>
      </Box>

      {/* Feature选择对话框 */}
      {featureDialog.visible && (
        <Box
          position="fixed"
          left={featureDialog.x}
          top={featureDialog.y}
          bg="white"
          border="1px"
          borderColor="gray.200"
          borderRadius="md"
          boxShadow="lg"
          zIndex={9999}
          minW="400px"
          maxH="300px"
          overflow="hidden"
          data-feature-dialog
          style={{ pointerEvents: 'auto' }}
        >
          <Flex 
            bg="gray.50" 
            p={1} 
            borderBottom="1px" 
            borderColor="gray.200"
            justify="space-between"
            align="center"
            cursor="move"
            onMouseDown={startDragDialog}
            userSelect="none"
          >
            <Text fontSize="sm" fontWeight="medium">选择Feature</Text>
            <Button
              size="xs"
              variant="ghost"
              onClick={closeFeatureDialog}
              onMouseDown={(e) => e.stopPropagation()}
            >
              <FiX />
            </Button>
          </Flex>
          
          <Box maxH="250px" overflowY="auto">
            <VStack align="stretch" gap={0}>
              {isLoadingFeatures ? (
                <Flex justify="center" align="center" h="50px">
                  <VStack gap={2}>
                    <Box
                      width="4"
                      height="4"
                      borderRadius="full"
                      bg="blue.500"
                      animation="pulse 1.5s infinite"
                    />
                    <Text fontSize="sm" color="gray.600">加载Feature数据中...</Text>
                  </VStack>
                </Flex>
              ) : featureList.length === 0 ? (
                <Flex justify="center" align="center" h="50px">
                  <Text fontSize="sm" color="gray.500">暂无Feature数据</Text>
                </Flex>
              ) : (
                featureList.map((feature) => (
                  <Flex
                    key={feature.featureId}
                    p={2}
                    cursor="pointer"
                    _hover={{ bg: "blue.50" }}
                    onClick={() => selectFeature(feature)}
                    borderBottom="1px"
                    borderColor="gray.100"
                  >
                    <Text fontSize="sm" flex="1" fontWeight="medium">
                      {feature.featureCode}
                    </Text>
                    <Text fontSize="sm" flex="2" color="gray.600">
                      {feature.featureDesc}
                    </Text>
                  </Flex>
                ))
              )}
            </VStack>
          </Box>
        </Box>
      )}

      {/* 通用表格选择对话框 */}
      <TableSelectDialog
        visible={tableDialog.visible}
        x={tableDialog.x}
        y={tableDialog.y}
        data={tableDialogConfig.data}
        columns={tableDialogConfig.columns}
        loading={tableDialogConfig.loading}
        apiConfig={tableDialogConfig.apiConfig}
        filterConfig={tableDialogConfig.filterConfig}
        displayConfig={tableDialogConfig.displayConfig}
        returnConfig={tableDialogConfig.returnConfig}
        title="选择属性特征"
        searchable={true}
        searchPlaceholder="搜索代码、名称或描述..."
        multiSelect={false}
        maxHeight="400px"
        minWidth="600px"
        onClose={closeTableDialog}
        onSelect={handleTableDialogSelect}
        onDoubleClick={handleTableDialogDoubleClick}
        isDragging={tableDialog.isDragging}
        dragOffset={tableDialog.dragOffset}
        onStartDrag={startDragTableDialog}
      />

      {/* 右键菜单 */}
      {contextMenu.visible && (
        <Box
          position="fixed"
          left={contextMenu.x}
          top={contextMenu.y}
          bg="white"
          border="1px"
          borderColor="gray.200"
          borderRadius="md"
          boxShadow="lg"
          zIndex={1000}
          minW="150px"
          onClick={() => console.log("菜单被点击")}
        >
          <VStack align="stretch" gap={0}>
            {contextMenu.node ? (
              // 在节点上右键时的菜单
              <>
                              <Button
                  variant="ghost"
                  size="sm"
                  justifyContent="flex-start"
                  onClick={addNode}
                >
                  <Flex align="center">
                    <Icon as={FiPlus} mr={2} />
                    新增同级节点
                  </Flex>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  justifyContent="flex-start"
                  onClick={() => {
                    console.log("新增子节点按钮被点击")
                    addSubNode()
                  }}
                >
                  <Flex align="center">
                    <Icon as={FiPlus} mr={2} />
                    新增子节点
                  </Flex>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  justifyContent="flex-start"
                  onClick={editNode}
                >
                  <Flex align="center">
                    <Icon as={FiEdit} mr={2} />
                    编辑节点
                  </Flex>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  justifyContent="flex-start"
                  onClick={deleteNode}
                  colorScheme="red"
                >
                  <Flex align="center">
                    <Icon as={FiTrash2} mr={2} />
                    删除节点
                  </Flex>
                </Button>
              </>
            ) : (
              // 在空白区域右键时的菜单
              <Button
                variant="ghost"
                size="sm"
                justifyContent="flex-start"
                onClick={addRootNode}
              >
                <Flex align="center">
                  <Icon as={FiPlus} mr={2} />
                  新增根节点
                </Flex>
              </Button>
            )}
          </VStack>
        </Box>
      )}

            {/* 右侧编辑区域 */}
        <Box
          position="absolute"
          left="300px"
          top={0}
          right={0}
          bottom={0}
          bg="white"
          display="flex"
          flexDirection="column"
          overflow="auto"
        >
          {/* 表头数据区域 */}
          <Box p={1} borderBottom="1px" borderColor="gray.200" flexShrink={0}>
            <Grid templateColumns="repeat(2, 1fr)" gap={1}>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">类别编号</Text>
                  <Input
                    value={materialClassData.classCode}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleHeaderChange('classCode', e.target.value)}
                    placeholder="请输入类别编号"
                    size="sm"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">类别描述</Text>
                  <Input
                    value={materialClassData.classDesc}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleHeaderChange('classDesc', e.target.value)}
                    placeholder="请输入类别描述"
                    size="sm"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">上级类别</Text>
                  <input type="hidden" value={materialClassData.materialClassPId} />
                  <SelectInput
                    value={`${materialClassData.materialClassPCode || ''}${materialClassData.materialClassPCode && materialClassData.materialClassPDesc ? ' | ' : ''}${materialClassData.materialClassPDesc || ''}`}
                    onChange={(value) => {
                      console.log('SelectInput onChange:', value)
                      // 处理选择逻辑，设置上级类别ID、编码和描述
                      if (value && typeof value === 'string') {
                        try {
                          const parsedValue = JSON.parse(value)
                          if (parsedValue.materialClassId) {
                            // 设置上级类别ID
                            handleHeaderChange('materialClassPId', parsedValue.materialClassId)
                            // 设置上级类别编码
                            handleHeaderChange('materialClassPCode', parsedValue.classCode || '')
                            // 设置上级类别描述
                            handleHeaderChange('materialClassPDesc', parsedValue.classDesc || '')
                            console.log('已设置上级类别:', {
                              id: parsedValue.materialClassId,
                              code: parsedValue.classCode,
                              desc: parsedValue.classDesc
                            })
                          }
                        } catch (error) {
                          console.log('解析返回值失败，直接使用原始值:', value)
                          // 如果不是JSON格式，直接作为ID使用
                          handleHeaderChange('materialClassPId', value)
                          // 清空编码和描述
                          handleHeaderChange('materialClassPCode', '')
                          handleHeaderChange('materialClassPDesc', '')
                        }
                      } else {
                        console.log('无效的返回值:', value)
                        // 清空所有相关字段
                        handleHeaderChange('materialClassPId', '')
                        handleHeaderChange('materialClassPCode', '')
                        handleHeaderChange('materialClassPDesc', '')
                      }
                    }}
                    placeholder="请选择上级类别"
                    buttonText="选择"
                    modalTitle="选择上级类别"
                    searchPlaceholder="请输入类别编码或描述"
                    columns={[
                      { 
                        header: "类别编码", 
                        field: "classCode",
                        width: 150,
                        minWidth: 120,
                        flex: 1,
                        align: "left"
                      },
                      { 
                        header: "类别描述", 
                        field: "classDesc",
                        width: 200,
                        minWidth: 150,
                        flex: 2,
                        align: "left"
                      }
                    ]}
                    valueField="materialClassId"
                    displayField="classCode"
                    returnFormat="object"
                    apiUrl="/api/v1/material-class/unified"
                    apiMethod="POST"
                    apiParams={{
                      action: "list",
                      module: "material-class",
                      page: 1,
                      limit: 100
                    }}
                    data={treeData.map(item => ({
                      materialClassId: item.id,
                      classCode: item.name,
                      classDesc: item.description,
                      remark: item.description
                    }))}
                    width="calc(100% - 80px)"
                  />
                </Flex>
              </GridItem>        
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">备注</Text>
                <Input
                    value={materialClassData.remark}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleHeaderChange('remark', e.target.value)}
                    placeholder="请输入备注信息"
                    size="sm"
                    flex="1"
                  />
                </Flex>
              </GridItem>
            </Grid>
          </Box>

          {/* 明细数据区域 */}
          <Box flex={1} display="flex" flexDirection="column" p={1} overflow="auto">
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
              </Flex>
              
              <Flex gap={1.5} align="center">
                {selectedRows.length > 0 && (
                  <Flex align="center" gap={1} px={1.5} py={0.5} bg="blue.100" borderRadius="sm">
                    <Text fontSize="xs" color="blue.700" fontWeight="medium">
                      已选 {selectedRows.length}
                    </Text>
                  </Flex>
                )}
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
              flex="1"
              minH="0"
              position="relative"
              overflow="hidden"
              border="1px"
              borderColor="gray.200"
              borderRadius="sm"
            >
              {isLoading && (
                <Box
                  position="absolute"
                  top="50%"
                  left="50%"
                  transform="translate(-50%, -50%)"
                  zIndex={10}
                  bg="white"
                  p={1}
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
                singleClickEdit={false}
                stopEditingWhenCellsLoseFocus={true}
                onCellEditingStarted={handleCellEditingStarted}
                onCellEditingStopped={handleCellEditingStopped}
                // 默认列定义
                defaultColDef={{
                  sortable: true,
                  filter: true,
                  resizable: true
                }}
              />
            </Box>
                         {/* 保存按钮 */}
            <Flex justify="center" mt={3} flexShrink={0}>
              <Button
                colorScheme="blue"
                variant="outline"
                size="sm"
                onClick={saveData}
                title="保存"
                minW="36px"
                height="26px"
                fontSize="11px"
                px={1.5}
                borderRadius="md"
                disabled={!selectedNode || isLoading}
                opacity={!selectedNode || isLoading ? 0.5 : 1}
              >
                {isLoading ? (
                  <Box
                    width="11px"
                    height="11px"
                    borderRadius="full"
                    bg="blue.500"
                    animation="pulse 1.5s infinite"
                  />
                ) : (
                  <FiSave size={11} />
                )}
              </Button>
            </Flex>
           
          </Box>
        </Box>
    </Box>
  )
}

export default MaterialClassEdit
