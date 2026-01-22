import { 
  Box, 
  Text, 
  Flex, 
  VStack, 
  Button, 
  Input
} from "@chakra-ui/react"
import { FiX } from "react-icons/fi"
import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

// 注册AG-Grid模块
ModuleRegistry.registerModules([AllCommunityModule])

// 表格列定义接口
export interface TableColumn {
  key: string
  title: string
  width?: string | number
  render?: (value: any, record: any, index: number) => React.ReactNode
}

// 表格数据行接口
export interface TableDataRow {
  [key: string]: any
  _id?: string // 唯一标识符，如果没有会自动生成
}

// API 配置接口
export interface ApiConfig {
  // API 端点
  endpoint: string
  // 请求方法
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  // 请求参数
  params?: Record<string, any>
  // 请求头
  headers?: Record<string, string>
  // 数据转换函数
  transform?: (response: any) => TableDataRow[]
  // 错误处理
  onError?: (error: any) => void
}

// 过滤条件接口
export interface FilterConfig {
  // 搜索字段
  searchFields?: string[]
  // 自定义过滤函数
  customFilter?: (row: TableDataRow, searchText: string) => boolean
  // 预过滤条件
  preFilters?: Record<string, any>
}

// 显示配置接口
export interface DisplayConfig {
  // 主键字段
  primaryKey?: string
  // 显示字段
  displayFields?: string[]
  // 自定义显示函数
  displayFormatter?: (row: TableDataRow) => string
}

// 返回值配置接口
export interface ReturnConfig {
  // 返回值字段
  returnFields?: string[]
  // 自定义返回值转换
  returnTransformer?: (row: TableDataRow) => any
}

// 对话框属性接口
export interface TableSelectDialogProps {
  // 显示控制
  visible: boolean
  x: number
  y: number
  
  // 数据相关（静态数据）
  data?: TableDataRow[]
  columns: TableColumn[]
  loading?: boolean
  
  // API 配置（动态数据）
  apiConfig?: ApiConfig
  
  // 过滤配置
  filterConfig?: FilterConfig
  
  // 显示配置
  displayConfig?: DisplayConfig
  
  // 返回值配置
  returnConfig?: ReturnConfig
  
  // 配置选项
  title?: string
  searchable?: boolean
  searchPlaceholder?: string
  multiSelect?: boolean
  maxHeight?: string | number
  minWidth?: string | number
  
  // 事件回调
  onClose: () => void
  onSelect: (selectedRows: TableDataRow[], selectedRow?: TableDataRow) => void
  onDoubleClick?: (row: TableDataRow, index: number) => void
  
  // 拖拽相关
  isDragging?: boolean
  dragOffset?: { x: number; y: number }
  onStartDrag?: (e: React.MouseEvent) => void
}

