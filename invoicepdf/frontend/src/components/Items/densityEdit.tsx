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

import useCustomToast from "../../hooks/useCustomToast"
import { getApiUrl, getAuthHeaders, API_CONFIG } from "../../client/unifiedTypes"



// MaterialDensity 数据接口
interface MaterialDensity {
  materialDensityId: string
  materialCode: string
  materialDesc: string
  density: number
  densityUnitId: string
  remark: string
  approveStatus: string
  approver: string
  approveDate: string
  creator: string
  createDate: string
  modifierLast: string
  modifyDateLast: string
}

interface DensityEditProps {
  materialDensityId?: string
  densityData?: any
}

const DensityEdit = ({ materialDensityId, densityData: initialDensityData }: DensityEditProps) => {
  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()
  
  // 密度数据状态
  const [densityData, setDensityData] = useState<MaterialDensity>({
    materialDensityId: "",
    materialCode: "",
    materialDesc: "",
    density: 0,
    densityUnitId: "",
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
  
  // 数据变更跟踪状态
  const [dataChanges, setDataChanges] = useState({
    headerModified: false
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
    return dataChanges.headerModified
  }

  // 新增功能 - 创建空的 MaterialDensity 对象
  const newOne = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      const response = await fetch(getApiUrl('/material-density/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'create',
          module: 'material-density',
          data: { create_empty: true },
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success && result.data) {
        // 使用从后端返回的空 MaterialDensity 对象
        setDensityData({
          ...result.data
        })
        
        // 重置变更跟踪状态
        setDataChanges({
          headerModified: true // 标记为已修改，因为这是新增
        })
        
        showSuccessToast('成功创建新的 MaterialDensity 对象')
      } else {
        showErrorToast(result.message || '创建 MaterialDensity 对象失败')
      }
    } catch (error) {
      console.error('创建 MaterialDensity 对象失败:', error)
      showErrorToast('创建 MaterialDensity 对象失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 删除功能 - 删除整个密度记录
  const deleteDensity = async () => {
    if (!materialDensityId) {
      showErrorToast("没有可删除的数据")
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      const response = await fetch(getApiUrl('/material-density/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'delete',
          module: 'material-density',
          data: densityData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("删除成功")
        // 清空数据
        setDensityData({
          materialDensityId: "",
          materialCode: "",
          materialDesc: "",
          density: 0,
          densityUnitId: "",
          remark: "",
          approveStatus: "N",
          approver: "",
          approveDate: "",
          creator: "",
          createDate: "",
          modifierLast: "",
          modifyDateLast: ""
        })
        setDataChanges({
          headerModified: false
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
        ...densityData
      }
      
      const response = await fetch(getApiUrl('/material-density/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'save',
          module: 'material-density',
          data: saveData,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        showSuccessToast("保存成功")
        // 重置变更跟踪
        setDataChanges({
          headerModified: false
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



  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      // 调用 read 接口获取数据
      if (materialDensityId) {
        try {
          setIsLoading(true)
          
          const response = await fetch(getApiUrl('/material-density/unified'), {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              action: 'read',
              module: 'material-density',
              data: {
                materialDensityId: materialDensityId
              }
            })
          })
          
          if (response.ok) {
            const result = await response.json()
            if (result.success && result.data) {
              // 设置密度数据
              setDensityData(result.data)
              
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
  }, [materialDensityId, initialDensityData])

  // 密度数据变更处理
  const handleDensityChange = (field: keyof MaterialDensity, value: any) => {
    setDensityData(prev => ({
      ...prev,
      [field]: value
    }))
    setDataChanges(prev => ({
      ...prev,
      headerModified: true
    }))
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
          colorScheme="green"
          variant="outline"
          size="sm"
          onClick={async () => {
            // 新增功能 - 调用接口获取空的MaterialDensity对象
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
            deleteDensity()
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
                value={densityData.materialCode}
                onChange={(e) => handleDensityChange('materialCode', e.target.value)}
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
                value={densityData.materialDesc}
                onChange={(e) => handleDensityChange('materialDesc', e.target.value)}
                placeholder="请输入物料描述"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">密度值</Text>
              <Input
                type="number"
                step="0.01"
                value={densityData.density}
                onChange={(e) => handleDensityChange('density', parseFloat(e.target.value) || 0)}
                placeholder="请输入密度值"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">密度单位</Text>
              <Input
                value={densityData.densityUnitId}
                onChange={(e) => handleDensityChange('densityUnitId', e.target.value)}
                placeholder="请输入密度单位"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
          
          <GridItem colSpan={2}>
            <Flex align="center" gap={2}>
              <Text fontSize="sm" fontWeight="medium" minW="80px">备注</Text>
              <Input
                value={densityData.remark}
                onChange={(e) => handleDensityChange('remark', e.target.value)}
                placeholder="请输入备注信息"
                size="sm"
                flex="1"
              />
            </Flex>
          </GridItem>
        </Grid>     
      </Box>

            {/* 状态显示 */}
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
        </Flex>
      </Flex>

    </Box>
  )
}

export default DensityEdit 