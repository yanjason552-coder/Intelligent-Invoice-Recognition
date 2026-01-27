import { Box, Text, VStack, HStack, Badge, Table, Thead, Tbody, Tr, Th, Td, Accordion, AccordionItem, AccordionButton, AccordionPanel, AccordionIcon, Button, Code } from "@chakra-ui/react"
import { FiAlertCircle, FiCheckCircle, FiXCircle, FiInfo, FiRefreshCw } from "react-icons/fi"
import { useState, useEffect } from "react"
import axios from 'axios'
import useCustomToast from '@/hooks/useCustomToast'

interface MismatchItem {
  field_path: string
  mismatch_type: string
  severity: string
  expected: any
  actual: any
  message: string
  can_auto_repair: boolean
  repair_suggestion?: string
}

interface SchemaMismatchDetail {
  has_mismatch: boolean
  mismatch_items: MismatchItem[]
  validation_result?: {
    is_valid: boolean
    errors: any[]
    warnings: any[]
  }
  repair_result?: {
    success: boolean
    repair_actions: any[]
  }
  fallback_result?: {
    fallback_type: string
    fallback_data: any
  }
  requires_manual_review: boolean
  total_errors: number
  total_warnings: number
  critical_count: number
  high_count: number
  medium_count: number
  schema_id?: string
  processing_time_ms: number
}

interface SchemaMismatchDetailProps {
  invoiceId: string
  taskId?: string
}

