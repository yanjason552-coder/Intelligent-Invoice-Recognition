import React, { useState, useMemo, useEffect } from "react"
import { 
  Box, 
  Button, 
  HStack,
  Text,
  Input,
  Grid,
  GridItem,
  Flex,
  IconButton
} from "@chakra-ui/react"
import { FiTrash2,  FiSearch,   FiChevronUp, FiChevronDown } from "react-icons/fi"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import useCustomToast from '../../hooks/useCustomToast'

// 注册AG-Grid模块
ModuleRegistry.registerModules([AllCommunityModule])

const NestingList = () => {
  // 查询条件
  const [condition, setCondition] = useState({
    title: '',
    description: '',
    remark: '',
    materialRatio: '',
    wasteRatio: ''
  })
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  const [pageSize, setPageSize] = useState(20)
  // AG-Grid状态
  const [tableData, setTableData] = useState<any[]>([])
  const [gridApi, setGridApi] = useState<any>(null)
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  // 工具栏功能
  const handleSearch = async () => {
    console.log('执行查询，条件:', condition)
    setIsLoading(true)
    
    try {
      // 构建请求体
      const requestBody: any = {
        action: 'list',
        module: 'nesting-layout',
        page: 1,
        limit: 500,
        timestamp: new Date().toISOString()
      }
      
      // 添加查询条件
      const filters: any = {}
      if (condition.title) {
        filters.nestingDesc = `%${condition.title}%`
      }
      if (condition.description) {
        filters.nestingEmployeeId = `%${condition.description}%`
      }
      if (condition.materialRatio) {
        filters.nestingDate = `%${condition.materialRatio}%`
      }
      if (condition.remark) {
        filters.remark = `%${condition.remark}%`
      }
      if (condition.wasteRatio) {
        filters.nestingedQty = parseFloat(condition.wasteRatio)
      }
      
      if (Object.keys(filters).length > 0) {
        requestBody.filters = filters
      }
      
      console.log("查询请求体:", requestBody)
      
      // 调用API进行查询
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
          console.log("查询成功:", result.data)
          setTableData(result.data || [])
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

  // 清空查询条件
  const clearQueryConditions = () => {
    setCondition({
      title: '',
      description: '',
      remark: '',
      materialRatio: '',
      wasteRatio: ''
    })
  }

  // 加载初始数据
  const loadInitialData = async () => {
    setIsLoading(true)
    try {
      const requestBody = {
        action: 'list',
        module: 'nesting-layout',
        page: 1,
        limit: 500,
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
          setTableData(result.data || [])
          showSuccessToast('数据加载成功')
        } else {
          showErrorToast(`数据加载失败: ${result.message}`)
        }
      } else {
        showErrorToast(`数据加载失败: ${response.status}`)
      }
    } catch (error) {
      console.error('加载初始数据失败:', error)
      showErrorToast(`数据加载失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 初始化加载数据
  useEffect(() => {
    loadInitialData()
  }, [])

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
      const deletePromises = selectedRows.map(async (nestingLayoutId) => {
        const response = await fetch('/api/v1/nesting-layout/unified', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            action: 'delete',
            module: 'nesting-layout',
            data: { nestingLayoutId: nestingLayoutId },
            timestamp: new Date().toISOString()
          })
        })
        
        if (!response.ok) {
          throw new Error(`删除失败: ${response.status}`)
        }
        
        const result = await response.json()
        if (!result.success) {
          throw new Error(result.message || '删除失败')
        }
        
        return result
      })
      
      await Promise.all(deletePromises)
      
      showSuccessToast(`成功删除 ${selectedRows.length} 条记录`)
      setSelectedRows([])
      
      // 重新加载数据
      await loadInitialData()
      
    } catch (error) {
      console.error('删除失败:', error)
      showErrorToast(`删除失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 切换查询面板显示状态
  const toggleQueryPanel = () => {
    setIsQueryPanelOpen(!isQueryPanelOpen)
  }

  // 条件变更处理函数
  const handleConditionChange = (updater: (prev: any) => any) => {
    setCondition(updater)
  }

  // AG-Grid 事件处理
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api)
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedNodes = gridApi.getSelectedNodes()
      const selectedIds = selectedNodes.map((node: any) => node.data.nestingLayoutId)
      setSelectedRows(selectedIds)
    }
  }

  // 行双击事件处理
  const onRowDoubleClicked = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.nestingLayoutId) {
      console.log('双击行数据:', rowData)
      
      // 触发自定义事件，打开NestingEdit TAB页
      const customEvent = new CustomEvent('openNestingEditTab', {
        detail: {
          nestingLayoutId: rowData.nestingLayoutId,
          nestingLayoutData: rowData // 传递完整的行数据到编辑页面
        }
      })
      window.dispatchEvent(customEvent)
    }
  }

  // AG-Grid 列定义
  const columnDefs: ColDef[] = useMemo(() => {
    return [
      {
        headerName: '',
        field: 'select',
        width: 40,
        checkboxSelection: true,
        headerCheckboxSelection: true,
        filter: false
      },
      
      { 
        headerName: '工厂', 
        field: 'plantId', 
        width: 100
      },
      { 
        headerName: '套料人员', 
        field: 'nestingEmployeeId', 
        width: 100
      },
      { 
        headerName: '套料时间', 
        field: 'nestingDate', 
        width: 180
      },
      { 
        headerName: '套料说明', 
        field: 'nestingDesc', 
        width: 150
      }
    ]
  }, [])
  return (
    <Box p={1} h="99%" display="flex" flexDirection="column">
     
      {/* 2. 查询区域 */}
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
                    <Text fontSize="sm" fontWeight="medium">套料说明</Text>
                    <Input
                      size="sm"
                      value={condition.title}
                      onChange={(e) => handleConditionChange(prev => ({ ...prev, title: e.target.value }))}
                      placeholder="请输入套料说明"
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                  <Flex align="center" gap={2}>
                    <Text fontSize="sm" fontWeight="medium">套料人员</Text>
                    <Input
                      size="sm"
                      value={condition.description}
                      onChange={(e) => handleConditionChange(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="请输入套料人员"
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">套料日期</Text>
                  <Input
                    size="sm"
                    value={condition.materialRatio}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, materialRatio: e.target.value }))}
                    placeholder="请输入套料日期"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">备注</Text>
                  <Input
                    size="sm"
                    value={condition.remark}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, remark: e.target.value }))}
                    placeholder="请输入备注"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              
            </Grid>
            <Button
              colorScheme="blue"
              variant="outline"
              size="sm"
              onClick={handleSearch}
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
          theme="legacy"
          columnDefs={columnDefs}
          rowData={tableData}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          onRowDoubleClicked={onRowDoubleClicked}
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
      

    </Box>
  )
}

export default NestingList 