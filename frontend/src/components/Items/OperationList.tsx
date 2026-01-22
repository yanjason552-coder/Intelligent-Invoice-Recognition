import React, { useRef } from "react"
import { Box, Text, Flex, Button, HStack, Input, Grid, GridItem,IconButton} from "@chakra-ui/react"
import { FiSearch,FiPlus, FiTrash2, FiChevronDown, FiChevronUp, FiFilter, FiRefreshCw, FiDownload, FiUpload } from "react-icons/fi"
import { useState, useEffect, useMemo, useCallback } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

// 注册AG-Grid模块 - 包含所有社区功能
ModuleRegistry.registerModules([AllCommunityModule])
import useCustomToast from '../../hooks/useCustomToast'
import { getApiUrl, getAuthHeaders } from '../../client/unifiedTypes'

const OperationList = () => {
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [tableData, setTableData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [totalItems, setTotalItems] = useState(0)

  // 导入导出相关状态
  const [isImporting, setIsImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 查询条件相关状态
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  const [queryConditions, setQueryConditions] = useState({
    operationCode: '',
    operationName: '',
    processingMode: '',
    processingCatego: '',
    approveStatus: ''
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
      const response = await fetch(getApiUrl('/operation/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'operation',
          page: currentPage,
          limit: pageSize,
          filters: {
            operation_code: queryConditions.operationCode || undefined,
            operation_name: queryConditions.operationName || undefined,
            processing_mode: queryConditions.processingMode || undefined,
            processing_catego: queryConditions.processingCatego || undefined,
            approve_status: queryConditions.approveStatus || undefined
          },
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
      operationCode: '',
      operationName: '',
      processingMode: '',
      processingCatego: '',
      approveStatus: ''
    })
  }



  // 导出Excel
  const handleExport = () => {
    if (tableData.length === 0) {
      showInfoToast('没有数据可导出')
      return
    }

    try {
      // 准备导出数据
      const exportData = tableData.map(item => ({
        '工艺ID': item.operationId || '',
        '工艺代码': item.operationCode || '',
        '工艺名称': item.operationName || '',
        '工艺说明': item.operationDesc || '',
        '标准节拍': item.stdTactTime || '',
        '节拍单位': item.unitIdTactTime || '',
        '加工方式': item.processingMode === '0' ? '卷加工' : '板加工',
        '加工类别': item.processingCatego === '0' ? '表面加工' : '剪切加工',
        '损耗数量': item.lossQuantity || '',
        '损耗单位': item.unitIdLoss || '',
        '备注': item.remark || '',
        '批准状态': item.approveStatus || '',
        '创建日期': item.createDate || ''
      }))

      // 创建工作簿
      const wb = XLSX.utils.book_new()
      const ws = XLSX.utils.json_to_sheet(exportData)

      // 设置列宽
      const colWidths = [
        { wch: 12 }, // 工艺ID
        { wch: 15 }, // 工艺代码
        { wch: 20 }, // 工艺名称
        { wch: 25 }, // 工艺说明
        { wch: 12 }, // 标准节拍
        { wch: 12 }, // 节拍单位
        { wch: 12 }, // 加工方式
        { wch: 12 }, // 加工类别
        { wch: 12 }, // 损耗数量
        { wch: 12 }, // 损耗单位
        { wch: 15 }, // 备注
        { wch: 10 }, // 批准状态
        { wch: 15 }  // 创建日期
      ]
      ws['!cols'] = colWidths

      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, '工艺方法明细')

      // 导出文件
      const fileName = `工艺方法明细_${new Date().toISOString().slice(0, 10)}.xlsx`
      XLSX.writeFile(wb, fileName)
      
      showSuccessToast('导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      showErrorToast('导出失败')
    }
  }

  // 保存导入的数据
  const saveImportedData = async (data: any[]) => {
    
  }

  // 导入Excel
  const handleImport = () => {
    fileInputRef.current?.click()
  }

  // 处理文件上传
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 检查文件类型
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      showErrorToast('请选择Excel文件(.xlsx或.xls)')
      return
    }

    setIsImporting(true)
    try {
      const data = await readExcelFile(file)
      console.log('导入的数据:', data)
      
      // 数据验证和转换
      const validatedData = data.map((item, index) => {
        // 验证必需字段
        if (!item['工艺代码'] && !item['工艺ID']) {
          throw new Error(`第${index + 1}行缺少工艺代码或工艺ID`)
        }
        
        // 转换为后端API格式
        return {
          operation_id: item['工艺ID'] || undefined,
          operation_code: item['工艺代码'] || '',
          operation_name: item['工艺名称'] || '',
          operation_desc: item['工艺说明'] || '',
          std_tact_time: item['标准节拍'] || '',
          unit_id_tact_time: item['节拍单位'] || '',
          processing_mode: item['加工方式'] || '0',
          processing_catego: item['加工类别'] || '0',
          loss_quantity: item['损耗数量'] || '',
          unit_id_loss: item['损耗单位'] || '',
          remark: item['备注'] || '',
          approve_status: item['批准状态'] || 'N'
        }
      })
      
      // 批量保存数据
      if (validatedData.length > 0) {
        await saveImportedData(validatedData)
        showSuccessToast(`成功导入 ${validatedData.length} 条数据`)
      }
      
      // 重新加载数据
      await loadOperationData()
    } catch (error) {
      console.error('导入失败:', error)
      showErrorToast(`导入失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsImporting(false)
      // 清空文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // 读取Excel文件
  const readExcelFile = (file: File): Promise<any[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer)
          const workbook = XLSX.read(data, { type: 'array' })
          const sheetName = workbook.SheetNames[0]
          const worksheet = workbook.Sheets[sheetName]
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
          
          // 跳过标题行，处理数据行
          const headers = jsonData[0] as string[]
          const rows = jsonData.slice(1) as any[][]
          
          const processedData = rows.map(row => {
            const item: any = {}
            headers.forEach((header, index) => {
              if (row[index] !== undefined) {
                item[header] = row[index]
              }
            })
            return item
          })
          
          resolve(processedData)
        } catch (error) {
          reject(error)
        }
      }
      reader.onerror = reject
      reader.readAsArrayBuffer(file)
    })
  }

  // 新增处理函数
  const handleAdd = () => {
    console.log("新增工艺方法")
    // 触发自定义事件，通知父组件打开OperationEdit TAB页
    const customEvent = new CustomEvent('openTab', {
      detail: {
        id: 'operation-edit',
        title: '制造工艺-编辑',
        type: '/operation-edit'
      }
    })
    window.dispatchEvent(customEvent)
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
      const deletePromises = selectedRows.map(async (operationId) => {
        const response = await fetch(getApiUrl('/operation/unified'), {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            action: 'delete',
            module: 'operation',
            data: { operationId: operationId },
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
        await loadOperationData()
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
      headerName: '工艺代码', 
      field: 'operationCode',
      width: 120
    },
    { 
      headerName: '工艺名称', 
      field: 'operationName',
      width: 160
    },
    { 
      headerName: '工艺说明', 
      field: 'operationDesc',
      width: 200
    },
    { 
      headerName: '标准节拍', 
      field: 'stdTactTime',
      width: 100
    },
    { 
      headerName: '节拍单位', 
      field: 'unitIdTactTime',
      width: 100
    },
    { 
      headerName: '加工方式', 
      field: 'processingMode',
      width: 100,
      valueFormatter: (params) => {
        return params.value === '0' ? '卷加工' : '板加工'
      }
    },
    { 
      headerName: '加工类别', 
      field: 'processingCatego',
      width: 100,
      valueFormatter: (params) => {
        return params.value === '0' ? '表面加工' : '剪切加工'
      }
    },
    { 
      headerName: '损耗数量', 
      field: 'lossQuantity',
      width: 100
    },
    { 
      headerName: '损耗单位', 
      field: 'unitIdLoss',
      width: 100
    },
    { 
      headerName: '备注', 
      field: 'remark',
      width: 160
    }
  ], [])

  // 加载operation数据
  const loadOperationData = useCallback(async () => {
    setIsLoading(true)
    
    try {
      const response = await fetch(getApiUrl('/operation/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'operation',
          page: currentPage,
          limit: pageSize,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        console.log('加载的数据:', result.data)
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
  }, [currentPage, pageSize, showErrorToast])

  // 初始化数据
  useEffect(() => {
    loadOperationData()
  }, [])

  // AG-Grid事件处理
  const onGridReady = (params: GridReadyEvent) => {
    console.log("AG-Grid准备就绪")
    console.log("表格数据:", params.api.getRenderedNodes().map(node => node.data))
  }

  const onSelectionChanged = (event: any) => {
    const selectedNodes = event.api.getSelectedNodes()
    const selectedIds = selectedNodes.map((node: any) => node.data.operationId)
    console.log('选中的行:', selectedIds)
    setSelectedRows(selectedIds)
  }

  // 行双击事件处理
  const onRowDoubleClicked = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.operationId) {
      console.log("双击行数据:", rowData)
      
      // 触发自定义事件，通知父组件打开OperationEdit TAB页
      const customEvent = new CustomEvent('openOperationEditTab', {
        detail: {
          operationId: rowData.operationId,
          operationData: rowData
        }
      })
      window.dispatchEvent(customEvent)
    }
  }

  // 分页变更事件处理
  const onPaginationChanged = (params:any) => {
    console.log('当前页码:', params.api.paginationGetCurrentPage() + 1);
    console.log('每页行数:', params.api.paginationGetPageSize());
    // TODO: 实现分页变更逻辑
  };

  return (
    <>
      <Box p={0} h="100vh" display="flex" flexDirection="column" overflow="auto" position="relative">
       
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
            <Grid templateColumns="repeat(3, 1fr)" gap={1}>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">工艺代码</Text>
                  <Input
                    size="sm"
                    placeholder="请输入工艺代码"
                    value={queryConditions.operationCode}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('operationCode', e.target.value)}
                    flex="1"
                  />
                </Flex>
              </GridItem>
              
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">工艺名称</Text>
                  <Input
                    size="sm"
                    placeholder="请输入工艺名称"
                    value={queryConditions.operationName}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('operationName', e.target.value)}
                    flex="1"
                  />
                </Flex>
              </GridItem>
              
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">加工方式</Text>
                  <select
                    value={queryConditions.processingMode}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleQueryConditionChange('processingMode', e.target.value)}
                    style={{ 
                      width: '100%', 
                      padding: '6px 12px', 
                      fontSize: '14px', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '6px',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="">全部</option>
                    <option value="0">卷加工</option>
                    <option value="1">板加工</option>
                  </select>
                </Flex>
              </GridItem>
              
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">加工类别</Text>
                  <select
                    value={queryConditions.processingCatego}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleQueryConditionChange('processingCatego', e.target.value)}
                    style={{ 
                      width: '100%', 
                      padding: '6px 12px', 
                      fontSize: '14px', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '6px',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="">全部</option>
                    <option value="0">表面加工</option>
                    <option value="1">剪切加工</option>
                  </select>
                </Flex>
              </GridItem>
            
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium" minW="80px">批准状态</Text>
                  <select
                    value={queryConditions.approveStatus}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleQueryConditionChange('approveStatus', e.target.value)}
                    style={{ 
                      width: '100%', 
                      padding: '6px 12px', 
                      fontSize: '14px', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '6px',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="">全部</option>
                    <option value="N">未审批</option>
                    <option value="Y">已审批</option>
                    <option value="U">审批中</option>
                    <option value="V">审批失败</option>
                  </select>
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
          getRowId={(params) => params.data.operationId}
          suppressCellFocus={true}
          paginationPageSizeSelector={[10, 20, 50]}
          onPaginationChanged={onPaginationChanged}
        />
      </Box>
      
      {/* 隐藏的文件输入元素 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFileUpload}
        style={{ display: 'none' }}
      />
    </Box>
    </>
  )
}

export default OperationList 