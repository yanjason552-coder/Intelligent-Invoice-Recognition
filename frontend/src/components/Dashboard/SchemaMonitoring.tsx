import React, { useState, useEffect } from "react"
import { Box, Text, Flex, HStack, VStack, Skeleton, Progress, Badge } from "@chakra-ui/react"
import { FiCheckCircle, FiXCircle, FiClock, FiTrendingUp, FiActivity, FiShield, FiRefreshCw } from "react-icons/fi"
import { getApiUrl, getAuthHeaders } from '../../client/unifiedTypes'

interface SchemaMonitoringData {
  metrics: {
    validation_total: number
    validation_success: number
    validation_success_rate: number
    repair_total: number
    repair_success: number
    repair_success_rate: number
    fallback_total: number
    fallback_by_type: { [key: string]: number }
    fallback_rate: number
    avg_validation_time: number
    avg_repair_time: number
    avg_total_time: number
    last_updated: string | null
  }
  system_stats: {
    active_model_configs: number
    active_schemas: number
    configs_with_default_schema: number
    schema_coverage_rate: number
  }
  query_params: {
    scope: string
    model_config_id: string | null
    schema_id: string | null
    time_range_hours: number
  }
}

const SchemaMonitoring = () => {
  const [data, setData] = useState<SchemaMonitoringData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [timeRange, setTimeRange] = useState(24)

  useEffect(() => {
    loadMonitoringData()
  }, [timeRange])

  const loadMonitoringData = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(getApiUrl(`/config/schema-monitoring/metrics?time_range_hours=${timeRange}`), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('加载监控数据失败')
      }

      const result = await response.json()
      setData(result)
    } catch (error: any) {
      console.error('加载监控数据失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms.toFixed(0)}ms`
    } else {
      return `${(ms / 1000).toFixed(2)}s`
    }
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }

  if (isLoading) {
    return (
      <Box p={4}>
        <Text fontSize="lg" fontWeight="bold" mb={4}>Schema监控指标</Text>
        <Box display="grid" gridTemplateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(4, 1fr)" }} gap={4}>
          {[...Array(8)].map((_, i) => (
            <Box key={i} p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
              <Skeleton height="100px" />
            </Box>
          ))}
        </Box>
      </Box>
    )
  }

  if (!data) {
    return (
      <Box p={4}>
        <Text>暂无监控数据</Text>
      </Box>
    )
  }

  const { metrics, system_stats } = data

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="lg" fontWeight="bold">Schema监控指标</Text>
        <Flex gap={2} align="center">
          <Text fontSize="sm" color="gray.600">时间范围:</Text>
          <Box as="select" 
            size="sm" 
            value={timeRange} 
            onChange={(e) => setTimeRange(Number(e.target.value))} 
            w="120px"
            p={1}
            borderRadius="md"
            border="1px"
            borderColor="gray.300"
            fontSize="sm"
          >
            <option value={1}>1小时</option>
            <option value={6}>6小时</option>
            <option value={24}>24小时</option>
            <option value={168}>7天</option>
          </Box>
          <Box
            as="button"
            onClick={loadMonitoringData}
            p={1}
            borderRadius="md"
            _hover={{ bg: "gray.100" }}
            transition="all 0.2s"
          >
            <FiRefreshCw size={16} />
          </Box>
        </Flex>
      </Flex>

      {/* 系统状态 */}
      <Box display="grid" gridTemplateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(4, 1fr)" }} gap={4} mb={6}>
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">活跃模型配置</Text>
              <Box color="blue.500">
                <FiActivity size={20} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">{system_stats.active_model_configs}</Text>
            <Text fontSize="xs" color="gray.600">
              有默认Schema: {system_stats.configs_with_default_schema}
            </Text>
          </VStack>
        </Box>

        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">活跃Schema</Text>
              <Box color="green.500">
                <FiShield size={20} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">{system_stats.active_schemas}</Text>
            <Text fontSize="xs" color="gray.600">
              Schema覆盖率: {system_stats.schema_coverage_rate.toFixed(1)}%
            </Text>
          </VStack>
        </Box>

        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">验证成功率</Text>
              <Box color={metrics.validation_success_rate >= 0.8 ? "green.500" : metrics.validation_success_rate >= 0.6 ? "yellow.500" : "red.500"}>
                <FiCheckCircle size={20} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">{formatPercentage(metrics.validation_success_rate)}</Text>
            <Text fontSize="xs" color="gray.600">
              {metrics.validation_success}/{metrics.validation_total} 次验证
            </Text>
          </VStack>
        </Box>

        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">修复成功率</Text>
              <Box color={metrics.repair_success_rate >= 0.7 ? "green.500" : metrics.repair_success_rate >= 0.5 ? "yellow.500" : "red.500"}>
                <FiTrendingUp size={20} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">{formatPercentage(metrics.repair_success_rate)}</Text>
            <Text fontSize="xs" color="gray.600">
              {metrics.repair_success}/{metrics.repair_total} 次修复
            </Text>
          </VStack>
        </Box>
      </Box>

      {/* 详细指标 */}
      <Box display="grid" gridTemplateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4} mb={6}>
        {/* 验证性能 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <Text fontSize="lg" fontWeight="bold" mb={4}>验证性能</Text>
          <VStack align="stretch" spacing={3}>
            <Box>
              <Flex justify="space-between" align="center" mb={1}>
                <Text fontSize="sm">验证成功率</Text>
                <Text fontSize="sm" fontWeight="bold">{formatPercentage(metrics.validation_success_rate)}</Text>
              </Flex>
              <Progress.Root value={metrics.validation_success_rate * 100} colorPalette="green" size="sm">
                <Progress.Track>
                  <Progress.Range />
                </Progress.Track>
              </Progress.Root>
            </Box>

            <Box>
              <Flex justify="space-between" align="center" mb={1}>
                <Text fontSize="sm">修复成功率</Text>
                <Text fontSize="sm" fontWeight="bold">{formatPercentage(metrics.repair_success_rate)}</Text>
              </Flex>
              <Progress.Root value={metrics.repair_success_rate * 100} colorPalette="blue" size="sm">
                <Progress.Track>
                  <Progress.Range />
                </Progress.Track>
              </Progress.Root>
            </Box>

            <Box>
              <Flex justify="space-between" align="center" mb={1}>
                <Text fontSize="sm">降级率</Text>
                <Text fontSize="sm" fontWeight="bold">{formatPercentage(metrics.fallback_rate)}</Text>
              </Flex>
              <Progress.Root value={metrics.fallback_rate * 100} colorPalette="orange" size="sm">
                <Progress.Track>
                  <Progress.Range />
                </Progress.Track>
              </Progress.Root>
            </Box>
          </VStack>
        </Box>

        {/* 降级统计 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <Text fontSize="lg" fontWeight="bold" mb={4}>降级统计</Text>
          <VStack align="stretch" spacing={3}>
            {Object.entries(metrics.fallback_by_type).map(([type, count]) => (
              <HStack key={type} justify="space-between">
                <HStack>
                  <Badge
                    colorScheme={
                      type === 'partial' ? 'blue' :
                      type === 'empty' ? 'gray' :
                      type === 'text' ? 'purple' : 'red'
                    }
                    variant="subtle"
                  >
                    {type}
                  </Badge>
                </HStack>
                <Text fontWeight="bold">{count}</Text>
              </HStack>
            ))}
            {Object.keys(metrics.fallback_by_type).length === 0 && (
              <Text fontSize="sm" color="gray.500">暂无降级记录</Text>
            )}
          </VStack>
        </Box>
      </Box>

      {/* 性能指标 */}
      <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
        <Text fontSize="lg" fontWeight="bold" mb={4}>性能指标</Text>
        <Box display="grid" gridTemplateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap={4}>
          <Box textAlign="center">
            <Text fontSize="sm" color="gray.600" mb={1}>平均验证耗时</Text>
            <Text fontSize="xl" fontWeight="bold" color="blue.600">
              {formatTime(metrics.avg_validation_time)}
            </Text>
          </Box>

          <Box textAlign="center">
            <Text fontSize="sm" color="gray.600" mb={1}>平均修复耗时</Text>
            <Text fontSize="xl" fontWeight="bold" color="orange.600">
              {formatTime(metrics.avg_repair_time)}
            </Text>
          </Box>

          <Box textAlign="center">
            <Text fontSize="sm" color="gray.600" mb={1}>平均总耗时</Text>
            <Text fontSize="xl" fontWeight="bold" color="purple.600">
              {formatTime(metrics.avg_total_time)}
            </Text>
          </Box>
        </Box>

        {metrics.last_updated && (
          <Text fontSize="xs" color="gray.500" mt={3} textAlign="center">
            最后更新: {new Date(metrics.last_updated).toLocaleString('zh-CN')}
          </Text>
        )}
      </Box>
    </Box>
  )
}

export default SchemaMonitoring
