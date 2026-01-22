import React, { useState, useEffect } from "react"
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
import useCustomToast from "../../hooks/useCustomToast"
import { getApiUrl, getAuthHeaders } from "../../client/unifiedTypes"

// Operation 数据接口
interface Operation {
  operationId: string
  operationCode: string
  operationName: string
  operationDesc: string
  stdTactTime: number
  unitIdTactTime: string
  processingMode: string
  processingCatego: string
  lossQuantity: number
  unitIdLoss: string
  remark: string
  approveStatus: string
  approver: string
  approveDate: string
  creator: string
  createDate: string
  modifierLast: string
  modifyDateLast: string
}

interface OperationEditProps {
  operationId?: string
  operationData?: any
}

const OperationEdit = ({ operationId, operationData: initialOperationData }: OperationEditProps) => {
  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  // 表头数据状态
  const [operationData, setOperationData] = useState<Operation>({
    operationId: "",
    operationCode: "",
    operationName: "",
    operationDesc: "",
    stdTactTime: 0.0,
    unitIdTactTime: "",
    processingMode: "0",
    processingCatego: "0",
    lossQuantity: 0.0,
    unitIdLoss: "",
    remark: "",
    approveStatus: "N",
    approver: "",
    approveDate: "",
    creator: "",
    createDate: "",
    modifierLast: "",
    modifyDateLast: ""
  })

  const [isLoading, setIsLoading] = useState(false)
  const [dataChanges, setDataChanges] = useState({ headerModified: false })

  // 选项数据
  const approveStatusOptions = [
    { value: "N", label: "未审批" },
    { value: "Y", label: "已审批" },
    { value: "U", label: "审批中" },
    { value: "V", label: "审批失败" }
  ]

  const processingModeOptions = [
    { value: "0", label: "卷加工" },
    { value: "1", label: "板加工" }
  ]

  const processingCategoOptions = [
    { value: "0", label: "表面加工" },
    { value: "1", label: "剪切加工" }
  ]

  const hasChanges = () => dataChanges.headerModified

  // 新增功能
  const newOne = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(getApiUrl('/operation/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'create',
          module: 'operation',
          data: { create_empty: true },
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success && result.data) {
        setOperationData(result.data)
        setDataChanges({ headerModified: true })
        showSuccessToast('成功创建新的 Operation 对象')
      } else {
        showErrorToast(result.message || '创建 Operation 对象失败')
      }
    } catch (error) {
      console.error('创建 Operation 对象失败:', error)
      showErrorToast('创建 Operation 对象失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 保存数据
  const save = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(getApiUrl('/operation/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'save',
          module: 'operation',
          data: operationData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("保存成功")
        setDataChanges({ headerModified: false })
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

  // 删除操作
  const handleDeleteOperation = async () => {
    if (!operationId) {
      showErrorToast("没有可删除的数据")
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(getApiUrl('/operation/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'delete',
          module: 'operation',
          data: operationData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("删除成功")
        setOperationData({
          operationId: "", operationCode: "", operationName: "", operationDesc: "",
          stdTactTime: 0.0, unitIdTactTime: "", processingMode: "0", processingCatego: "0",
          lossQuantity: 0.0, unitIdLoss: "", remark: "", approveStatus: "N",
          approver: "", approveDate: "", creator: "", createDate: "",
          modifierLast: "", modifyDateLast: ""
        })
        setDataChanges({ headerModified: false })
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
      if (operationId) {
        try {
          setIsLoading(true)
          
          const response = await fetch(getApiUrl('/operation/unified'), {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              action: 'read',
              module: 'operation',
              data: { operationId: operationId }
            })
          })
          
          if (response.ok) {
            const result = await response.json()
            if (result.success && result.data) {
              setOperationData(result.data)
              showSuccessToast('页面数据初始化成功')
            } else {
              showErrorToast(`初始化数据失败: ${result.message}`)
            }
          } else {
            showErrorToast(`初始化数据请求失败: ${response.status}`)
          }
        } catch (error) {
          showErrorToast(`初始化数据异常: ${error}`)
        } finally {
          setIsLoading(false)
        }
      }
    }
    
    initializeData()
  }, [operationId, initialOperationData])

  // 表头数据变更处理
  const handleHeaderChange = (field: keyof Operation, value: any) => {
    setOperationData(prev => ({ ...prev, [field]: value }))
    setDataChanges(prev => ({ ...prev, headerModified: true }))
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
        flexShrink={0}
      >
        <Button
          colorScheme="blue"
          variant="outline"
          size="sm"
          onClick={() => console.log("查询工艺方法")}
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
          onClick={newOne}
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
          onClick={() => console.log("修改工艺方法")}
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
          onClick={save}
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
          onClick={handleDeleteOperation}
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
        p={1} 
        borderRadius="lg" 
        border="1px" 
        borderColor="gray.200"
        mb={1}
        flexShrink={0}
      >
        <Grid templateColumns="repeat(3, 1fr)" gap={1}>
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">工艺代码</Text>
              <Input
                value={operationData.operationCode}
                onChange={(e) => handleHeaderChange('operationCode', e.target.value)}
                placeholder="请输入工艺代码"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">工艺名称</Text>
              <Input
                value={operationData.operationName}
                onChange={(e) => handleHeaderChange('operationName', e.target.value)}
                placeholder="请输入工艺名称"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">工艺说明</Text>
              <Input
                value={operationData.operationDesc}
                onChange={(e) => handleHeaderChange('operationDesc', e.target.value)}
                placeholder="请输入工艺说明"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">标准节拍</Text>
              <Input
                type="number"
                step="0.1"
                value={operationData.stdTactTime}
                onChange={(e) => handleHeaderChange('stdTactTime', parseFloat(e.target.value) || 0)}
                placeholder="请输入标准节拍"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">节拍单位</Text>
              <Input
                value={operationData.unitIdTactTime}
                onChange={(e) => handleHeaderChange('unitIdTactTime', e.target.value)}
                placeholder="请输入节拍单位"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">加工方式</Text>
              <select
                value={operationData.processingMode}
                onChange={(e) => handleHeaderChange('processingMode', e.target.value)}
                style={{ 
                  width: '100%', 
                  padding: '6px 12px', 
                  fontSize: '14px', 
                  border: '1px solid #e2e8f0', 
                  borderRadius: '6px',
                  backgroundColor: 'white'
                }}
              >
                {processingModeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">加工类别</Text>
              <select
                value={operationData.processingCatego}
                onChange={(e) => handleHeaderChange('processingCatego', e.target.value)}
                style={{ 
                  width: '100%', 
                  padding: '6px 12px', 
                  fontSize: '14px', 
                  border: '1px solid #e2e8f0', 
                  borderRadius: '6px',
                  backgroundColor: 'white'
                }}
              >
                {processingCategoOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">损耗数量</Text>
              <Input
                type="number"
                step="0.1"
                value={operationData.lossQuantity}
                onChange={(e) => handleHeaderChange('lossQuantity', parseFloat(e.target.value) || 0)}
                placeholder="请输入损耗数量"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">损耗单位</Text>
              <Input
                value={operationData.unitIdLoss}
                onChange={(e) => handleHeaderChange('unitIdLoss', e.target.value)}
                placeholder="请输入损耗单位"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">备注</Text>
              <Input
                value={operationData.remark}
                onChange={(e) => handleHeaderChange('remark', e.target.value)}
                placeholder="请输入备注信息"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          
        </Grid>
      </Box>

      {/* 状态信息显示 */}
      <Box 
        bg="gray.50" 
        p={2} 
        borderRadius="md" 
        mb={2}
        border="1px"
        borderColor="gray.200"
        flexShrink={0}
      >
        <Flex justify="space-between" align="center">
          
          {hasChanges() && (
            <Flex align="center" gap={1} px={2} py={1} bg="orange.100" borderRadius="sm">
              <Text fontSize="xs" color="orange.700" fontWeight="medium">
                有变更
              </Text>
            </Flex>
          )}
        </Flex>
      </Box>

      {/* 占位区域 */}
      <Box flex="1" bg="gray.50" borderRadius="md" p={4}>
        <Text color="gray.500" textAlign="center">
          工艺方法编辑区域
        </Text>
      </Box>
    </Box>
  )
}

export default OperationEdit 