const TableSelectDialog: React.FC<TableSelectDialogProps> = ({
  visible,
  x,
  y,
  data = [],
  columns = [],
  loading = false,
  apiConfig,
  filterConfig,
  displayConfig,
  returnConfig,
  title = "选择数据",
  searchable = true,
  searchPlaceholder = "搜索...",
  multiSelect = true,
  maxHeight = "400px",
  minWidth = "600px",
  onClose,
  onSelect,
  onDoubleClick,
  isDragging = false,
  dragOffset = { x: 0, y: 0 },
  onStartDrag
}) => {
  const [searchText, setSearchText] = useState("")
  const [selectedRowIds, setSelectedRowIds] = useState<Set<string>>(new Set())
  const [apiData, setApiData] = useState<TableDataRow[]>([])
  const [apiLoading, setApiLoading] = useState(false)
  
  // 获取数据源（静态数据或API数据）
  const dataSource = useMemo(() => {
    if (apiConfig) {
      return apiData
    }
    return data
  }, [apiConfig, apiData, data])
  
  // 为数据添加唯一ID（如果没有的话）
  const dataWithIds = useMemo(() => {
    return dataSource.map((item, index) => ({
      ...item,
      _id: item._id || item.id || `row_${index}`
    }))
  }, [dataSource])
  
  // API 数据获取
  const fetchApiData = useCallback(async () => {
    if (!apiConfig) return
    
    setApiLoading(true)
    try {
      const response = await fetch(apiConfig.endpoint, {
        method: apiConfig.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...apiConfig.headers
        },
        body: apiConfig.method !== 'GET' ? JSON.stringify(apiConfig.params) : undefined
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      const transformedData = apiConfig.transform ? apiConfig.transform(result) : result
      setApiData(transformedData)
    } catch (error) {
      console.error('API 数据获取失败:', error)
      if (apiConfig.onError) {
        apiConfig.onError(error)
      }
    } finally {
      setApiLoading(false)
    }
  }, [apiConfig])
  
  // 组件挂载时获取API数据
  useEffect(() => {
    if (visible && apiConfig) {
      fetchApiData()
    }
  }, [visible, apiConfig, fetchApiData])
  
  // 过滤数据
  const filteredData = useMemo(() => {
    let result = dataWithIds
    
    // 应用预过滤条件
    if (filterConfig?.preFilters) {
      result = result.filter(row => {
        return Object.entries(filterConfig.preFilters!).every(([key, value]) => {
          return (row as any)[key] === value
        })
      })
    }
    
    // 应用搜索过滤
    if (searchText.trim()) {
      const searchLower = searchText.toLowerCase()
      result = result.filter(row => {
        if (filterConfig?.customFilter) {
          return filterConfig.customFilter(row, searchText)
        }
        
        // 默认搜索逻辑
        const searchFields = filterConfig?.searchFields || columns.map(col => col.key)
        return searchFields.some(field => {
          const value = (row as any)[field]
          return value && String(value).toLowerCase().includes(searchLower)
        })
      })
    }
    
    return result
  }, [dataWithIds, searchText, columns, filterConfig])

  // 转换为 AG-Grid 列定义
  const agGridColumns = useMemo(() => {
    const cols: ColDef[] = []
    
    if (multiSelect) {
      cols.push({
        headerName: '',
        field: '_select',
        width: 50,
        checkboxSelection: true,
        headerCheckboxSelection: true,
        pinned: 'left'
      })
    }
    
    columns.forEach(col => {
      cols.push({
        headerName: col.title,
        field: col.key,
        width: col.width ? (typeof col.width === 'number' ? col.width : 150) : 150,
        cellRenderer: col.render ? (params: any) => {
          return col.render!(params.value, params.data, params.rowIndex)
        } : undefined
      })
    })
    
    return cols
  }, [columns, multiSelect])
  
  // 重置选择状态
  useEffect(() => {
    if (visible) {
      setSelectedRowIds(new Set())
      setSearchText("")
    }
  }, [visible])
  
  // AG-Grid 选择变化处理
  const onSelectionChanged = () => {
    if (gridRef.current) {
      const selectedNodes = gridRef.current.api.getSelectedNodes()
      const selectedIds = new Set(selectedNodes.map(node => node.data._id))
      setSelectedRowIds(selectedIds)
    }
  }

  // 网格引用
  const gridRef = useRef<AgGridReact>(null)
  
  // 处理行双击
  const handleRowDoubleClick = (row: TableDataRow, index: number) => {
    if (onDoubleClick) {
      onDoubleClick(row, index)
    } else {
      // 默认行为：选择该行并关闭对话框
      const selectedRows = [row]
      onSelect(selectedRows, row)
      onClose()
    }
  }
  
  // 处理确认选择
  const handleConfirmSelect = () => {
    const selectedRows = filteredData.filter(row => selectedRowIds.has(row._id))
    
    // 应用返回值转换
    let processedRows = selectedRows
    if (returnConfig?.returnTransformer) {
      processedRows = selectedRows.map(returnConfig.returnTransformer)
    } else if (returnConfig?.returnFields) {
      processedRows = selectedRows.map(row => {
        const result: any = {}
        returnConfig.returnFields!.forEach(field => {
          result[field] = (row as any)[field]
        })
        return result
      })
    }
    
    onSelect(processedRows, processedRows[0])
    onClose()
  }
  
  if (!visible) return null
  
  return (
    <Box
      position="fixed"
      left={x}
      top={y}
      bg="white"
      border="1px"
      borderColor="gray.200"
      borderRadius="md"
      boxShadow="lg"
      zIndex={9999}
      minW={minWidth}
      maxH={maxHeight}
      overflow="hidden"
      style={{ pointerEvents: 'auto' }}
    >
      {/* 标题栏 */}
      <Flex 
        bg="gray.50" 
        p={3} 
        borderBottom="1px" 
        borderColor="gray.200"
        justify="space-between"
        align="center"
        cursor={onStartDrag ? "move" : "default"}
        onMouseDown={onStartDrag}
        userSelect="none"
      >
        <Text fontSize="sm" fontWeight="medium">{title}</Text>
        <Button
          size="xs"
          variant="ghost"
          onClick={onClose}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <FiX />
        </Button>
      </Flex>
      
      {/* 搜索栏 */}
      {searchable && (
        <Box p={3} borderBottom="1px" borderColor="gray.100">
          <Input
            placeholder={searchPlaceholder}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            bg="white"
            size="sm"
          />
        </Box>
      )}
      
      {/* 表格内容 */}
      <Box maxH="300px" overflow="hidden">
        {(loading || apiLoading) ? (
          <Flex justify="center" align="center" h="100px">
            <VStack gap={2}>
              <Box
                width="4"
                height="4"
                borderRadius="full"
                bg="blue.500"
                animation="pulse 1.5s infinite"
              />
              <Text fontSize="sm" color="gray.600">加载数据中...</Text>
            </VStack>
          </Flex>
        ) : filteredData.length === 0 ? (
          <Flex justify="center" align="center" h="100px">
            <Text fontSize="sm" color="gray.500">
              {data.length === 0 ? "暂无数据" : "未找到匹配的数据"}
            </Text>
          </Flex>
        ) : (
          <Box h="300px" w="100%" overflow="hidden">
            <AgGridReact
              ref={gridRef}
              rowData={filteredData}
              theme="legacy"
              columnDefs={agGridColumns}
              rowSelection={multiSelect ? { mode: 'multiRow' } : { mode: 'singleRow' }}
              onSelectionChanged={onSelectionChanged}
              onRowDoubleClicked={(event) => {
                if (event.data && event.rowIndex !== null) {
                  handleRowDoubleClick(event.data, event.rowIndex)
                }
              }}
              defaultColDef={{
                resizable: true,
                sortable: true,
                filter: true
              }}
              suppressRowClickSelection={false}
              animateRows={true}
              className="ag-theme-alpine"
            />
          </Box>
        )}
      </Box>
      
      {/* 底部按钮 */}
      {multiSelect && (
        <Flex 
          p={3} 
          borderTop="1px" 
          borderColor="gray.200" 
          justify="space-between" 
          align="center"
          bg="gray.50"
        >
          <Text fontSize="sm" color="gray.600">
            已选择 {selectedRowIds.size} 项
          </Text>
          <Flex gap={2}>
            <Button size="sm" variant="ghost" onClick={onClose}>
              取消
            </Button>
            <Button 
              size="sm" 
              colorScheme="blue" 
              onClick={handleConfirmSelect}
              disabled={selectedRowIds.size === 0}
            >
              确定
            </Button>
          </Flex>
        </Flex>
      )}
    </Box>
  )
}

export default TableSelectDialog

