import { useState, useMemo, useEffect } from "react"
import { 
  Box, 
  Text, 
  Heading, 
  Flex, 
  Grid, 
  GridItem, 
  Input, 
  HStack, 
  VStack
} from "@chakra-ui/react"
import { Button } from "@/components/ui/button"
import { FiSave, FiPlus, FiTrash2, FiSearch, FiEdit } from "react-icons/fi"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { generateGUID } from "@/utils"
import useCustomToast from "@/hooks/useCustomToast"

// 注册AG-Grid模块 - 包含所有社区功能
ModuleRegistry.registerModules([AllCommunityModule])

// 表头数据接口 - 对应 feature 表
interface Feature {
  featureId: string
  featureCode: string
  featureDesc: string
  dataType: string
  dataLen: number
  dataRanger: string
  dataMin: string
  dataMax: string
  remark: string
  approveStatus: string
  creator: string
  createDate: string
  modifierLast: string
  modifyDateLast: string
  featureDList: FeatureD[]
}

// 明细数据接口 - 对应 feature_d 表
interface FeatureD {
  featureDId: string
  featureId: string
  featureValue: string
  featureValueDesc: string
  remark?: string
  creator: string
  approveDate?: string
}

interface FeatureEditProps {
  featureId?: string
  featureData?: any
}

