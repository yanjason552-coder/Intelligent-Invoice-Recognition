import React, { useState, useMemo, useEffect } from "react"
import { 
  Box, 
  Text, 
  Button, 
  Input,
  HStack,
  Grid,
  GridItem,
  Flex
} from "@chakra-ui/react"
import { FiTrash2, FiSave, FiSearch, FiEdit, FiSend } from "react-icons/fi"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { Stage, Layer, Rect, Transformer } from 'react-konva'
import useCustomToast from '../../hooks/useCustomToast'

// 注册AG-Grid模块
ModuleRegistry.registerModules([AllCommunityModule])

// 定义嵌套布局数据类型
interface NestingLayoutData {
  nestingLayoutId?: string
  plantId?: string
  nestingEmployeeId?: string
  nestingDate?: string
  nestingDesc?: string
  rateOfFinished?: number
  rateOfSurplus?: number
  nestingLayoutDList?: Array<{
    nestingLayoutDId?: string
    nestingLayoutId?: string
    warehouseId?: string
    binId?: string
    materialId?: string
    materialCode?: string
    materialDescription?: string
    materialLotId?: string
    lotNo?: string
    lotDesc?: string
    sn?: string
    startPositionX?: number
    startPositionY?: number
    endPositionX?: number
    endPositionY?: number
    nestingedQty?: number
    unitId?: string
    nestingedSecondQty?: number
    unitIdSecond?: string
    nestingedSoQty?: number
    unitIdSo?: string
    stockQty?: number
    availableStockQty?: number
    remainingStockQty?: number
    nestingLayoutSdList?: any[]
  }>
  [key: string]: any
}

interface NestingEditProps {
  nestingLayoutId?: string
  initialNestingLayoutData?: any
}

