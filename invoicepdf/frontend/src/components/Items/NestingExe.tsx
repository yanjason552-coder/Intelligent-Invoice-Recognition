import React, { useState, useRef } from "react"
import { 
  Box, 
  Flex, 
  Text, 
  Input, 
  Button, 
  IconButton,
  HStack,
  VStack,
  Grid,
  GridItem
} from "@chakra-ui/react"
import {useMemo } from "react"
import { FiChevronUp, FiChevronDown, FiArrowRight, FiSearch } from "react-icons/fi"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { Stage, Layer, Rect, Text as KonvaText } from 'react-konva'

// 注册AG-Grid模块
ModuleRegistry.registerModules([AllCommunityModule])

interface NestingExeProps {
  nestingLayoutId?: string
  nestingLayoutData?: any
}

import useCustomToast from '@/hooks/useCustomToast'

const NestingExe = ({ }: NestingExeProps) => {
  // 查询区域显示/隐藏状态
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  
  // 面板显示状态
  const [currentPanel, setCurrentPanel] = useState<'so-panel' | 'index-panel' | 'nesting-panel'>('so-panel')
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()

  const [soDynamicColumns, setSoDynamicColumns] = useState<ColDef[]>([])
  const [nestingDynamicColumns, setNestingDynamicColumns] = useState<ColDef[]>([])

  // 表格数据状态
  const [soTableData, setSoTableData] = useState<any[]>([])
  const [nestingTableData, setNestingTableData] = useState<any[]>([])
  const [gridApi, setGridApi] = useState<any>(null)
  
  // 选中的数据状态
  const [selectedSoData, setSelectedSoData] = useState<any[]>([])
  const [selectedNestingData, setSelectedNestingData] = useState<any[]>([])
  
  // Konva Canvas相关状态
  const [rectangles, setRectangles] = useState<Array<{
    id: string
    x: number
    y: number
    width: number
    height: number
    fill: string
    stroke?: string
    strokeWidth?: number
    docNo?: string
    quantity?: number
  }>>([])
  const stageRef = useRef<any>(null)
  
  // 画布缩放和平移状态
  const [stageScale, setStageScale] = useState(1)
  const [stagePosition, setStagePosition] = useState({ x: 0, y: 0 })
  const [containerSize, setContainerSize] = useState({ width: 1200, height: 600 })

  const [queryConditions, setQueryConditions] = useState({
    customerFullName: '',
    docNo: '',
    docDate:'',    
    deliveryDate: ''    
  })

  // 切换查询面板显示状态
  const toggleQueryPanel = () => {
    setIsQueryPanelOpen(!isQueryPanelOpen)
  }

  // 处理查询条件变化
  const handleQueryConditionChange = (field: string, value: string) => {
    setQueryConditions(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // 数据转换函数 - 将后端返回的数据转换为前端格式，子对象数据横置转换
  const transformData = (data: any[]): any[] => {
    const result: any[] = []
    
    // 收集所有唯一的 featureDesc 作为动态列
    const allFeatureDescs = new Set<string>()
    data.forEach(item => {
      if (item.salesOrderDocDFeatureList && item.salesOrderDocDFeatureList.length > 0) {
        item.salesOrderDocDFeatureList.forEach((feature: any) => {
          if (feature.featureDesc) {
            allFeatureDescs.add(feature.featureDesc)
          }
        })
      }
    })

    // 生成动态列定义
    const dynamicColumns: ColDef[] = Array.from(allFeatureDescs).map(featureDesc => ({
      headerName: featureDesc,
      field: featureDesc,
      width: 120,
      filter: 'text'
    }))
    
    // 更新动态列状态
    setSoDynamicColumns(dynamicColumns)

    // 转换数据
    data.forEach(item => {
      const transformedItem = {
        ...item,
        // 添加动态特征字段
        ...Array.from(allFeatureDescs).reduce((acc, featureDesc) => {
          const feature = item.salesOrderDocDFeatureList?.find((f: any) => f.featureDesc === featureDesc)
          acc[featureDesc] = feature?.featureValue || ''
          return acc
        }, {} as any)
      }
      result.push(transformedItem)
    })

    return result
  }


  // 执行查询
  const handleSoQuery = async () => {
    console.log("执行查询，条件:", queryConditions)
    setIsLoading(true)
    
    try {
      // 构建请求体
      const requestBody: any = {
        action: 'list',
        module: 'sales_order_doc_d',
        page: currentPage,
        limit: 500,
        timestamp: new Date().toISOString()
      }
      
      // 添加查询条件
      const filters: any = {}
      if (queryConditions.customerFullName) filters.customer_full_name = queryConditions.customerFullName
      if (queryConditions.docNo) filters.doc_no = queryConditions.docNo
      if (queryConditions.docDate) filters.doc_code = queryConditions.docDate
      if (queryConditions.deliveryDate) filters.delivery_date = queryConditions.deliveryDate
      
      
      if (Object.keys(filters).length > 0) {
        requestBody.filters = filters
      }
      
      console.log("查询请求体:", requestBody)
      
      const response = await fetch('/api/v1/salesOrderDocD/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          console.log("查询成功:", result.data)
          const transformedData = transformData(result.data || [])
          console.log("转换后的数据:", transformedData)
          setSoTableData(transformedData)
          const totalCount = result.pagination?.total || 0
          const queryType = Object.keys(filters).length > 0 ? '条件查询' : '全部数据'
          const message = `${queryType}成功，找到 ${totalCount} 条记录`
          showSuccessToast(message)
        } else {
          showErrorToast(`查询失败: ${result.message}`)
        }
      } else {
        showErrorToast(`查询失败: ${response.status}`)
      }
    } catch (error) {
      console.error('查询失败:', error)
      showErrorToast(`查询失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 下一步功能
  const handleNextStep = () => {
    console.log("执行下一步")
    if (currentPanel === 'so-panel') {
      console.log("从SO面板选中的数据:", selectedSoData)
      setCurrentPanel('index-panel')
    } else if (currentPanel === 'index-panel') {
      setCurrentPanel('nesting-panel')
      // 套料逻辑
      console.log("开始套料，使用选中的SO数据:", selectedSoData)
      
      // 调用后端套料算法API
      handleNestingAlgorithm()
    }
  }


  // 调用套料算法（直接使用后端算法）
  const handleNestingAlgorithm = async () => {
    console.log("开始套料算法")
    setIsLoading(true)
    
    try {
      console.log("使用后端套料算法")
      // 构建请求体
      const requestBody = {
        action: 'create',
        module: 'nesting_layout',
        data: {
          selectedSoData: selectedSoData,
          nestingParams: {
            materialUtilizationRate: 0.85,
            surplusConsumptionRate: 0.15
          }
        },
        timestamp: new Date().toISOString()
      }
      
      const response = await fetch('/api/v1/nesting-layout/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          console.log("===== 后端套料算法执行成功 =====")
          console.log("完整返回结果:", result)
          console.log("result.data:", result.data)
          console.log("result.data.nesting_result:", result.data?.nesting_result)
          
          showSuccessToast("后端套料算法执行成功")
          
          // 修改：正确解析后端返回的数据结构
          if (result.data && result.data.nesting_result) {
            const nestingResult = result.data.nesting_result
            console.log("套料结果对象:", nestingResult)
            
            // 提取final_table作为套料结果
            if (nestingResult.final_table && Array.isArray(nestingResult.final_table)) {
              console.log("final_table数据:", nestingResult.final_table)
              console.log("final_table记录数:", nestingResult.final_table.length)
              
              // 转换为前端需要的格式
              const convertedData = nestingResult.final_table.map((item: any, index: number) => ({
                seq: index + 1,
                materialCode: item.material_code || '',
                materialDesc: item.material_desc || '',
                warehouseName: item.warehouse_name || '',
                binName: item.bin_name || '',
                lotNo: item.lot_no || '',
                stockQty: item.stock_qty || 0,
                stockQtyLocked: item.stock_qty_locked || 0,
                nestingQty: item.nesting_qty || 0,
                ...item // 保留其他字段
              }))
              
              console.log("转换后的前端数据:", convertedData)
              setNestingTableData(convertedData)
              
              // 更新Konva画布 - 使用visualization数据（包含坐标信息）
              if (nestingResult.visualization && Array.isArray(nestingResult.visualization)) {
                console.log("visualization数据:", nestingResult.visualization)
                updateCanvasWithResults(nestingResult.visualization)
              } else {
                console.log("没有visualization数据")
                setRectangles([])
              }
            } else {
              console.warn("后端返回的final_table不是数组或为空:", nestingResult.final_table)
              setNestingTableData([])
            }
          } else {
            console.warn("后端返回的数据中没有nesting_result字段:", result.data)
            setNestingTableData([])
          }
        } else {
          showErrorToast(`后端套料算法执行失败: ${result.message}`)
        }
      } else {
        const errorText = await response.text()
        console.error("后端返回错误:", errorText)
        showErrorToast(`后端套料算法调用失败: ${response.status}`)
      }
    } catch (error) {
      console.error('套料算法执行失败:', error)
      showErrorToast(`套料算法执行失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 更新画布显示套料结果
  const updateCanvasWithResults = (results: any[]) => {
    console.log("updateCanvasWithResults 接收到的数据:", results)
    
    if (!results || results.length === 0) {
      console.log("没有坐标数据可显示")
      setRectangles([])
      return
    }
    
    // results 是钢卷数组，每个钢卷包含 coordinates 数组
    const newRectangles: any[] = []
    
    // 为每个订单分配不同的颜色
    const colors = [
      'rgba(59, 130, 246, 0.5)',   // 蓝色
      'rgba(16, 185, 129, 0.5)',   // 绿色
      'rgba(251, 146, 60, 0.5)',   // 橙色
      'rgba(236, 72, 153, 0.5)',   // 粉色
      'rgba(139, 92, 246, 0.5)',   // 紫色
      'rgba(245, 158, 11, 0.5)',   // 黄色
      'rgba(20, 184, 166, 0.5)',   // 青色
      'rgba(244, 63, 94, 0.5)',    // 红色
    ]
    
    // 垂直偏移量，用于将多个钢卷排列在不同行
    let currentYOffset = 0
    const steelGap = 100  // 钢卷之间的间距
    
    results.forEach((steelData, steelIndex) => {
      const coordinates = steelData.coordinates || []
      const steelWidth = steelData.steelWidth || 1000
      
      console.log(`钢卷${steelIndex + 1} (${steelData.steelIdentifier}): ${coordinates.length} 个订单坐标, 宽度=${steelWidth}mm`)
      
      // 按 docNo 分组，相同订单使用相同颜色
      const docNoColorMap = new Map<string, string>()
      
      // 记录这个钢卷使用的最大高度（用于下一个钢卷的y偏移）
      let maxHeightInThisSteel = 0
      
      coordinates.forEach((coord: any, coordIndex: number) => {
        const docNo = coord.docNo || `订单${coordIndex + 1}`
        
        // 为每个订单号分配颜色
        if (!docNoColorMap.has(docNo)) {
          const colorIndex = docNoColorMap.size % colors.length
          docNoColorMap.set(docNo, colors[colorIndex])
        }
        
        // 计算实际的Y坐标（原始y坐标 + 当前钢卷的偏移量）
        const actualY = (coord.y || 0) + currentYOffset
        const rectHeight = coord.width || 80
        
        // 更新这个钢卷的最大高度
        maxHeightInThisSteel = Math.max(maxHeightInThisSteel, (coord.y || 0) + rectHeight)
        
        // 每个订单块都单独创建矩形，即使是同一个订单的多个块
        newRectangles.push({
          id: `steel_${steelIndex}_order_${coordIndex}`,
          x: coord.x || 0,
          y: actualY,  // 使用调整后的Y坐标
          width: coord.length || 100,   // 订单的长度作为矩形的宽度
          height: rectHeight,           // 订单的宽度作为矩形的高度
          fill: docNoColorMap.get(docNo),
          stroke: '#000',               // 黑色边框
          strokeWidth: 2,               // 边框宽度
          docNo: docNo,
          quantity: coord.quantity || 1,
          steelIndex: steelIndex,       // 记录属于哪个钢卷
          steelIdentifier: steelData.steelIdentifier
        })
      })
      
      // 为下一个钢卷设置Y偏移量（当前钢卷的最大高度 + 间距）
      currentYOffset += maxHeightInThisSteel + steelGap
      
      console.log(`钢卷${steelIndex + 1}的最大高度: ${maxHeightInThisSteel}mm, 下一个钢卷Y偏移: ${currentYOffset}mm`)
    })
    
    console.log(`共生成 ${newRectangles.length} 个矩形，总高度约 ${currentYOffset}mm`)
    setRectangles(newRectangles)
    
    // 自动调整缩放以适应所有矩形
    if (newRectangles.length > 0) {
      const maxX = Math.max(...newRectangles.map(r => r.x + r.width))
      const maxY = Math.max(...newRectangles.map(r => r.y + r.height))
      
      // 计算合适的缩放比例
      const scaleX = (containerSize.width - 40) / maxX
      const scaleY = (containerSize.height - 40) / maxY
      const initialScale = Math.min(scaleX, scaleY, 1) // 不放大，只缩小
      
      setStageScale(initialScale)
      setStagePosition({ x: 20, y: 20 })
      
      console.log(`画布范围: ${maxX} x ${maxY}, 初始缩放: ${initialScale}`)
    }
  }

  // 前一步功能
  const handlePreviousStep = () => {
    console.log("执行前一步")
    if (currentPanel === 'index-panel') {
      setCurrentPanel('so-panel')
    } else if (currentPanel === 'nesting-panel') {
      setCurrentPanel('index-panel')
    }
  }


 // So面板的AG-Grid列定义
 const soColumnDefs: ColDef[] = useMemo(() => {
  const baseColumns: ColDef[] = [
    {
      headerName: '',
      field: 'select',
      width: 30,
      checkboxSelection: true,
      headerCheckboxSelection: true,
      pinned: 'left',
      filter: false
    },
    {
      headerName: '序号',
      field: 'sequence',
      width: 60,
      pinned: 'left',
      filter: 'text',
      valueGetter: (params) => {
        return String((params.node?.rowIndex || 0) + 1).padStart(4, '0')
      }
    },
    {
      headerName: '客户',
      field: 'customerFullName',
      width: 80,
      pinned: 'left',
      filter: 'text'
    },
    {
      headerName: '订单单号',
      field: 'docNo',
      width: 120,
      pinned: 'left',
      filter: 'text'
    },
    {
      headerName: '行号',
      field: 'sequence',
      width: 60,
      pinned: 'left',
      filter: 'text'
    },
    {
      headerName: '订单日期',
      field: 'docDate',
      width: 110,
      pinned: 'left',
      filter: 'text'
    },
    {
      headerName: '物料编码',
      field: 'materialCode',
      width: 110,
      filter: 'text'
    },
    {
      headerName: '物料描述',
      field: 'materialDescription',
      width: 250,
      filter: 'text'
    },
    {
      headerName: '数量',
      field: 'qty',
      width: 100,
      filter: 'number'
    },
    {
      headerName: '交期',
      field: 'deliveryDate',
      width: 120,
      filter: 'text'
    },
    {
      headerName: '套料数量',
      field: 'nestingedQty',
      width: 120,
      filter: 'number'
    }
  ]
  
  return [...baseColumns, ...soDynamicColumns]
}, [soDynamicColumns])

  // Nesting面板的AG-Grid列定义
 const nestingColumnDefs: ColDef[] = useMemo(() => {
  const baseColumns: ColDef[] = [
    {
      headerName: '',
      field: 'select',
      width: 40,
      checkboxSelection: true,
      headerCheckboxSelection: true,
      filter: false
    },
    { 
      headerName: '行号', 
      field: 'seq', 
      width: 70
    },
    { 
      headerName: '物料编码', 
      field: 'materialCode', 
      width: 120
    },
    { 
      headerName: '物料描述', 
      field: 'materialDesc', 
      width: 150
    },
    { 
      headerName: '仓库', 
      field: 'warehouseName', 
      width: 100
    },
    { 
      headerName: '库位', 
      field: 'binName', 
      width: 100
    },
    { 
      headerName: '批号', 
      field: 'lotNo', 
      width: 120
    },
    { 
      headerName: '库存数量', 
      field: 'stockQty', 
      width: 100
    },
    { 
      headerName: '已套数量', 
      field: 'stockQtyLocked', 
      width: 110
    },
    { 
      headerName: '本次数量', 
      field: 'nestingQty', 
      width: 110
    }
  ]

  return [...baseColumns, ...nestingDynamicColumns]
}, [nestingDynamicColumns])

  // 格式化函数
  const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      return date.toISOString().split('T')[0] // 返回 YYYY-MM-DD 格式
    } catch (error) {
      return dateString
    }
  }

  const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
    if (value === null || value === undefined) return ''
    return Number(value).toFixed(decimals)
  }

  const formatNumberAdvanced = (value: number | null | undefined, decimals: number = 2, showThousandsSeparator: boolean = false): string => {
    if (value === null || value === undefined) return ''
    const num = Number(value)
    if (showThousandsSeparator) {
      return num.toLocaleString('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      })
    }
    return num.toFixed(decimals)
  }

  // AG-Grid 事件处理
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api)
  }

  // 处理行选择变化
  const onSelectionChanged = () => {
    const selectedRows = gridApi?.getSelectedRows()
    console.log('选中的行:', selectedRows)
    
    // 根据当前面板保存选中的数据
    if (currentPanel === 'so-panel') {
      setSelectedSoData(selectedRows || [])
    } else if (currentPanel === 'nesting-panel') {
      setSelectedNestingData(selectedRows || [])
    }
  }

  // Konva Canvas相关函数
  const addRectangle = () => {
    console.log('添加矩形按钮被点击')
    const newRect = {
      id: Date.now().toString(),
      x: 50,
      y: 50,
      width: 100,
      height: 80,
      fill: `hsl(${Math.random() * 360}, 70%, 50%)`
    }
    console.log('新矩形:', newRect)
    console.log('当前矩形数量:', rectangles.length)
    setRectangles([...rectangles, newRect])
    console.log('矩形已添加到状态')
  }

  const clearCanvas = () => {
    setRectangles([])
  }

  const handleStageClick = (e: any) => {
    // 画布点击事件（保留用于可能的其他交互）
  }

  // 处理滚轮缩放
  const handleWheel = (e: any) => {
    e.evt.preventDefault()
    
    const stage = e.target.getStage()
    const oldScale = stage.scaleX()
    const pointer = stage.getPointerPosition()
    
    const scaleBy = 1.1
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy
    
    // 限制缩放范围
    const limitedScale = Math.max(0.1, Math.min(5, newScale))
    
    setStageScale(limitedScale)
    
    // 计算新的位置，使鼠标指针位置保持不变
    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    }
    
    const newPos = {
      x: pointer.x - mousePointTo.x * limitedScale,
      y: pointer.y - mousePointTo.y * limitedScale,
    }
    
    setStagePosition(newPos)
  }

  // 重置视图
  const resetView = () => {
    setStageScale(1)
    setStagePosition({ x: 0, y: 0 })
  }

  // 适应视图
  const fitView = () => {
    if (rectangles.length === 0) return
    
    const maxX = Math.max(...rectangles.map(r => r.x + r.width))
    const maxY = Math.max(...rectangles.map(r => r.y + r.height))
    
    const scaleX = (containerSize.width - 40) / maxX
    const scaleY = (containerSize.height - 40) / maxY
    const scale = Math.min(scaleX, scaleY, 1)
    
    setStageScale(scale)
    setStagePosition({ x: 20, y: 20 })
  }


  // 监听rectangles状态变化
  React.useEffect(() => {
    console.log('rectangles状态更新:', rectangles)
    console.log('矩形数量:', rectangles.length)
  }, [rectangles])

  // 监听容器大小变化
  React.useEffect(() => {
    const updateSize = () => {
      // 获取实际的容器大小
      const container = document.querySelector('#canvas-container')
      if (container) {
        const width = container.clientWidth
        const height = container.clientHeight
        setContainerSize({ width, height })
        console.log('画布容器大小:', width, 'x', height)
      }
    }
    
    // 初始化
    updateSize()
    
    // 监听窗口大小变化
    window.addEventListener('resize', updateSize)
    
    // 延迟更新以确保容器已渲染
    setTimeout(updateSize, 100)
    
    return () => window.removeEventListener('resize', updateSize)
  }, [currentPanel])

  return (
    <Box p={0} h="100%" display="flex" flexDirection="column">
      {/* SO面板 */}
      {currentPanel === 'so-panel' && (
        <Box id="so-panel" p={0} h="100%" display="flex" flexDirection="column">
      {/* 查询区域 */}
      <Box bg="white" borderBottom="1px" borderColor="gray.200" flexShrink={0}>
        {/* 查询条件区域 */}
        {isQueryPanelOpen && (
          <Box p={1}>
            <Flex align="top" justify="space-between" gap={2}>
              <Grid templateColumns="repeat(3, 1fr)" gap={1}>
                <GridItem>
                  <Flex align="center" gap={2}>
                    <Text fontSize="sm" fontWeight="medium" minW="80px">客户全称</Text>
                    <Input
                      size="sm"
                      placeholder="请输入客户名称"
                      value={queryConditions.customerFullName}
                      onChange={(e) => handleQueryConditionChange('customerFullName', e.target.value)}
                      flex="1"
                    />
                  </Flex>
                </GridItem>
                
                <GridItem>
                  <Flex align="center" gap={2}>
                    <Text fontSize="sm" fontWeight="medium" minW="80px">订单单号</Text>
                    <Input
                      size="sm"
                      placeholder="请输入订单单号"
                      value={queryConditions.docNo}
                      onChange={(e) => handleQueryConditionChange('docNo', e.target.value)}
                      flex="1"
                    />
                  </Flex>
                </GridItem>
                
                <GridItem>
                  <Flex align="center" gap={2}>
                    <Text fontSize="sm" fontWeight="medium" minW="80px">交货日期</Text>
                    <Input
                      size="sm"
                      type="date"
                      placeholder="请选择交期"
                      value={queryConditions.deliveryDate}
                      onChange={(e) => handleQueryConditionChange('deliveryDate', e.target.value)}
                      flex="1"
                    />
                  </Flex>
                </GridItem>
              </Grid>
              <Button
                colorScheme="blue"
                variant="outline"
                size="sm"
                onClick={handleSoQuery}
                title="查询"
                minW="44px"
                height="32px"
                fontSize="13px"
                px={2}
                borderRadius="md"
              >
                <FiSearch />
            </Button>
            </Flex>
            
          </Box>
        )}
        
        {/* 查询区域折叠按钮 */}
        <Flex 
          justify="center" 
          p={0} 
          borderTop="0px" 
          borderColor="gray"
          bg="gray.50"
        >
          
          <IconButton
            aria-label="切换"
            size="xs"
            variant="ghost"
            colorScheme="blue"
            onClick={toggleQueryPanel}
            ml={2}
          >
            {isQueryPanelOpen ? <FiChevronUp /> : <FiChevronDown />}
          </IconButton>
        </Flex>
      </Box>

      {/* 明细数据表格区域 */}
      <Box flex="0.95" minH="0" display="flex" flexDirection="column">
        <Box
          className="ag-theme-alpine"
          flex="1"
          width="100%"
          border="1px"
          borderColor="gray.200"
        >
          <AgGridReact
          columnDefs={soColumnDefs}
          rowData={soTableData}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          rowSelection={{ mode: 'multiRow' }}
          pagination={true}
          paginationPageSize={pageSize}
          suppressRowClickSelection={true}
          animateRows={true}
          // 默认列定义
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true
          }}
        />
        </Box>
      </Box>

      {/* 尾部操作区域 */}
      <Flex 
        justify="space-between"
        align="center"
        bg="white"
        p={1}
        borderColor="gray"
        flexShrink={0}
      >
        <Text fontSize="sm" color="gray.600">
          已选择 {selectedSoData.length} 条记录
        </Text>
        <Button
          colorScheme="blue"
          variant="outline"
          size="sm"
          onClick={handleNextStep}
          title="下一步"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={2}
          borderRadius="md"
        >
          下一步
          <FiArrowRight />
        </Button>
      </Flex>
        </Box>
      )}

      {/* Index面板 */}
      {currentPanel === 'index-panel' && (
        <Box id="index-panel" p={0} h="100%" display="flex" flexDirection="column">
          {/* 内容区域 */}
          <Box flex="0.95" p={1} display="flex" alignItems="center" justifyContent="center">
            
            <Flex align="center" gap={4} maxW="400px" w="100%">
              <Flex align="center" gap={2} flex="1">
                <Text fontSize="sm" fontWeight="medium" whiteSpace="nowrap">材料利用率</Text>
                <Input
                  size="md"
                  placeholder="请输入内容"
                  borderColor="gray.300"
                  value={0.0}
                  flex="1"
                  type="number"
                  max={1}
                />
              </Flex>
              
              <Flex align="center" gap={2} flex="1">
                <Text fontSize="sm" fontWeight="medium" whiteSpace="nowrap">余料消耗率</Text>
                <Input
                  size="md"
                  placeholder="请输入内容"
                  borderColor="gray.300"
                  flex="1"
                  type="number"
                />
              </Flex>
            </Flex>
                
              
            
          </Box>

          {/* 按钮区域 */}
          <Flex 
            justify="space-between"
            align="center"
            p={1}
            bg="white"
            borderTop="1px"
            borderColor="gray.200"
            flexShrink={0}
          >
            <Button
              bg="blue.500"
              color="white"
              size="md"
              onClick={handlePreviousStep}
              _hover={{ bg: "blue.600" }}
              _active={{ bg: "blue.700" }}
            >
              前一步
            </Button>
            
            <Button
              bg="blue.500"
              color="white"
              size="sm"
              onClick={handleNextStep}
              title="下一步"
              minW="44px"
              height="32px"
              fontSize="13px"
              px={2}
              borderRadius="md"
              _hover={{ bg: "blue.600" }}
              _active={{ bg: "blue.700" }}
            >
              下一步
              <FiArrowRight />
            </Button>
          </Flex>
        </Box>
      )}

      {/* Nesting面板 */}
      {currentPanel === 'nesting-panel' && (
        <Box id="nesting-panel" p={0} h="100%" display="flex" flexDirection="column">
          {/* 内容区域 */}
          <Box flex="0.95" p={1} display="flex" flexDirection="column">
            {/* 上半部分：AG-Grid表格 */}
            <Box flex="0.3" minH="0" mb={2}>
              <Box
                className="ag-theme-alpine"
                width="100%"
                height="100%"
                overflow="hidden"
                border="1px"
                borderColor="gray.200"
              >
                <AgGridReact
                  columnDefs={nestingColumnDefs}
                  rowData={nestingTableData}
                  onGridReady={onGridReady}
                  onSelectionChanged={onSelectionChanged}
                  pagination={true}
                  paginationPageSize={20}
                  rowSelection={{ mode: 'multiRow' }}
                  suppressRowClickSelection={true}
                  defaultColDef={{
                    filter: true,
                    sortable: true,
                    resizable: true,
                    filterParams: {
                      buttons: ['apply', 'reset'],
                      closeOnApply: true
                    }
                  }}
                  enableRangeSelection={true}
                  suppressMenuHide={true}
                />
              </Box>
            </Box>

            {/* 下半部分：画板 */}
            <Box flex="0.7" minH="0" border="1px" borderColor="gray.200" bg="white" p={2}>
              <VStack gap={2} align="stretch" h="100%">
                {/* 工具栏 */}
                <HStack gap={2} justify="space-between" flexShrink={0}>
                  <HStack gap={2}>
                    <Button
                      size="sm"
                      colorScheme="blue"
                      onClick={fitView}
                    >
                      适应窗口
                    </Button>
                    <Button
                      size="sm"
                      colorScheme="gray"
                      onClick={resetView}
                    >
                      重置视图
                    </Button>
                    <Button
                      size="sm"
                      colorScheme="red"
                      onClick={clearCanvas}
                    >
                      清空画布
                    </Button>
                  </HStack>
                  <HStack gap={2}>
                    <Text fontSize="sm" color="gray.600">
                      缩放: {(stageScale * 100).toFixed(0)}%
                    </Text>
                    <Text fontSize="sm" color="gray.600">
                      |
                    </Text>
                    <Text fontSize="sm" color="gray.600">
                      滚轮缩放 | 拖拽平移
                    </Text>
                  </HStack>
                </HStack>
                
                {/* Konva Stage */}
                <Box 
                  id="canvas-container"
                  flex="1" 
                  border="1px solid #666" 
                  borderRadius="md" 
                  overflow="hidden"
                  bg="gray.50"
                >
                  <Stage
                    ref={stageRef}
                    width={containerSize.width}
                    height={containerSize.height}
                    scaleX={stageScale}
                    scaleY={stageScale}
                    x={stagePosition.x}
                    y={stagePosition.y}
                    draggable
                    onClick={handleStageClick}
                    onWheel={handleWheel}
                  >
                    <Layer>
                      {rectangles.map((rect) => (
                        <React.Fragment key={rect.id}>
                          <Rect
                            id={rect.id}
                            x={rect.x}
                            y={rect.y}
                            width={rect.width}
                            height={rect.height}
                            fill={rect.fill}
                            stroke={rect.stroke || "#333"}
                            strokeWidth={rect.strokeWidth || 2}
                            listening={false}
                          />
                          {/* 在矩形上显示订单信息 */}
                          {rect.docNo && rect.width > 50 && rect.height > 20 && (
                            <KonvaText
                              x={rect.x + 5}
                              y={rect.y + 5}
                              text={`${rect.docNo}\n数量:${rect.quantity || 1}`}
                              fontSize={28}
                              fill="#000"
                              fontStyle="bold"
                              listening={false}
                            />
                          )}
                        </React.Fragment>
                      ))}
                    </Layer>
                  </Stage>
                </Box>
              </VStack>
            </Box>
          </Box>

          {/* 按钮区域 */}
          <Flex 
            justify="flex-end"
            align="center"
            p={1}
            bg="white"
            borderTop="1px"
            borderColor="gray.200"
            flexShrink={0}
          >
            <Button
              bg="blue.500"
              color="white"
              size="sm"
              onClick={handlePreviousStep}
              _hover={{ bg: "blue.600" }}
              _active={{ bg: "blue.700" }}
            >
              前一步
            </Button>
          </Flex>
        </Box>
      )}
    </Box>
  )
}

export default NestingExe
