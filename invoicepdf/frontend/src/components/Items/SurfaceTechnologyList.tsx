import React from "react"
import { Box, Text, Flex, Button, HStack, Input, Grid, GridItem, IconButton } from "@chakra-ui/react"
import { FiSearch, FiPlus, FiTrash2, FiDownload, FiUpload, FiChevronDown, FiChevronUp, FiFilter, FiRefreshCw } from "react-icons/fi"
import { useState, useRef, useEffect, useMemo } from "react"
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, GridApi, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

// 注册AG-Grid模块 - 包含所有社区功能
ModuleRegistry.registerModules([AllCommunityModule])
import useCustomToast from '../../hooks/useCustomToast'
import { getApiUrl, getAuthHeaders, API_CONFIG } from '../../client/unifiedTypes'

const SurfaceTechnologyList = () => {
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [isImporting, setIsImporting] = useState(false)
  const [tableData, setTableData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalItems, setTotalItems] = useState(0)
  const [sortField, setSortField] = useState<string>('')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 查询条件相关状态
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  const [queryConditions, setQueryConditions] = useState({
    surfaceCode: '',
    surfaceDesc: '',
    remark: ''
  })

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()







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

  // 执行查询
  const executeQuery = async () => {
    console.log("执行查询，条件:", queryConditions)
    setIsLoading(true)
    
    try {
      const response = await fetch(getApiUrl('/surface-technology/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'surface-technology',
          page: currentPage,
          limit: 500,
          filters: {
            surface_code: queryConditions.surfaceCode || undefined,
            surface_desc: queryConditions.surfaceDesc || undefined,
            remark: queryConditions.remark || undefined
          },
          sort: sortField ? { [sortField]: sortDirection } : undefined,
          timestamp: new Date().toISOString()
        })
      })

      // 检查响应状态
      if (!response.ok) {
        const errorText = await response.text()
        console.error('HTTP错误:', response.status, response.statusText, errorText)
        showErrorToast(`查询失败: ${response.status} ${response.statusText}`)
        return
      }

      // 尝试解析JSON
      let result
      try {
        result = await response.json()
      } catch (jsonError) {
        console.error('JSON解析失败:', jsonError)
        const responseText = await response.text()
        console.error('响应内容:', responseText)
        showErrorToast('服务器返回的数据格式错误')
        return
      }
      
      if (result.success) {
        setTableData(result.data || [])
        setTotalItems(result.pagination?.total || 0)
        showSuccessToast(result.message || '查询成功')
      } else {
        showErrorToast(result.message || '查询失败')
      }
    } catch (error) {
      console.error('查询失败:', error)
      showErrorToast('查询失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  // 清空查询条件
  const clearQueryConditions = () => {
    setQueryConditions({
      surfaceCode: '',
      surfaceDesc: '',
      remark: ''
    })
  }

  // 新增处理函数
  const handleAdd = () => {
    console.log("新增表面要求")
    // TODO: 实现新增逻辑
    showInfoToast("新增功能开发中...")
  }

  // 删除处理函数
  const handleDelete = async () => {
    if (selectedRows.length === 0) {
      showErrorToast("请先选择要删除的记录")
      return
    }
    
    if (!confirm(`确定要删除选中的 ${selectedRows.length} 条记录吗？`)) {
      return
    }
    
    setIsLoading(true)
    
    try {
      const deletePromises = selectedRows.map(async (surfaceTechnologyId) => {
        const response = await fetch(getApiUrl('/surface-technology/unified'), {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            action: 'delete',
            module: 'surface-technology',
            data: { surfaceTechnologyId: surfaceTechnologyId },
            timestamp: new Date().toISOString()
          })
        })
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error('删除HTTP错误:', response.status, response.statusText, errorText)
          return { success: false, message: `删除失败: ${response.status} ${response.statusText}` }
        }
        
        try {
          return await response.json()
        } catch (jsonError) {
          console.error('删除JSON解析失败:', jsonError)
          return { success: false, message: '服务器返回的数据格式错误' }
        }
      })
      
      const results = await Promise.all(deletePromises)
      const successCount = results.filter(result => result.success).length
      
      if (successCount > 0) {
        showSuccessToast(`成功删除 ${successCount} 条记录`)
        setSelectedRows([])
        // 重新加载数据
        await loadSurfaceTechnologyData()
      } else {
        showErrorToast('删除失败')
      }
    } catch (error) {
      console.error('删除失败:', error)
      showErrorToast('删除失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  // 导出处理函数
  const handleExport = () => {
    console.log("导出表面要求数据")
    // TODO: 实现导出逻辑
    showInfoToast("导出功能开发中...")
  }

  // 导入处理函数
  const handleImport = () => {
    console.log("导入表面要求数据")
    fileInputRef.current?.click()
  }

  // 文件上传处理
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsImporting(true)
    console.log("上传文件:", file.name)
    
    // TODO: 实现文件导入逻辑
    setTimeout(() => {
      setIsImporting(false)
      showSuccessToast("文件导入成功")
      if (event.target) {
        event.target.value = ''
      }
    }, 2000)
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
      resizable: false
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
      headerName: '表面代码', 
      field: 'surfaceCode', 
      width: 120,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '表面描述', 
      field: 'surfaceDesc', 
      width: 150,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '备注', 
      field: 'remark', 
      width: 150,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    }
  ], [])

  // 初始化数据
  useEffect(() => {
    loadSurfaceTechnologyData()
  }, [])

  // 加载surface technology数据
  const loadSurfaceTechnologyData = async () => {
    setIsLoading(true)
    
    try {
      const response = await fetch(getApiUrl('/surface-technology/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'surface-technology',
          page: currentPage,
          limit: pageSize,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        setTableData(result.data || [])
        setTotalItems(result.pagination?.total || 0)
      } else {
        console.error('加载数据失败:', result.message)
        showErrorToast(result.message || '加载数据失败')
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      showErrorToast('加载数据失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  // AG-Grid事件处理
  const onGridReady = (params: GridReadyEvent) => {
    console.log("AG-Grid准备就绪")
  }

  const onSelectionChanged = (event: any) => {
    const selectedNodes = event.api.getSelectedNodes()
    const selectedIds = selectedNodes.map((node: any) => node.data.surfaceTechnologyId)
    setSelectedRows(selectedIds)
  }

  // 行双击事件处理
  const onRowDoubleClicked = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.surfaceTechnologyId) {
      console.log("双击行数据:", rowData)
      
      // 触发自定义事件，通知父组件打开SurfaceTechnologyEdit TAB页
      const customEvent = new CustomEvent('openSurfaceTechnologyEditTab', {
        detail: {
          surfaceTechnologyId: rowData.surfaceTechnologyId,
          surfaceTechnologyData: rowData
        }
      })
      window.dispatchEvent(customEvent)
    }
  }
// 分页变更事件处理
  const onPaginationChanged = async (params:any) => {
    
  };

  return (
    <Box p={0} h="100%" display="flex" flexDirection="column">
      

      {/* 查询区域 */}
      <Box 
        bg="white" 
        p={1} 
        borderRadius="md" 
        mb={0}
        border="1px" 
        borderColor="gray.200"
        flexShrink={0}
      >
        {isQueryPanelOpen && (
          
          <Flex align="top" justify="space-between" gap={3}>
            <Grid templateColumns="repeat(3, 1fr)" gap={3}>
            <GridItem>
              <Flex align="center" gap={2}>
                <Text fontSize="sm" fontWeight="medium" minW="80px">表面代码</Text>
                <Input
                  size="sm"
                  placeholder="请输入表面代码"
                  value={queryConditions.surfaceCode}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('surfaceCode', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>
            
            <GridItem>
              <Flex align="center" gap={2}>
                <Text fontSize="sm" fontWeight="medium" minW="80px">表面描述</Text>
                <Input
                  size="sm"
                  placeholder="请输入表面描述"
                  value={queryConditions.surfaceDesc}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('surfaceDesc', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>
            
            <GridItem>
              <Flex align="center" gap={2}>
                <Text fontSize="sm" fontWeight="medium" minW="80px">备注</Text>
                <Input
                  size="sm"
                  placeholder="请输入备注"
                  value={queryConditions.remark}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('remark', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>
          </Grid>
            <Button
              colorScheme="blue"
              variant="outline"
              size="sm"
              onClick={executeQuery}
              title="查询"
            >
              <FiSearch />
              
            </Button>
            
          </Flex>
          
    
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

      {/* 数据表格 */}
      <Box
        className="ag-theme-alpine"
        width="100%"
        flex="0.9"
        minH="0"
        overflow="hidden"
      >
        <AgGridReact
            theme="legacy"
            columnDefs={columnDefs}
            rowData={tableData}
            onGridReady={onGridReady}
            onSelectionChanged={onSelectionChanged}
            onRowDoubleClicked={onRowDoubleClicked}
            rowSelection={{ mode: 'multiRow' }}
            pagination={true}
            paginationPageSize={20}
            suppressRowClickSelection={false}
            animateRows={true}
            paginationPageSizeSelector={[10, 20, 50]}
            onPaginationChanged={onPaginationChanged}
          />
      </Box>
    </Box>
  )
}

export default SurfaceTechnologyList 