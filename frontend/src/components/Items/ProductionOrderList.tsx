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

const ProductionOrderList = () => {
  // 查询条件
  const [condition, setCondition] = useState({
    docNo: '',
    docDate: '',
    materialCode: '',
    materialDescription:'',
    status: ''
  })
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  const [pageSize, setPageSize] = useState(20)
  // AG-Grid状态
  const [tableData, setTableData] = useState<any[]>([])
  const [gridApi, setGridApi] = useState<any>(null)
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  // 查询生产订单
  const handleSearch = async () => {
    console.log('执行查询，条件:', condition)
    setIsLoading(true)
    
    try {
      // 构建请求体
      const requestBody: any = {
        action: 'list',
        module: 'productionOrder',
        page: 1,
        limit: 500,
        timestamp: new Date().toISOString()
      }
      
      // 添加查询条件
      const filters: any = {}
      if (condition.docNo) {
        filters.orderNo = `%${condition.docNo}%`
      }
      if (condition.docDate) {
        filters.docDate = `%${condition.docDate}%`
      }
      if (condition.materialCode) {
        filters.materialCode = `%${condition.materialCode}%`
      }
      if (condition.materialDescription) {
        filters.materialDescription = `%${condition.materialDescription}%`
      }
      if (condition.status) {
        filters.status = condition.status
      }
      
      if (Object.keys(filters).length > 0) {
        requestBody.filters = filters
      }
      
      console.log("查询请求体:", requestBody)
      
      // 调用API进行查询
      const response = await fetch('/api/v1/productionOrder/unified', {
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
      docNo: '',
      docDate: '',
      materialCode: '',
      materialDescription: '',
      status: ''
    })
  }

  // 加载初始数据
  const loadInitialData = async () => {
    setIsLoading(true)
    try {
      
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
      const selectedIds = selectedNodes.map((node: any) => node.data.productionOrderId)
      setSelectedRows(selectedIds)
    }
  }

  // 行双击事件处理
  const onRowDoubleClicked = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.productionOrderId) {
      console.log('双击行数据:', rowData)
      
      // 触发自定义事件，打开ProductionOrderEdit TAB页
      const customEvent = new CustomEvent('openProductionOrderEditTab', {
        detail: {
          productionOrderId: rowData.productionOrderId,
          productionOrderData: rowData // 传递完整的行数据到编辑页面
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
        field: 'plantName', 
        width: 80
      },
      { 
        headerName: '订单编号', 
        field: 'docNo', 
        width: 100
      },
      { 
        headerName: '订单日期', 
        field: 'docDate', 
        width: 120
      },
      { 
        headerName: '物料编码', 
        field: 'materialCode', 
        width: 100
      },
      { 
        headerName: '物料描述', 
        field: 'materialDescription', 
        width: 120
      },
      { 
        headerName: '计划数量', 
        field: 'planQty', 
        width: 100
      },
      { 
        headerName: '单位', 
        field: 'unitName', 
        width: 80
      },
      { 
        headerName: '开始日期', 
        field: 'basicDateStart', 
        width: 100
      },
      { 
        headerName: '结束日期', 
        field: 'basicDateEnd', 
        width: 100
      }
      
    ]
  }, [])

  return (
    <Box p={1} h="99%" display="flex" flexDirection="column">
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
                  <Text fontSize="sm" fontWeight="medium">订单编号</Text>
                  <Input
                    size="sm"
                    value={condition.docNo}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, orderNo: e.target.value }))}
                    placeholder="请输入订单编号"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">客户名称</Text>
                  <Input
                    size="sm"
                    value={condition.docDate}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, docDate: e.target.value }))}
                    placeholder="请输入订单日期"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">物料编码</Text>
                  <Input
                    size="sm"
                    value={condition.materialCode}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, materialCode: e.target.value }))}
                    placeholder="请输入物料编码"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">物料描述</Text>
                  <Input
                    size="sm"
                    value={condition.materialDescription}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, materialDescription: e.target.value }))}
                    placeholder="请输入物料编码"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">状态</Text>
                  <Input
                    size="sm"
                    value={condition.status}
                    onChange={(e) => handleConditionChange(prev => ({ ...prev, status: e.target.value }))}
                    placeholder="请输入状态"
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
          minH="0"
          overflow="hidden"
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

export default ProductionOrderList