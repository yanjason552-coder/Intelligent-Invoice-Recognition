import React, { useState } from 'react'
import { Box, Button, Input, Text, Flex } from '@chakra-ui/react'

interface QueryDialogProps {
  isOpen: boolean
  onClose: () => void
  onQuery: (queryParams: QueryParams) => void
}

export interface QueryParams {
  customer_full_name?: string
  doc_no?: string
  doc_date?: string
  material_code?: string
  material_description?: string
  material_specification?: string
}

const SalesOrderQueryDialog: React.FC<QueryDialogProps> = ({
  isOpen,
  onClose,
  onQuery
}) => {
  const [queryParams, setQueryParams] = useState<QueryParams>({})

  const handleInputChange = (field: keyof QueryParams, value: string) => {
    setQueryParams(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleQuery = () => {
    // 清理空值
    const cleanedParams: QueryParams = {}
    Object.entries(queryParams).forEach(([key, value]) => {
      if (value && value.trim() !== '') {
        cleanedParams[key as keyof QueryParams] = value.trim()
      }
    })

    onQuery(cleanedParams)
    onClose()
  }

  const handleCancel = () => {
    setQueryParams({})
    onClose()
  }

  const handleReset = () => {
    setQueryParams({})
  }

  if (!isOpen) return null

  return (
    <Box
      position="fixed"
      top={0}
      left={0}
      right={0}
      bottom={0}
      bg="rgba(0, 0, 0, 0.5)"
      zIndex={1000}
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      <Box
        bg="white"
        borderRadius="md"
        p={6}
        w="500px"
        maxW="90vw"
        maxH="90vh"
        overflow="auto"
        boxShadow="lg"
      >
        {/* 标题 */}
        <Text fontSize="lg" fontWeight="bold" mb={4}>
          销售订单查询
        </Text>

        {/* 查询条件 */}
        <Box mb={6}>
          <Box mb={3}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              客户全称
            </Text>
            <Input
              placeholder="请输入客户全称"
              value={queryParams.customer_full_name || ''}
              onChange={(e) => handleInputChange('customer_full_name', e.target.value)}
              size="sm"
            />
          </Box>

          <Box mb={3}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              订单单号
            </Text>
            <Input
              placeholder="请输入订单单号"
              value={queryParams.doc_no || ''}
              onChange={(e) => handleInputChange('doc_no', e.target.value)}
              size="sm"
            />
          </Box>

          <Box mb={3}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              订单日期
            </Text>
            <Input
              type="date"
              value={queryParams.doc_date || ''}
              onChange={(e) => handleInputChange('doc_date', e.target.value)}
              size="sm"
            />
          </Box>

          <Box mb={3}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              物料编码
            </Text>
            <Input
              placeholder="请输入物料编码"
              value={queryParams.material_code || ''}
              onChange={(e) => handleInputChange('material_code', e.target.value)}
              size="sm"
            />
          </Box>

          <Box mb={3}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              物料描述
            </Text>
            <Input
              placeholder="请输入物料描述"
              value={queryParams.material_description || ''}
              onChange={(e) => handleInputChange('material_description', e.target.value)}
              size="sm"
            />
          </Box>

          <Box mb={3}>
            <Text fontSize="sm" fontWeight="medium" mb={1}>
              物料规格
            </Text>
            <Input
              placeholder="请输入物料规格"
              value={queryParams.material_specification || ''}
              onChange={(e) => handleInputChange('material_specification', e.target.value)}
              size="sm"
            />
          </Box>
        </Box>

        {/* 按钮 */}
        <Flex justify="flex-end" gap={3}>
          <Button variant="outline" size="sm" onClick={handleReset}>
            重置
          </Button>
          <Button variant="outline" size="sm" onClick={handleCancel}>
            取消
          </Button>
          <Button colorScheme="blue" size="sm" onClick={handleQuery}>
            查询
          </Button>
        </Flex>
      </Box>
    </Box>
  )
}

export default SalesOrderQueryDialog 