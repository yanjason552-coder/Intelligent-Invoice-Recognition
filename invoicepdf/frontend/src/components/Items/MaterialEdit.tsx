import React, { useState, useMemo, useEffect } from "react"
import { 
  Box, 
  Text, 
  Flex, 
  Grid, 
  GridItem, 
  Input, 
  Button
} from "@chakra-ui/react"
import { FiSave, FiPlus, FiTrash2, FiSearch, FiEdit } from "react-icons/fi"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { generateGUID } from "../../utils"
import useCustomToast from "../../hooks/useCustomToast"
import { getApiUrl, getAuthHeaders, API_CONFIG } from "../../client/unifiedTypes"

// 注册AG-Grid模块
ModuleRegistry.registerModules([AllCommunityModule])

// Material 数据接口
interface Material {
  materialId: string
  materialClassId: string
  materialCode: string
  materialDesc: string
  unitId: string
  secondUnitId: string
  remark: string
  approveStatus: string
  approver: string
  approveDate: string
  creator: string
  createDate: string
  modifierLast: string
  modifyDateLast: string
  materialDList: MaterialD[]
}

// MaterialD 数据接口
interface MaterialD {
  materialDId: string
  materialId: string
  featureCode: string
  featureDesc: string
  featureValue: string
  remark?: string
  creator: string
  approveDate?: string
}

interface MaterialEditProps {
  materialId?: string
  materialData?: any
}