const NestingEdit = ({ nestingLayoutId, initialNestingLayoutData }: NestingEditProps) => {
  // 状态管理
  const [isLoading, setIsLoading] = useState(false)
  const [gridApi, setGridApi] = useState<any>(null)
  const [tableData, setTableData] = useState<any[]>([])
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [nestingDynamicColumns, setNestingDynamicColumns] = useState<ColDef[]>([])
  
  // 主表数据状态
  const [currentNestingLayoutData, setCurrentNestingLayoutData] = useState<NestingLayoutData>({
    nestingEmployeeId: '',
    nestingDate: '',
    nestingDesc: '',
    rateOfFinished: 0,
    rateOfSurplus: 0
  })
  
 

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()

  // Konva画板状态
  const [rectangles, setRectangles] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [stageSize, setStageSize] = useState({ width: 800, height: 400 })

  // 初始化数据加载
  useEffect(() => {
    
    if (nestingLayoutId) {
      // 通过ID加载数据
      loadNestingLayoutData(nestingLayoutId)
    } else if (initialNestingLayoutData) {
      // 直接使用传入的数据
      initializeWithData(initialNestingLayoutData)
    } else {
      // 新建模式
      console.log('新建套料排版模式')
      showInfoToast('新建套料排版')
    }
  }, [nestingLayoutId, initialNestingLayoutData])

  // 数据加载函数
  const loadNestingLayoutData = async (id: string) => {
    console.log('开始加载套料排版数据:', id)
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/v1/nesting-layout/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          action: 'read',
          module: 'nesting-layout',
          data: { nestingLayoutId: id },
          timestamp: new Date().toISOString()
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          const data = result.data
          console.log('加载到的数据:', data)
          
          // 初始化数据
          initializeWithData(data)
          
          showSuccessToast(`成功加载套料排版: ${data.nestingLayoutId}`)
        } else {
          showErrorToast(`加载失败: ${result.message}`)
        }
      } else {
        showErrorToast(`加载失败: ${response.status}`)
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      showErrorToast(`加载失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 使用传入数据初始化
  const initializeWithData = (data: any) => {
    console.log('使用传入数据初始化:', data)
    
    // 设置主表数据
    setCurrentNestingLayoutData({
      ...data,
      nestingEmployeeId: data.nestingEmployeeId || '',
      nestingDate: data.nestingDate || '',
      nestingDesc: data.nestingDesc || '',
      rateOfFinished: data.rateOfFinished || 0,
      rateOfSurplus: data.rateOfSurplus || 0
    })
    
    // 设置明细表数据
    setTableData(data.nestingLayoutDList || [])
    
    // 初始化画板数据（如果有的话）
    if (data.nestingLayoutDList && data.nestingLayoutDList.length > 0) {
      initializeCanvasFromData(data.nestingLayoutDList)
    }
  }

  // 从数据初始化画板
  const initializeCanvasFromData = (details: any[]) => {
    const canvasRects = details.map((detail, index) => ({
      id: `rect-${detail.nestingLayoutDId || index}`,
      x: detail.startPositionX || (index * 120),
      y: detail.startPositionY || (index * 100),
      width: detail.endPositionX ? detail.endPositionX - detail.startPositionX : 100,
      height: detail.endPositionY ? detail.endPositionY - detail.startPositionY : 80,
      fill: '#4A90E2',
      stroke: '#2E5BBA',
      strokeWidth: 2,
      draggable: true,
      materialCode: detail.materialCode,
      materialDesc: detail.materialDescription
    }))
    
    setRectangles(canvasRects)
  }

  // AG-Grid 列定义
  const nestingColumnDefs: ColDef[] = useMemo(() => {
    const baseColumns: ColDef[] = [
      {
        headerName: '',
        field: 'select',
        width: 30,
        checkboxSelection: true,
        headerCheckboxSelection: true,
        filter: false
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
        headerName: '物料编码', 
        field: 'materialCode', 
        width: 120
      },
      { 
        headerName: '物料描述', 
        field: 'materialDescription', 
        width: 130
      },
      { 
        headerName: '仓库', 
        field: 'warehouseId', 
        width: 100
      },
      { 
        headerName: '库位', 
        field: 'binId', 
        width: 100
      },
      { 
        headerName: '批号', 
        field: 'lotNo', 
        width: 130
      },
      { 
        headerName: '库存数量', 
        field: 'stockQty', 
        width: 100,
        valueFormatter: (params: any) => {
          const value = params.value
          if (value === null || value === undefined) return ''
          return Number(value).toLocaleString()
        }
      },
      { 
        headerName: '可用数量', 
        field: 'availableStockQty', 
        width: 120,
        valueFormatter: (params: any) => {
          const value = params.value
          if (value === null || value === undefined) return ''
          return Number(value).toLocaleString()
        }
      },
      { 
        headerName: '本次用量', 
        field: 'nestingedQty', 
        width: 100,
        valueFormatter: (params: any) => {
          const value = params.value
          if (value === null || value === undefined) return ''
          return Number(value).toLocaleString()
        }
      },
      { 
        headerName: '剩余数量', 
        field: 'remainingStockQty', 
        width: 120,
        valueFormatter: (params: any) => {
          const value = params.value
          if (value === null || value === undefined) return ''
          return Number(value).toLocaleString()
        }
      }
    ]
  
    return [...baseColumns, ...nestingDynamicColumns]
  }, [nestingDynamicColumns])

  // AG-Grid 事件处理
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api)
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedNodes = gridApi.getSelectedNodes()
      const selectedIds = selectedNodes.map((node: any) => node.data.id)
      setSelectedRows(selectedIds)
    }
  }

  // 工具栏功能
  const handleRelease = () => {
    console.log('添加功能')
  }

  const handleDelete = () => {
    console.log('删除功能')
  }

  const handleSave = () => {
    console.log('保存功能')
  }

  const handleSearch = () => {
    console.log('查询功能')
  }

  const handleEdit = () => {
    console.log('编辑功能')
  }

  // Konva画板功能
  const addRectangle = () => {
    const newRect = {
      id: `rect-${Date.now()}`,
      x: Math.random() * (stageSize.width - 100),
      y: Math.random() * (stageSize.height - 100),
      width: 100,
      height: 80,
      fill: '#4A90E2',
      stroke: '#2E5BBA',
      strokeWidth: 2,
      draggable: true
    }
    setRectangles([...rectangles, newRect])
  }

  const clearCanvas = () => {
    setRectangles([])
    setSelectedId(null)
  }

  const handleRectClick = (id: string) => {
    setSelectedId(id)
  }

  const handleStageClick = (e: any) => {
    const clickedOnEmpty = e.target === e.target.getStage()
    if (clickedOnEmpty) {
      setSelectedId(null)
    }
  }

  const handleRectChange = (id: string, newAttrs: any) => {
    setRectangles(rectangles.map(rect => 
      rect.id === id ? { ...rect, ...newAttrs } : rect
    ))
  }

  return (
    <Box p={1} h="99%" display="flex" flexDirection="column">
      {/* 加载状态显示 */}
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
        >
          <Flex align="center" gap={2}>
            <Box
              width="4"
              height="4"
              borderRadius="full"
              bg="blue.500"
              animation="pulse 1.5s infinite"
            />
            <Text fontSize="sm" color="gray.600">加载数据中...</Text>
          </Flex>
        </Box>
      )}

      {/* 1. 工具栏区域 */}
      <Box 
        bg="white" 
        p={1} 
        borderRadius="md" 
        mb={1}
        border="1px" 
        borderColor="gray.200"
        flexShrink={0}
      >
                <HStack gap={2} justify="flex-start">
          <Button
            colorScheme="blue"
            variant="outline"
            size="sm"
            onClick={handleSearch}
            title="查询"
          >
            <FiSearch />
             
          </Button>
          <Button
            colorScheme="purple"
            variant="outline"
            size="sm"
            onClick={handleEdit}
            title="编辑"
          >
            <FiEdit />
             
          </Button>
          <Button
            colorScheme="blue"
            variant="outline"
            size="sm"
            onClick={handleSave}
            title="保存"
          >
            <FiSave />
             
          </Button>
          <Button
            colorScheme="red"
            variant="outline"
            size="sm"
            onClick={handleDelete}
            title="删除"
          >
            <FiTrash2 />
            
          </Button>
                     <Button
             colorScheme="green"
             variant="outline"
             size="sm"
             onClick={handleRelease}
             title="发布"
           >
             <FiSend />
               
           </Button>
        </HStack>
      </Box>

      {/* 2. 文本区域 */}
      <Box 
        bg="white" 
        p={1} 
        borderRadius="md" 
        mb={1}
        border="1px" 
        borderColor="gray.200"
        flexShrink={0}
      >
        <Grid templateColumns="repeat(3, 1fr)" gap={1}>
          <GridItem>
              <Flex align="center" gap={2}>
                <Text fontSize="sm" fontWeight="medium">套料人员</Text>
                <Input
                  size="sm"
                  value={currentNestingLayoutData.nestingEmployeeId}
                  onChange={(e) => setCurrentNestingLayoutData((prev: NestingLayoutData) => ({ ...prev, nestingEmployeeId: e.target.value }))}
                  flex="1"
                />
            </Flex>
          </GridItem>
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium">套料时间</Text>
              <Input
                size="sm"
                value={currentNestingLayoutData.nestingDate}
                onChange={(e) => setCurrentNestingLayoutData((prev: NestingLayoutData) => ({ ...prev, nestingDate: e.target.value }))}
                placeholder="请输入套料时间"
                flex="1"
              />
            </Flex>
          </GridItem>
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium">套料描述</Text>
              <Input
                size="sm"
                value={currentNestingLayoutData.nestingDesc}
                onChange={(e) => setCurrentNestingLayoutData((prev: NestingLayoutData) => ({ ...prev, nestingDesc: e.target.value }))}
                placeholder="请输入套料描述"
                flex="1"
              />
            </Flex>
          </GridItem>
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium">成材比率</Text>
              <Input
                size="sm"
                value={currentNestingLayoutData.rateOfFinished ? `${(currentNestingLayoutData.rateOfFinished * 100).toFixed(2)}%` : ''}
                onChange={(e) => {
                  const value = e.target.value.replace('%', '')
                  const numValue = parseFloat(value) / 100
                  setCurrentNestingLayoutData((prev: NestingLayoutData) => ({ 
                    ...prev, 
                    rateOfFinished: isNaN(numValue) ? 0 : numValue
                  }))
                }}
                placeholder="请输入成材比率"
                flex="1"
              />
            </Flex>
          </GridItem>
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium">余料比率</Text>
              <Input
                size="sm"
                value={currentNestingLayoutData.rateOfSurplus ? `${(currentNestingLayoutData.rateOfSurplus * 100).toFixed(2)}%` : ''}
                onChange={(e) => {
                  const value = e.target.value.replace('%', '')
                  const numValue = parseFloat(value) / 100
                  setCurrentNestingLayoutData((prev: NestingLayoutData) => ({ 
                    ...prev, 
                    rateOfSurplus: isNaN(numValue) ? 0 : numValue
                  }))
                }}
                placeholder="请输入余料比率"
                flex="1"
              />
            </Flex>
          </GridItem>
        </Grid>
      </Box>

      {/* 3. 明细表区域 (AG-Grid) */}
      <Box 
        bg="white" 
        p={1} 
        borderRadius="md" 
        mb={1}
        border="1px" 
        borderColor="gray.200"
        flex="1"
        minH="0"
      >
        <Box
          className="ag-theme-alpine"
          height="100%"
          width="100%"
          overflow="hidden"
        >
          <AgGridReact
            theme="legacy"
            columnDefs={nestingColumnDefs}
            rowData={tableData}
            onGridReady={onGridReady}
            onSelectionChanged={onSelectionChanged}
            rowSelection={{ mode: 'multiRow' }}
            pagination={true}
            paginationPageSize={20}
            suppressRowClickSelection={true}
            animateRows={true}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true
            }}
          />
        </Box>
      </Box>

      {/* 4. 画板区域 */}
      <Box 
        flex="1" 
        border="2px dashed #ccc" 
        borderRadius="md"
        overflow="hidden"
        bg="white"
      >
        <Stage
          width={stageSize.width}
          height={stageSize.height}
          onClick={handleStageClick}
          style={{ background: '#f8f9fa' }}
        >
          <Layer>
            {rectangles.map((rect) => (
              <Rect
                key={rect.id}
                {...rect}
                onClick={() => handleRectClick(rect.id)}
                onTap={() => handleRectClick(rect.id)}
                onDragEnd={(e) => {
                  handleRectChange(rect.id, {
                    x: e.target.x(),
                    y: e.target.y(),
                  })
                }}
              />
            ))}
            {selectedId && (
              <Transformer
                boundBoxFunc={(oldBox, newBox) => {
                  // 限制缩放范围
                  return newBox.width < 5 || newBox.height < 5 ? oldBox : newBox
                }}
              />
            )}
          </Layer>
        </Stage>
      </Box>
    </Box>
  )
}

export default NestingEdit 