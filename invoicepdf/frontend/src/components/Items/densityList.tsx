import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { Box, Button, Flex, Text, Input, HStack, VStack, useDisclosure, Grid, GridItem, IconButton } from '@chakra-ui/react'
import { FiChevronDown, FiChevronUp, FiSearch, FiTrash2, FiDownload, FiUpload, FiPlus } from 'react-icons/fi'
import { AgGridReact } from 'ag-grid-react'
import { GridReadyEvent, ColDef } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import { getApiUrl, getAuthHeaders } from '../../client/unifiedTypes'
import useCustomToast from '../../hooks/useCustomToast'

// 注册AG-Grid模块 - 包含所有社区功能
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
ModuleRegistry.registerModules([AllCommunityModule])

const DensityList = () => {
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [tableData, setTableData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalItems, setTotalItems] = useState(0)

  // 导入导出相关状态
  const [isImporting, setIsImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 查询条件相关状态
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  const [queryConditions, setQueryConditions] = useState({
    materialCode: '',
    materialDesc: '',
    density: '',
    densityUnitId: '',
    remark: ''
  })

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  const showErrorToastRef = useRef(showErrorToast)
  const isInitializedRef = useRef(false)
  
  // 更新ref
  useEffect(() => {
    showErrorToastRef.current = showErrorToast
  }, [showErrorToast])

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
  const handleQuery = async () => {
    setIsLoading(true)
    
    try {
      const response = await fetch(getApiUrl('/material-density/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'material-density',
          page: 1, // 重置到第一页
          limit: pageSize,
          filters: {
            material_code: queryConditions.materialCode || undefined,
            material_desc: queryConditions.materialDesc || undefined,
            density: queryConditions.density || undefined,
            density_unit_id: queryConditions.densityUnitId || undefined,
            remark: queryConditions.remark || undefined
          },

          timestamp: new Date().toISOString()
        })
      })

      // 检查响应状态
      if (!response.ok) {
        const errorText = await response.text()
        console.error('HTTP错误:', response.status, response.statusText, errorText)
        showErrorToastRef.current(`查询失败: ${response.status} ${response.statusText}`)
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
        showErrorToastRef.current('服务器返回的数据格式错误')
        return
      }
      
      if (result.success) {
        setTableData(result.data || [])
        setTotalItems(result.pagination?.total || 0)
        setCurrentPage(1) // 重置到第一页
        showSuccessToast(result.message || '查询成功')
      } else {
        showErrorToastRef.current(result.message || '查询失败')
      }
    } catch (error) {
      console.error('查询失败:', error)
      showErrorToastRef.current('查询失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  // 清空查询条件
  const clearQueryConditions = () => {
    setQueryConditions({
      materialCode: '',
      materialDesc: '',
      density: '',
      densityUnitId: '',
      remark: ''
    })
  }




  // 新增处理函数
  const handleAdd = () => {
    console.log("新增密度")
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
      const deletePromises = selectedRows.map(async (materialId) => {
        const response = await fetch(getApiUrl('/material-density/unified'), {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            action: 'delete',
            module: 'material-density',
            data: { materialDensityId: materialId },
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
        await loadDensityData()
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





  // AG-Grid列定义
  const columnDefs: ColDef[] = useMemo(() => [
    {
      headerName: '',
      checkboxSelection: true,
      headerCheckboxSelection: true,
      width: 40,
      sortable: false,
      filter: false,
      resizable: false
    },
    { 
      headerName: '行号', 
      width: 70,
      field: 'seq', 
      valueGetter: (params) => {
        const rowIndex = params.node?.rowIndex || 0;
        return String(rowIndex + 1).padStart(4, '0');
      }
    },
    { 
      headerName: '材质编码', 
      field: 'materialCode',
      width: 120
    },
    { 
      headerName: '材质描述', 
      field: 'materialDesc',
      width: 160
    },
    { 
      headerName: '密度值', 
      field: 'density',
      width: 100
    },
    { 
      headerName: '密度单位', 
      field: 'densityUnitId',
      width: 100
    },
    { 
      headerName: '备注', 
      field: 'remark',
      width: 160
    }
  ], [])

  // 加载密度数据
  const loadDensityData = useCallback(async () => {
    console.log('🔄 loadDensityData 被调用', { currentPage, pageSize, timestamp: new Date().toISOString() })
    setIsLoading(true)
    
    try {
      const response = await fetch(getApiUrl('/material-density/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'material-density',
          page: currentPage,
          limit: pageSize,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        console.log('✅ 加载的数据:', result.data)
        setTableData(result.data || [])
        setTotalItems(result.pagination?.total || 0)
      } else {
        console.error('❌ 加载数据失败:', result.message)
        showErrorToastRef.current(result.message || '加载数据失败')
      }
    } catch (error) {
      console.error('❌ 加载数据失败:', error)
      showErrorToastRef.current('加载数据失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }, [currentPage, pageSize])

  // 初始化和分页变化时加载数据
  useEffect(() => {
    console.log('🔄 useEffect 执行，加载数据', { currentPage, pageSize })
    loadDensityData()
  }, [currentPage, pageSize])

  // AG-Grid事件处理
  const onGridReady = (params: GridReadyEvent) => {
    console.log("AG-Grid准备就绪")
    console.log("表格数据:", params.api.getRenderedNodes().map(node => node.data))
    console.log("第一行数据示例:", params.api.getRenderedNodes()[0]?.data)
    console.log("materialDensityId字段存在:", params.api.getRenderedNodes()[0]?.data?.materialDensityId)
  }

  const onSelectionChanged = (event: any) => {
    const selectedNodes = event.api.getSelectedNodes()
    const selectedIds = selectedNodes.map((node: any) => node.data.materialDensityId)
    console.log('选中的行:', selectedIds)
    console.log('选中的节点数据:', selectedNodes.map((node: any) => node.data))
    setSelectedRows(selectedIds)
  }

  // 行双击事件处理
  const onRowDoubleClicked = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.materialDensityId) {
      console.log("双击行数据:", rowData)
      
      // 触发自定义事件，通知父组件打开DensityEdit TAB页
      const customEvent = new CustomEvent('openDensityEditTab', {
        detail: {
          materialDensityId: rowData.materialDensityId,
          densityData: rowData
        }
      })
      window.dispatchEvent(customEvent)
    }
  }

  return (
    <>

      <Box p={0} h="100vh" display="flex" flexDirection="column" overflow="auto" position="relative">
       
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
            <Grid templateColumns="repeat(3, 1fr)" gap={1}>
            <GridItem>
                  <Flex align="center" gap={3}>
                    <Text fontSize="sm" fontWeight="medium">材质编码</Text>
                    <Input
                      size="sm"
                      value={queryConditions.materialCode}
                      onChange={(e) => handleQueryConditionChange('materialCode', e.target.value)}
                      placeholder="请输入材质编码"
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                  <Flex align="center" gap={2}>
                    <Text fontSize="sm" fontWeight="medium">材质描述</Text>
                    <Input
                      size="sm"
                      value={queryConditions.materialDesc}
                      onChange={(e) => handleQueryConditionChange('materialDesc', e.target.value)}
                      placeholder="请输入材质描述"
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">密度</Text>
                  <Input
                    size="sm"
                    value={queryConditions.density}
                    onChange={(e) => handleQueryConditionChange('density', e.target.value)}
                    placeholder="请输入密度值"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              
              
            </Grid>
            <Button
              colorScheme="blue"
              variant="outline"
              size="sm"
              onClick={handleQuery}
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
        flex="0.85"
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
          paginationPageSize={pageSize}
          getRowId={(params) => params.data.materialDensityId}
          suppressCellFocus={true}
          suppressRowClickSelection={false}
        />
      </Box>
      
      
    </Box>
    </>
  )
}

export default DensityList 