const MaterialEdit = ({ materialId, materialData: initialMaterialData }: MaterialEditProps) => {
  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  // 表头数据状态
  const [materialData, setMaterialData] = useState<Material>({
    materialId: "",
    materialClassId: "",
    materialCode: "",
    materialDesc: "",
    unitId: "",
    secondUnitId: "",
    remark: "",
    approveStatus: "N",
    approver: "",
    approveDate: "",
    creator: "",
    createDate: "",
    modifierLast: "",
    modifyDateLast: "",
    materialDList: []
  })

  // 明细数据状态
  const [detailData, setDetailData] = useState<MaterialD[]>([])
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [gridApi, setGridApi] = useState<any>(null)
  
  // 数据变更跟踪状态
  const [dataChanges, setDataChanges] = useState({
    headerModified: false,
    newDetails: [] as string[],
    updatedDetails: [] as string[],
    deletedDetails: [] as string[]
  })

  // 审批状态选项
  const approveStatusOptions = [
    { value: "N", label: "未审批" },
    { value: "Y", label: "已审批" },
    { value: "U", label: "审批中" },
    { value: "V", label: "审批失败" }
  ]

  // 检查是否有变更
  const hasChanges = () => {
    return dataChanges.headerModified || 
           dataChanges.newDetails.length > 0 || 
           dataChanges.updatedDetails.length > 0 || 
           dataChanges.deletedDetails.length > 0
  }

  // 新增功能 - 创建空的 Material 对象
  const newOne = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      const response = await fetch(getApiUrl('/material/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'create',
          module: 'material',
          data: { create_empty: true },
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success && result.data) {
        // 使用从后端返回的空 Material 对象
        setMaterialData({
          ...result.data,
          materialDList: []
        })
        
        // 清空明细数据
        setDetailData([])
        
        // 重置变更跟踪状态
        setDataChanges({
          headerModified: true, // 标记为已修改，因为这是新增
          newDetails: [],
          updatedDetails: [],
          deletedDetails: []
        })
        
        showSuccessToast('成功创建新的 Material 对象')
      } else {
        showErrorToast(result.message || '创建 Material 对象失败')
      }
    } catch (error) {
      console.error('创建 Material 对象失败:', error)
      showErrorToast('创建 Material 对象失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 删除选中的明细行
  const deleteSelectedRows = () => {
    if (selectedRows.length === 0) {
      showInfoToast("请先选择要删除的行")
      return
    }
    
    const newDetailData = detailData.filter(detail => !selectedRows.includes(detail.materialDId))
    setDetailData(newDetailData)
    
    // 更新变更跟踪
    const deletedIds = selectedRows.filter(id => !id.startsWith('new-'))
    setDataChanges(prev => ({
      ...prev,
      deletedDetails: [...prev.deletedDetails, ...deletedIds]
    }))
    
    setSelectedRows([])
    showSuccessToast("删除成功")
  }

  // 保存数据
  const save = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      // 构建保存数据
      const saveData = {
        ...materialData,
        materialDList: detailData
      }
      
      const response = await fetch(getApiUrl('/material/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'save',
          module: 'material',
          data: saveData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("保存成功")
        // 重置变更跟踪
        setDataChanges({
          headerModified: false,
          newDetails: [],
          updatedDetails: [],
          deletedDetails: []
        })
      } else {
        showErrorToast(result.message || "保存失败")
      }
    } catch (error) {
      console.error('保存失败:', error)
      showErrorToast("保存失败：" + error)
    } finally {
      setIsLoading(false)
    }
  }

  // 删除整个 Material（表头和所有明细）
  const handleDeleteMaterial = async () => {
    if (!materialId) {
      showErrorToast("没有可删除的数据")
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      const response = await fetch(getApiUrl('/material/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'delete',
          module: 'material',
          data: materialData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("删除成功")
        // 清空数据
        setMaterialData({
          materialId: "",
          materialClassId: "",
          materialCode: "",
          materialDesc: "",
          unitId: "",
          secondUnitId: "",
          remark: "",
          approveStatus: "N",
          approver: "",
          approveDate: "",
          creator: "",
          createDate: "",
          modifierLast: "",
          modifyDateLast: "",
          materialDList: []
        })
        setDetailData([])
        setDataChanges({
          headerModified: false,
          newDetails: [],
          updatedDetails: [],
          deletedDetails: []
        })
      } else {
        showErrorToast(result.message || "删除失败")
      }
    } catch (error) {
      console.error('删除失败:', error)
      showErrorToast("删除失败，请重试")
    } finally {
      setIsLoading(false)
    }
  }

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      
      
      // 调用 read 接口获取数据
      if (materialId) {
        try {
          setIsLoading(true)
          
          const response = await fetch(getApiUrl('/material/unified'), {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              action: 'read',
              module: 'material',
              data: {
                materialId: materialId
              }
            })
          })
          
          if (response.ok) {
            const result = await response.json()
            if (result.success && result.data) {
              // 设置表头数据
              setMaterialData(result.data)
              
              // 设置明细数据
              if (result.data.materialDList) {
                setDetailData(result.data.materialDList)
              }
              
              console.log('页面数据初始化成功:', result.data)
              showSuccessToast('页面数据初始化成功')
            } else {
              console.error('初始化数据失败:', result.message)
              showErrorToast(`初始化数据失败: ${result.message}`)
            }
          } else {
            console.error('初始化数据请求失败:', response.status)
            showErrorToast(`初始化数据请求失败: ${response.status}`)
          }
        } catch (error) {
          console.error('初始化数据异常:', error)
          showErrorToast(`初始化数据异常: ${error}`)
        } finally {
          setIsLoading(false)
        }
      }
    }
    
    initializeData()
  }, [materialId, initialMaterialData])

  // 表头数据变更处理
  const handleHeaderChange = (field: keyof Material, value: any) => {
    setMaterialData(prev => ({
      ...prev,
      [field]: value
    }))
    setDataChanges(prev => ({
      ...prev,
      headerModified: true
    }))
  }

  // 明细数据变更处理
  const handleDetailChange = (rowIndex: number, field: keyof MaterialD, value: any) => {
    const newDetailData = [...detailData]
    const detailId = newDetailData[rowIndex].materialDId
    
    newDetailData[rowIndex] = {
      ...newDetailData[rowIndex],
      [field]: value
    }
    
    setDetailData(newDetailData)
    
    // 更新变更跟踪
    if (detailId.startsWith('new-')) {
      if (!dataChanges.newDetails.includes(detailId)) {
        setDataChanges(prev => ({
          ...prev,
          newDetails: [...prev.newDetails, detailId]
        }))
      }
    } else {
      if (!dataChanges.updatedDetails.includes(detailId)) {
        setDataChanges(prev => ({
          ...prev,
          updatedDetails: [...prev.updatedDetails, detailId]
        }))
      }
    }
  }

  // 添加明细行
  const addDetailRow = () => {
    const newDetail: MaterialD = {
      materialDId: `new-${generateGUID()}`, // 使用GUID生成唯一ID
      materialId: materialData.materialId,
      featureCode: "",
      featureDesc: "",
      featureValue: "",
      remark: "",
      creator: "admin",
      approveDate: undefined
    }
    setDetailData([...detailData, newDetail])
    
    // 跟踪新增的记录
    setDataChanges(prev => ({
      ...prev,
      newDetails: [...prev.newDetails, newDetail.materialDId]
    }))
    
    // 显示成功提示
    console.log("新增明细行成功，ID:", newDetail.materialDId)
    showSuccessToast(`新增明细行成功，ID: ${newDetail.materialDId}`)
    
    // 滚动到表格底部以显示新行
    setTimeout(() => {
      if (gridApi) {
        gridApi.ensureIndexVisible(detailData.length, 'bottom')
      }
    }, 100)
  }



  // AG-Grid 列定义
  const columnDefs: ColDef[] = useMemo(() => [
    {
      headerName: '',
      field: 'select',
      width: 60,
      checkboxSelection: true,
      headerCheckboxSelection: true
    },
    {
      headerName: '属性编码',
      field: 'featureCode',
      width: 120,
      editable: true,
      cellEditor: 'agTextCellEditor'
    },
    {
      headerName: '属性描述',
      field: 'featureDesc',
      width: 150,
      editable: true,
      cellEditor: 'agTextCellEditor'
    },
    {
      headerName: '属性值',
      field: 'featureValue',
      width: 120,
      editable: true,
      cellEditor: 'agTextCellEditor'
    },
    {
      headerName: '备注',
      field: 'remark',
      width: 150,
      editable: true,
      cellEditor: 'agTextCellEditor'
    }
  ], [])

  // AG-Grid 事件处理
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api)
    console.log("AG-Grid准备就绪")
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedNodes = gridApi.getSelectedNodes()
      const selectedIds = selectedNodes.map((node: any) => node.data.materialDId)
      setSelectedRows(selectedIds)
    }
  }

  const onCellValueChanged = (params: any) => {
    const rowIndex = params.rowIndex
    const field = params.colDef.field
    const value = params.newValue
    
    handleDetailChange(rowIndex, field, value)
  }

  return (
    <Box p={1} h="100%" display="flex" flexDirection="column">
            {/* 工具栏 */}
      <Flex 
        bg="white" 
        p={2} 
        borderRadius="lg" 
        mt={0}
        mb={2}
        border="1px"
        borderColor="e2e8f0"
        justify="flex-start"
        align="center"
        gap={3}
        boxShadow="0 1px 3px rgba(0,0,0,0.1)"
        flexShrink={0}  // 防止工具栏被压缩
      >
        <Button
          colorScheme="blue"
          variant="outline"
          size="sm"
          onClick={() => {
            // 查询功能
            console.log("查询物料")
          }}
          title="查询"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiSearch />
        </Button>
        <Button
          colorScheme="green"
          variant="outline"
          size="sm"
          onClick={async () => {
            // 新增功能 - 调用接口获取空的Material对象
            await newOne()
          }}
          title="新增"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
          loading={isLoading}
          loadingText="创建中..."
        >
          <FiPlus />
        </Button>
        <Button
          colorScheme="blue"
          variant="outline"
          size="sm"
          onClick={() => {
            // 修改功能
            console.log("修改物料")
          }}
          title="修改"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiEdit />
        </Button>
        <Button
          colorScheme="purple"
          variant="outline"
          size="sm"
          onClick={() => {
            // 保存功能
            save()
          }}
          title="保存"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
          disabled={!hasChanges()}
          opacity={hasChanges() ? 1 : 0.5}
        >
          <FiSave />
        </Button>
        <Button
          colorScheme="red"
          variant="outline"
          size="sm"
          onClick={() => {
            // 删除功能 - 删除数据库中对应的数据并同步更新
            handleDeleteMaterial()
          }}
          title="删除"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiTrash2 />
        </Button>
      </Flex>
       
              {/* 表头部分 */}
        <Box 
          bg="white" 
          p={0} 
          borderRadius="lg" 
          border="1px" 
          borderColor="gray.200"
          mb={1}
          flexShrink={0}
        >
          
          
          <Grid templateColumns="repeat(3, 1fr)" gap={1}>
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">物料编码</Text>
                              <Input
                  value={materialData.materialCode}
                  onChange={(e) => handleHeaderChange('materialCode', e.target.value)}
                  placeholder="请输入物料编码"
                  size="sm"
                  flex="1"
                />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">物料描述</Text>
              <Input
                value={materialData.materialDesc}
                onChange={(e) => handleHeaderChange('materialDesc', e.target.value)}
                placeholder="请输入物料描述"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">物料类别</Text>
              <Input
                value={materialData.materialClassId}
                onChange={(e) => handleHeaderChange('materialClassId', e.target.value)}
                placeholder="请输入物料类别"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">基本单位</Text>
              <Input
                value={materialData.unitId}
                onChange={(e) => handleHeaderChange('unitId', e.target.value)}
                placeholder="请输入基本单位"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">第二单位</Text>
              <Input
                value={materialData.secondUnitId}
                onChange={(e) => handleHeaderChange('secondUnitId', e.target.value)}
                placeholder="请输入第二单位"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
       
          <GridItem >
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">备注</Text>
              <Input
                value={materialData.remark}
                onChange={(e) => handleHeaderChange('remark', e.target.value)}
                placeholder="请输入备注信息"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
        </Grid>     
      </Box>

      {/* 明细数据操作工具栏 */}
      <Flex 
        bg="gray.50" 
        p={1.5} 
        borderRadius="md" 
        mb={2}
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
          {selectedRows.length > 0 && (
            <Flex align="center" gap={1} px={1.5} py={0.5} bg="blue.100" borderRadius="sm">
              <Text fontSize="xs" color="blue.700" fontWeight="medium">
                已选 {selectedRows.length}
              </Text>
            </Flex>
          )}
          {hasChanges() && (
            <Flex align="center" gap={1} px={1.5} py={0.5} bg="orange.100" borderRadius="sm">
              <Text fontSize="xs" color="orange.700" fontWeight="medium">
                有变更
              </Text>
            </Flex>
          )}
        </Flex>
        
        <Flex gap={1.5} align="center">
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
        borderRadius="md"
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
          theme="legacy"
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
          editType="fullRow"
          stopEditingWhenCellsLoseFocus={true}
          // 默认列定义
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true
          }}
        />
      </Box>

    </Box>
  )
}

export default MaterialEdit 