const FeatureEdit = ({ featureId, featureData: initialFeatureData }: FeatureEditProps) => {
  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  // 表头数据状态
  const [featureData, setFeatureData] = useState<Feature>({
    featureId: "",
    featureCode: "",
    featureDesc: "",
    dataType: "",
    dataLen: 0,
    dataRanger: "",
    dataMin: "",
    dataMax: "",
    remark: "",
    approveStatus: "N",
    creator: "",
    createDate: "",
    modifierLast: "",
    modifyDateLast: "",
    featureDList: []
  })

  // 明细数据状态
  const [detailData, setDetailData] = useState<FeatureD[]>([])
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [gridApi, setGridApi] = useState<any>(null)
  const [pageSize, setPageSize] = useState(20)
  // 数据变更跟踪状态
  const [dataChanges, setDataChanges] = useState({
    headerModified: false,
    newDetails: [] as string[],
    updatedDetails: [] as string[],
    deletedDetails: [] as string[]
  })

  // 数据类型选项
  const dataTypeOptions = [
    { value: "1", label: "字符串" },
    { value: "2", label: "整数" },
    { value: "3", label: "小数" },
    { value: "4", label: "日期" },
    { value: "5", label: "布尔值" }
  ]

  const dataRangerOptions = [
    { value: "1", label: "枚举" },
    { value: "2", label: "区间" },
    { value: "3", label: "任意" }
    
  ]

  // 审批状态选项
  const approveStatusOptions = [
    { value: "N", label: "未批准" },
    { value: "Y", label: "已批准" },
    { value: "U", label: "批准中" },
    { value: "V", label: "失败" }
  ]

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
      resizable: false,
      editable: false
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
      headerName: '属性值', 
      field: 'featureValue', 
      width: 90,
      sortable: true,
      filter: true,
      editable: true,
      cellEditor: 'agTextCellEditor',
      cellEditorParams: {
        maxLength: 20
      },
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    },
    { 
      headerName: '属性值描述', 
      field: 'featureValueDesc', 
      width: 120,
      sortable: true,
      filter: true,
      editable: true,
      cellEditor: 'agTextCellEditor',
      cellEditorParams: {
        maxLength: 20
      },
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
      editable: true,
      cellEditor: 'agTextCellEditor',
      cellEditorParams: {
        maxLength: 200
      },
      filterParams: {
        filterOptions: ['contains', 'equals', 'startsWith', 'endsWith']
      }
    }
  ], [])

  // AG-Grid事件处理
  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api)
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedNodes = gridApi.getSelectedNodes()
      const selectedIds = selectedNodes.map((node: any) => node.data.featureDId)
      setSelectedRows(selectedIds)
    }
  }

  // 单元格编辑完成事件
  const onCellValueChanged = (event: any) => {
    const { data, field, newValue, oldValue } = event
    console.log(`单元格编辑: ${field} 从 "${oldValue}" 改为 "${newValue}"`)
    
    // 更新本地数据状态
    const updatedData = detailData.map(item => {
      if (item.featureDId === data.featureDId) {
        return {
          ...item,
          [field]: newValue
        }
      }
      return item
    })
    
    setDetailData(updatedData)
    
    // 标记为已更新（如果是已存在的记录，不是新增的记录，且ID不为空）
    if (!data.featureDId.startsWith('new-')) {
      showInfoToast("修改")
      setDataChanges(prev => ({
        ...prev,
        updatedDetails: prev.updatedDetails.includes(data.featureDId) 
          ? prev.updatedDetails 
          : [...prev.updatedDetails, data.featureDId]
      }))
    }
  }

  // 加载明细数据
  const loadDetailData = async (featureId: string) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/feature-d/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          action: 'list',
          module: 'feature-d',
          page: 1,
          limit: 100, // 获取较多数据
          filters: {
            featureId: featureId
          },
          timestamp: new Date().toISOString()
        })
      })

      if (!response.ok) {
        console.error('加载明细数据失败:', response.status, response.statusText)
        return
      }

      const result = await response.json()
      
      if (result.success) {
        console.log("明细数据加载成功:", result.data)
        setDetailData(result.data || [])
      } else {
        console.error('加载明细数据失败:', result.message)
      }
    } catch (error) {
      console.error('加载明细数据失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 处理传入的featureData
  useEffect(() => {
    if (initialFeatureData && featureId) {
      console.log("FeatureEdit接收到数据:", { featureId, initialFeatureData })
      
      // 更新表头数据
      setFeatureData({
        featureId: initialFeatureData.featureId || "",
        featureCode: initialFeatureData.featureCode || "",
        featureDesc: initialFeatureData.featureDesc || "",
        dataType: initialFeatureData.dataType || "",
        dataLen: initialFeatureData.dataLen || 0,
        dataRanger: initialFeatureData.dataRanger || "",
        dataMin: initialFeatureData.dataMin || "",
        dataMax: initialFeatureData.dataMax || "",
        remark: initialFeatureData.remark || "",
        approveStatus: initialFeatureData.approveStatus || "N",
        creator: initialFeatureData.creator || "",
        createDate: initialFeatureData.createDate || "",
        modifierLast: initialFeatureData.modifierLast || "",
        modifyDateLast: initialFeatureData.modifyDateLast || "",
        featureDList:[]
      })
      
      // 加载对应的明细数据
      loadDetailData(featureId)
    }
  }, [featureId, initialFeatureData]) // 添加 initialFeatureData 依赖

  // 表头数据变化处理
  const handleHeaderChange = (field: keyof Feature, value: any) => {
    setFeatureData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // 标记表头数据已修改
    setDataChanges(prev => ({
      ...prev,
      headerModified: true
    }))
  }

  // 检查是否有数据变更
  const hasChanges = () => {
    return dataChanges.headerModified || 
           dataChanges.newDetails.length > 0 ||
           dataChanges.updatedDetails.length > 0 ||
           dataChanges.deletedDetails.length > 0
  }

  // 获取变更摘要
  const getChangeSummary = () => {
    const changes = []
    if (dataChanges.headerModified) changes.push("表头已修改")
    if (dataChanges.newDetails.length > 0) changes.push(`新增${dataChanges.newDetails.length}条明细`)
    if (dataChanges.updatedDetails.length > 0) changes.push(`更新${dataChanges.updatedDetails.length}条明细`)
    if (dataChanges.deletedDetails.length > 0) changes.push(`删除${dataChanges.deletedDetails.length}条明细`)
    return changes.join(", ")
  }

  // 保存所有数据（表头和表身）
  const save = async () => {
    if (!hasChanges()) {
     showInfoToast("没有数据变更，无需保存")
      return
    }

    setIsLoading(true)
    try {
     
      
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      // 一次性提交所有数据
      await saveData(token)
      
      console.log("数据保存成功")
      showSuccessToast("数据保存成功")
      
      // 重置变更跟踪状态
      setDataChanges({
        headerModified: false,
        newDetails: [],
        updatedDetails: [],
        deletedDetails: []
      })
      
    } catch (error) {
      console.error('保存数据失败:', error)
      showErrorToast(`保存失败: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 一次性提交所有数据
  const saveData = async (token: string) => {
          // 准备提交数据
    
    // 将表格的业务数据赋值给featureData.featureDList
    featureData.featureDList = detailData
    
    const response = await fetch('/api/v1/feature/unified', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        action: 'submit_all',
        module: 'feature',
        data: featureData,
        timestamp: new Date().toISOString()
      })
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(`提交失败: ${errorData.message || response.statusText}`)
    }

    const result = await response.json()
    if (!result.success) {
      throw new Error(`提交失败: ${result.message}`)
    }

    console.log("一次性提交成功:", result.data)

    // 更新本地数据中的GUID为真实数据库ID
    if (result.data.details && result.data.details.created) {
      const createdIds = result.data.details.created
      const updatedDetailData = detailData.map(item => {
        const newItemIndex = dataChanges.newDetails.findIndex(newItemId => newItemId === item.featureDId)
        if (newItemIndex !== -1 && newItemIndex < createdIds.length) {
          return {
            ...item,
            featureDId: createdIds[newItemIndex] // 使用真实的数据库ID
          }
        }
        return item
      })
      
      setDetailData(updatedDetailData)
    }
  }

    // 注释：这些函数已被 saveData 替代，保留作为参考
  // 更新表头数据
  // const updateFeatureData = async (token: string) => { ... }
  
  // 处理明细数据变更
  // const processDetailDataChanges = async (token: string) => { ... }
  
  // 批量删除明细数据
  // const batchDeleteDetails = async (token: string, featureDIds: string[]) => { ... }
  
  // 批量更新明细数据
  // const batchUpdateDetails = async (token: string, items: FeatureD[]) => { ... }
  
  // 批量创建明细数据
  // const batchCreateDetails = async (token: string, items: FeatureD[]) => { ... }

  // 添加明细行
  const addDetailRow = () => {
    const newDetail: FeatureD = {
      featureDId: `new-${generateGUID()}`, // 使用GUID生成唯一ID
      featureId: featureData.featureId,
      featureValue: "",
      featureValueDesc: "",
      remark: "",
      creator: "admin",
      approveDate: undefined
    }
    setDetailData([...detailData, newDetail])
    
    // 跟踪新增的记录
    setDataChanges(prev => ({
      ...prev,
      newDetails: [...prev.newDetails, newDetail.featureDId]
    }))
    
    // 显示成功提示
    console.log("新增明细行成功，ID:", newDetail.featureDId)
    showSuccessToast(`新增明细行成功，ID: ${newDetail.featureDId}`)
    
    // 滚动到表格底部以显示新行
    setTimeout(() => {
      if (gridApi) {
        gridApi.ensureIndexVisible(detailData.length, 'bottom')
      }
    }, 100)
  }

  // 删除整个Feature（表头和所有明细）
  const handleDeleteFeature = async () => {
    if (!featureId) {
      showErrorToast("没有可删除的数据")
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      // 获取要删除的明细ID（只包含已存在的记录，不包括新增的记录）
      const existingDetailIds = detailData
        .map(item => item.featureDId)
        .filter(id => !id.startsWith('new-'))
      
      console.log(`准备删除物料属性: featureId=${featureId}, 明细数量=${existingDetailIds.length}`)
      console.log(`要删除的明细ID:`, existingDetailIds)

      // 一次性提交删除操作（表头和所有明细）
      const response = await fetch('/api/v1/feature/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          action: 'delete',
          module: 'feature',
          data: featureData,
          timestamp: new Date().toISOString()
        })
      })

      if (!response.ok) {
        throw new Error('删除操作失败')
      }

      const result = await response.json()
      if (!result.success) {
        throw new Error(`删除失败: ${result.message}`)
      }

      showSuccessToast("物料属性删除成功")
      
      // 清空本地数据
      setFeatureData({
        featureId: "",
        featureCode: "",
        featureDesc: "",
        dataType: "",
        dataLen: 0,
        dataRanger: "",
        dataMin: "",
        dataMax: "",
        remark: "",
        approveStatus: "N",
        creator: "",
        createDate: "",
        modifierLast: "",
        modifyDateLast: "",
        featureDList:[]
      })
      setDetailData([])
      setDataChanges({
        headerModified: false,
        newDetails: [],
        updatedDetails: [],
        deletedDetails: []
      })

      // 关闭当前标签页
      window.dispatchEvent(new CustomEvent('closeCurrentTab'))

    } catch (error) {
      console.error('删除物料属性失败:', error)
      showErrorToast(`删除失败: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 删除选中的明细行
  const deleteSelectedRows = () => {
    if (selectedRows.length === 0) {
      console.log("请先选择要删除的行")
      showInfoToast("请先选择要删除的行")
      return
    }
    
    // 区分新增的记录和已存在的记录
    const newIds = selectedRows.filter(id => id.startsWith('new-'))
    const existingIds = selectedRows.filter(id => !id.startsWith('new-'))
    
    console.log(`准备删除 ${selectedRows.length} 行明细数据:`)
    console.log(`- 新增记录: ${newIds.length} 条`)
    console.log(`- 已存在记录: ${existingIds.length} 条`)
    
    // 更新变更跟踪状态
    setDataChanges(prev => ({
      ...prev,
      newDetails: prev.newDetails.filter(id => !newIds.includes(id)),
      deletedDetails: [...prev.deletedDetails, ...existingIds]
    }))
    
    const newDetailData = detailData.filter(item => !selectedRows.includes(item.featureDId))
    setDetailData(newDetailData)
    setSelectedRows([])
    
    console.log(`已删除 ${selectedRows.length} 行明细数据`)
    showSuccessToast(`已删除 ${selectedRows.length} 行明细数据`)
  }

  // 新增物料属性 - 调用接口获取空的Feature对象
  const newOne = async () => {
    try {
      setIsLoading(true)
      
      // 调用 /unified/create 接口获取空的 Feature 对象
      const response = await fetch('/api/v1/feature/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          action: 'create',
          module: 'feature',
          data: {
            create_empty: true
          }
        })
      })

      const result = await response.json()
      
      if (result.success && result.data) {
        // 使用从后端返回的空 Feature 对象
        setFeatureData({
          ...result.data,
          featureDList: []
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
        
        showSuccessToast('成功创建新的 Feature 对象')
      } else {
        showErrorToast(result.message || '创建 Feature 对象失败')
      }
    } catch (error) {
      console.error('创建 Feature 对象失败:', error)
      showErrorToast('创建 Feature 对象失败')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Box p={1} h="100%" display="flex" flexDirection="column">
            {/* 工具栏 */}
      <Flex 
        bg="white" 
        p={1} 
        borderRadius="lg" 
        mt={0}
        mb={1}
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
            console.log("查询物料属性")
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
            // 新增功能 - 调用接口获取空的Feature对象
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
            console.log("修改物料属性")
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
            handleDeleteFeature()
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
              <Text fontSize="sm" fontWeight="medium" minW="80px">属性编码</Text>
                              <Input
                  value={featureData.featureCode}
                  onChange={(e) => handleHeaderChange('featureCode', e.target.value)}
                  placeholder="请输入属性编码"
                  size="sm"
                  flex="1"
                />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">属性描述</Text>
              <Input
                value={featureData.featureDesc}
                onChange={(e) => handleHeaderChange('featureDesc', e.target.value)}
                placeholder="请输入属性描述"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">数据类型</Text>
              <select
                value={featureData.dataType}
                onChange={(e) => handleHeaderChange('dataType', e.target.value)}
                style={{
                  flex: '1',
                  padding: '8px 12px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                <option value="">请选择数据类型</option>
                {dataTypeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">数据长度</Text>
              <Input
                type="number"
                value={featureData.dataLen}
                onChange={(e) => handleHeaderChange('dataLen', parseInt(e.target.value) || 0)}
                placeholder="请输入数据长度"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">数据范围</Text>
              
              <select
                value={featureData.dataRanger}
                onChange={(e) => handleHeaderChange('dataRanger', e.target.value)}
                style={{
                  flex: '1',
                  padding: '8px 12px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                <option value="">请选择数据范围</option>
                {dataRangerOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Flex>
          </GridItem>
          
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">最小值</Text>
              <Input
                value={featureData.dataMin}
                onChange={(e) => handleHeaderChange('dataMin', e.target.value)}
                placeholder="请输入最小值"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">最大值</Text>
              <Input
                value={featureData.dataMax}
                onChange={(e) => handleHeaderChange('dataMax', e.target.value)}
                placeholder="请输入最大值"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          <GridItem colSpan={2}>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">备注</Text>
              <Input
                value={featureData.remark}
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
        p={1} 
        borderRadius="md" 
        mb={1}
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
        flex="0.95"
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
            p={1}
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
          pagination={false}
          paginationPageSize={pageSize}
          suppressRowClickSelection={false}
          animateRows={true}
          editType="fullRow"
          stopEditingWhenCellsLoseFocus={true}
          
        />
      </Box>

    </Box>
  )
}

export default FeatureEdit 