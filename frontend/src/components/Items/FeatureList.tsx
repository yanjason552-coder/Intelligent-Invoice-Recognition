import React from "react"
import { Box, Text, Flex, Button, Input, Grid, GridItem, IconButton } from "@chakra-ui/react"
import { FiSearch, FiChevronDown, FiChevronUp, } from "react-icons/fi"
import { useState, useRef, useEffect, useMemo } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

// 注册AG-Grid模块 - 包含所有社区功能
ModuleRegistry.registerModules([AllCommunityModule])
import useCustomToast from '../../hooks/useCustomToast'

const FeatureList = () => {
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  
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
    featureCode: '',
    featureDesc: '',
    dataType: '',
    dataLen: '',
    remark: ''
  })

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()

  // 格式化日期函数 - 只显示日期部分
  const formatDate = (dateString: string | null) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      return date.toISOString().split('T')[0] // 只返回 YYYY-MM-DD 格式
    } catch (error) {
      return dateString
    }
  }

  // 格式化数值函数 - 自定义小数点位数
  const formatNumber = (value: number | null, decimals: number = 2) => {
    if (value === null || value === undefined) return ''
    return Number(value).toFixed(decimals)
  }

  // 字段定义 - 对应feature实体的字段名和注释
  const fieldDefinitions = [
    { field: 'feature_id', label: '属性ID' },
    { field: 'feature_code', label: '属性编码' },
    { field: 'feature_desc', label: '属性描述' },
    { field: 'data_len', label: '数据长度' },
    { field: 'data_type', label: '数据类型' },
    { field: 'data_ranger', label: '数据范围' },
    { field: 'data_min', label: '最小值' },
    { field: 'data_max', label: '最大值' },
    { field: 'remark', label: '备注' },
    { field: 'creator', label: '创建人' },
    { field: 'create_date', label: '创建日期' },
    { field: 'modifier_last', label: '最后修改人' },
    { field: 'modify_date_last', label: '最后修改日期' },
    { field: 'approve_status', label: '审批状态' },
    { field: 'approver', label: '审批人' },
    { field: 'approve_date', label: '审批日期' }
  ]

  

  // 切换查询面板显示状态
  const toggleQueryPanel = () => {
    setIsQueryPanelOpen(!isQueryPanelOpen)
  }

  // 处理查询条件变化
  const handleConditionChange = (updater: (prev: any) => any) => {
    setQueryConditions(updater)
  }

  // 执行查询
  const executeQuery = async () => {
    console.log("执行查询，条件:", queryConditions)
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/v1/feature/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          action: 'list',
          module: 'feature',
          page: currentPage,
          limit: pageSize,
          filters: {
            feature_code: queryConditions.featureCode || undefined,
            feature_desc: queryConditions.featureDesc || undefined,
            data_type: queryConditions.dataType || undefined,
            data_len: queryConditions.dataLen || undefined,
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
      featureCode: '',
      featureDesc: '',
      dataType: '',
      dataLen: '',
      remark: ''
    })
  }

  // 新增处理函数
  const handleAdd = () => {
    console.log("新增物料属性")
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
      const deletePromises = selectedRows.map(async (featureId) => {
        const response = await fetch('/api/v1/feature/unified', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            action: 'delete',
            module: 'feature',
            data: { feature_id: featureId },
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
        await loadFeatureData()
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
    console.log("导出物料属性数据")
    // TODO: 实现导出逻辑
    showInfoToast("导出功能开发中...")
  }

  // 导入处理函数
  const handleImport = () => {
    console.log("导入物料属性数据")
    fileInputRef.current?.click()
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
      headerName: '属性编码', 
      field: 'featureCode', 
      width: 100,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '属性描述', 
      field: 'featureDesc', 
      width: 120,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '数据长度', 
      field: 'dataLen', 
      width: 100,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['equals', 'lessThan', 'greaterThan', 'inRange']
      },
      cellStyle: { 
        textAlign: 'right'
      }
    },
    { 
      headerName: '数据类型', 
      field: 'dataTypeDesc', 
      width: 100,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '数据范围', 
      field: 'dataRangeDesc', 
      width: 100,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '最小值', 
      field: 'dataMin', 
      width: 90,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['equals', 'lessThan', 'greaterThan', 'inRange']
      }
    },
    { 
      headerName: '最大值', 
      field: 'dataMax', 
      width: 90,
      sortable: true,
      filter: true,
      filterParams: {
        filterOptions: ['equals', 'lessThan', 'greaterThan', 'inRange']
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
    loadFeatureData()
  }, [])

  // 加载feature数据
  const loadFeatureData = async () => {
    setIsLoading(true)
    
    try {
      const response = await fetch('/api/v1/feature/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          action: 'list',
          module: 'feature',
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
    const selectedIds = selectedNodes.map((node: any) => node.data.featureId)
    setSelectedRows(selectedIds)
  }

  // 行双击事件处理
  const onRowDoubleClicked = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.featureId) {
      console.log("双击行数据:", rowData)
      
      // 触发自定义事件，通知父组件打开FeatureEdit TAB页
      const customEvent = new CustomEvent('openFeatureEditTab', {
        detail: {
          featureId: rowData.featureId,
          featureData: rowData
        }
      })
      window.dispatchEvent(customEvent)
    }
  }

  return (
    <Box p={0} h="99%" display="flex" flexDirection="column">
       
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
                  <Flex align="center" gap={1}>
                    <Text fontSize="sm" fontWeight="medium">特征代码</Text>
                    <Input
                      size="sm"
                      value={queryConditions.featureCode}
                      onChange={(e) => handleConditionChange(prev => ({ ...prev, featureCode: e.target.value }))}
                      placeholder="请输入特征代码"
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                  <Flex align="center" gap={1}>
                    <Text fontSize="sm" fontWeight="medium">特征名称</Text>
                    <Input
                      size="sm"
                      value={queryConditions.featureDesc}
                      onChange={(e) => handleConditionChange(prev => ({ ...prev, featureDesc: e.target.value }))}
                      placeholder="请输入特征名称"
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={1}>
                  <Text fontSize="sm" fontWeight="medium">数据类型</Text>
                  <Input
                    size="sm"
                    value={queryConditions.dataType}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, dataType: e.target.value }))}
                    placeholder="请输入数据类型"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={1}>
                  <Text fontSize="sm" fontWeight="medium">备注</Text>
                  <Input
                    size="sm"
                    value={queryConditions.remark}
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
        flex="0.95"
        minH="0"
        position="relative"
        overflow="hidden"
        width="100%"
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
          suppressRowClickSelection={false}
          animateRows={true}
          
          
          // 空数据提示
          noRowsOverlayComponent={() => (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '100%',
              color: '#666',
              fontSize: '14px'
            }}>
              暂无数据
            </div>
          )}
          // 行样式
          getRowStyle={(params) => ({
            cursor: 'pointer'
          })}
        />
      </Box>
    </Box>
  )
}

export default FeatureList 