const SchemaMismatchDetail = ({ invoiceId, taskId }: SchemaMismatchDetailProps) => {
  const [mismatchDetail, setMismatchDetail] = useState<SchemaMismatchDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const loadMismatchDetail = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`/api/v1/invoices/${invoiceId}/schema-validation`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        params: taskId ? { task_id: taskId } : {}
      })

      if (response.data) {
        // 解析验证记录中的不匹配信息
        const record = response.data
        const mismatchItems: MismatchItem[] = []
        
        if (record.validation_errors?.mismatch_items) {
          mismatchItems.push(...record.validation_errors.mismatch_items)
        }

        setMismatchDetail({
          has_mismatch: !record.is_valid,
          mismatch_items: mismatchItems,
          validation_result: {
            is_valid: record.is_valid,
            errors: record.validation_errors?.mismatch_items || [],
            warnings: record.validation_warnings || []
          },
          repair_result: record.repair_attempted ? {
            success: record.repair_success,
            repair_actions: record.repair_actions || []
          } : undefined,
          fallback_result: record.fallback_type ? {
            fallback_type: record.fallback_type,
            fallback_data: record.fallback_data
          } : undefined,
          requires_manual_review: record.error_count > 0 && record.repair_success === false,
          total_errors: record.error_count || 0,
          total_warnings: record.warning_count || 0,
          critical_count: mismatchItems.filter(m => m.severity === 'critical').length,
          high_count: mismatchItems.filter(m => m.severity === 'high').length,
          medium_count: mismatchItems.filter(m => m.severity === 'medium').length,
          schema_id: record.schema_id,
          processing_time_ms: record.validation_time_ms || 0
        })
      }
    } catch (error: any) {
      console.error('加载不匹配详情失败:', error)
      if (error.response?.status !== 404) {
        showErrorToast(error.response?.data?.detail || '加载不匹配详情失败')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (invoiceId) {
      loadMismatchDetail()
    }
  }, [invoiceId, taskId])

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red'
      case 'high': return 'orange'
      case 'medium': return 'yellow'
      case 'low': return 'blue'
      default: return 'gray'
    }
  }

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'critical': return '严重'
      case 'high': return '高'
      case 'medium': return '中'
      case 'low': return '低'
      default: return '信息'
    }
  }

  const getMismatchTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'missing_required_field': '缺失必填字段',
      'type_mismatch': '类型不匹配',
      'extra_field': '额外字段',
      'value_validation_failed': '值验证失败',
      'schema_version_mismatch': 'Schema 版本不匹配',
      'structure_mismatch': '结构不匹配'
    }
    return labels[type] || type
  }

  if (loading) {
    return (
      <Box p={4} textAlign="center">
        <Text>加载中...</Text>
      </Box>
    )
  }

  if (!mismatchDetail || !mismatchDetail.has_mismatch) {
    return (
      <Box p={4} bg="green.50" borderRadius="md" border="1px" borderColor="green.200">
        <HStack spacing={2}>
          <FiCheckCircle color="#48BB78" />
          <Text color="green.700">Schema 验证通过，无数据不匹配</Text>
        </HStack>
      </Box>
    )
  }

  return (
    <Box p={4}>
      <VStack spacing={4} align="stretch">
        {/* 概览卡片 */}
        <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
          <HStack justify="space-between" mb={4}>
            <Text fontSize="lg" fontWeight="bold">Schema 不匹配概览</Text>
            <Button
              size="sm"
              leftIcon={<FiRefreshCw />}
              onClick={loadMismatchDetail}
              variant="outline"
            >
              刷新
            </Button>
          </HStack>
          
          <HStack spacing={4} flexWrap="wrap">
            <Box>
              <Text fontSize="sm" color="gray.600">总错误数</Text>
              <Text fontSize="xl" fontWeight="bold" color="red.600">
                {mismatchDetail.total_errors}
              </Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="gray.600">警告数</Text>
              <Text fontSize="xl" fontWeight="bold" color="orange.600">
                {mismatchDetail.total_warnings}
              </Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="gray.600">严重错误</Text>
              <Text fontSize="xl" fontWeight="bold" color="red.700">
                {mismatchDetail.critical_count}
              </Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="gray.600">高级错误</Text>
              <Text fontSize="xl" fontWeight="bold" color="orange.700">
                {mismatchDetail.high_count}
              </Text>
            </Box>
            <Box>
              <Text fontSize="sm" color="gray.600">处理耗时</Text>
              <Text fontSize="xl" fontWeight="bold">
                {mismatchDetail.processing_time_ms.toFixed(2)}ms
              </Text>
            </Box>
          </HStack>

          {mismatchDetail.requires_manual_review && (
            <Box mt={4} p={3} bg="red.50" borderRadius="md" border="1px" borderColor="red.200">
              <HStack spacing={2}>
                <FiAlertCircle color="#E53E3E" />
                <Text color="red.700" fontWeight="medium">
                  需要人工审核：存在严重错误或自动修复失败
                </Text>
              </HStack>
            </Box>
          )}
        </Box>

        {/* 不匹配项列表 */}
        {mismatchDetail.mismatch_items.length > 0 && (
          <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
            <Text fontSize="lg" fontWeight="bold" mb={4}>不匹配项详情</Text>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>字段路径</Th>
                  <Th>类型</Th>
                  <Th>严重程度</Th>
                  <Th>可自动修复</Th>
                  <Th>错误信息</Th>
                  <Th>修复建议</Th>
                </Tr>
              </Thead>
              <Tbody>
                {mismatchDetail.mismatch_items.map((item, index) => (
                  <Tr key={index}>
                    <Td>
                      <Code fontSize="xs">{item.field_path}</Code>
                    </Td>
                    <Td>
                      <Badge colorScheme="purple">
                        {getMismatchTypeLabel(item.mismatch_type)}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge colorScheme={getSeverityColor(item.severity)}>
                        {getSeverityLabel(item.severity)}
                      </Badge>
                    </Td>
                    <Td>
                      {item.can_auto_repair ? (
                        <Badge colorScheme="green">是</Badge>
                      ) : (
                        <Badge colorScheme="red">否</Badge>
                      )}
                    </Td>
                    <Td>
                      <Text fontSize="sm" color="gray.700">
                        {item.message}
                      </Text>
                      {item.expected && (
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          期望: <Code fontSize="xs">{JSON.stringify(item.expected)}</Code>
                        </Text>
                      )}
                      {item.actual !== undefined && (
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          实际: <Code fontSize="xs">{JSON.stringify(item.actual)}</Code>
                        </Text>
                      )}
                    </Td>
                    <Td>
                      {item.repair_suggestion ? (
                        <Text fontSize="sm" color="blue.600">
                          {item.repair_suggestion}
                        </Text>
                      ) : (
                        <Text fontSize="sm" color="gray.400">-</Text>
                      )}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        )}

        {/* 修复结果 */}
        {mismatchDetail.repair_result && (
          <Accordion allowToggle>
            <AccordionItem>
              <AccordionButton>
                <Box flex="1" textAlign="left">
                  <HStack spacing={2}>
                    {mismatchDetail.repair_result.success ? (
                      <FiCheckCircle color="#48BB78" />
                    ) : (
                      <FiXCircle color="#E53E3E" />
                    )}
                    <Text fontWeight="medium">
                      自动修复结果: {mismatchDetail.repair_result.success ? '成功' : '失败'}
                    </Text>
                  </HStack>
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel pb={4}>
                {mismatchDetail.repair_result.repair_actions.length > 0 ? (
                  <VStack spacing={2} align="stretch">
                    {mismatchDetail.repair_result.repair_actions.map((action: any, index: number) => (
                      <Box key={index} p={2} bg="gray.50" borderRadius="md">
                        <Text fontSize="sm">
                          <Badge colorScheme="blue" mr={2}>{action.action}</Badge>
                          {action.field && `字段: ${action.field}`}
                          {action.value !== undefined && ` → ${JSON.stringify(action.value)}`}
                        </Text>
                      </Box>
                    ))}
                  </VStack>
                ) : (
                  <Text fontSize="sm" color="gray.500">无修复动作</Text>
                )}
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
        )}

        {/* 降级结果 */}
        {mismatchDetail.fallback_result && (
          <Box bg="yellow.50" p={4} borderRadius="md" border="1px" borderColor="yellow.200">
            <HStack spacing={2} mb={2}>
              <FiInfo color="#D69E2E" />
              <Text fontWeight="medium" color="yellow.800">
                降级策略: {mismatchDetail.fallback_result.fallback_type}
              </Text>
            </HStack>
            <Text fontSize="sm" color="yellow.700">
              由于自动修复失败，系统使用了降级策略返回数据
            </Text>
          </Box>
        )}
      </VStack>
    </Box>
  )
}

export default SchemaMismatchDetail

