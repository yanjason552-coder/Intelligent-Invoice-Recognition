import React, { useState, useEffect } from "react"
import { Box, Text, Flex, Grid, GridItem, HStack, VStack, Skeleton } from "@chakra-ui/react"
import { FiFileText, FiActivity, FiCheckCircle, FiXCircle, FiClock, FiTrendingUp, FiDollarSign, FiLayers } from "react-icons/fi"
import { getApiUrl, getAuthHeaders } from '../../client/unifiedTypes'
import LineChart from './LineChart'

interface StatisticsData {
  overview: {
    total_invoices: number
    today_invoices: number
    total_tasks: number
    today_tasks: number
    total_templates: number
    active_templates: number
    total_amount: number
    today_amount: number
  }
  task_status: {
    pending: number
    processing: number
    completed: number
    failed: number
  }
  review_status: {
    pending: number
    approved: number
    rejected: number
  }
  daily_stats: Array<{
    date: string
    invoices: number
    amount: number
  }>
}

const Statistics = () => {
  const [data, setData] = useState<StatisticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadStatistics()
  }, [])

  const loadStatistics = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(getApiUrl('/statistics/overview'), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('加载统计数据失败')
      }

      const result = await response.json()
      setData(result)
    } catch (error: any) {
      console.error('加载统计数据失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatAmount = (amount: number) => {
    if (amount >= 100000000) {
      return `${(amount / 100000000).toFixed(2)}亿`
    } else if (amount >= 10000) {
      return `${(amount / 10000).toFixed(2)}万`
    } else {
      return amount.toFixed(2)
    }
  }

  if (isLoading) {
    return (
      <Box p={4}>
        <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(4, 1fr)" }} gap={4}>
          {[...Array(8)].map((_, i) => (
            <Box key={i} p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
              <Skeleton height="100px" />
            </Box>
          ))}
        </Grid>
      </Box>
    )
  }

  if (!data) {
    return (
      <Box p={4}>
        <Text>暂无统计数据</Text>
      </Box>
    )
  }

  return (
    <Box p={4} h="100%" overflowY="auto">
      <Text fontSize="2xl" fontWeight="bold" mb={4}>
        数据统计
      </Text>

      {/* 概览统计卡片 */}
      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(4, 1fr)" }} gap={4} mb={6}>
        {/* 发票总数 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">发票总数</Text>
              <Box color="blue.500">
                <FiFileText size={24} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">{data.overview.total_invoices}</Text>
            <Text fontSize="xs" color="green.600">
              今日新增: {data.overview.today_invoices}
            </Text>
          </VStack>
        </Box>

        {/* 识别任务 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">识别任务</Text>
              <Box color="purple.500">
                <FiActivity size={24} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">{data.overview.total_tasks}</Text>
            <Text fontSize="xs" color="green.600">
              今日新增: {data.overview.today_tasks}
            </Text>
          </VStack>
        </Box>

        {/* 发票总金额 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">发票总金额</Text>
              <Box color="green.500">
                <FiDollarSign size={24} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">¥{formatAmount(data.overview.total_amount)}</Text>
            <Text fontSize="xs" color="green.600">
              今日: ¥{formatAmount(data.overview.today_amount)}
            </Text>
          </VStack>
        </Box>

        {/* 模板数量 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <VStack align="start" spacing={2}>
            <HStack justify="space-between" w="100%">
              <Text fontSize="sm" color="gray.600">模板数量</Text>
              <Box color="orange.500">
                <FiLayers size={24} />
              </Box>
            </HStack>
            <Text fontSize="2xl" fontWeight="bold">{data.overview.total_templates}</Text>
            <Text fontSize="xs" color="gray.600">
              活跃: {data.overview.active_templates}
            </Text>
          </VStack>
        </Box>
      </Grid>

      {/* 状态统计 */}
      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4} mb={6}>
        {/* 识别任务状态 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <Text fontSize="lg" fontWeight="bold" mb={4}>识别任务状态</Text>
          <VStack align="stretch" spacing={3}>
            <HStack justify="space-between">
              <HStack>
                <FiClock color="#F59E0B" />
                <Text>待处理</Text>
              </HStack>
              <Text fontWeight="bold">{data.task_status.pending}</Text>
            </HStack>
            <HStack justify="space-between">
              <HStack>
                <FiActivity color="#3B82F6" />
                <Text>处理中</Text>
              </HStack>
              <Text fontWeight="bold">{data.task_status.processing}</Text>
            </HStack>
            <HStack justify="space-between">
              <HStack>
                <FiCheckCircle color="#10B981" />
                <Text>已完成</Text>
              </HStack>
              <Text fontWeight="bold">{data.task_status.completed}</Text>
            </HStack>
            <HStack justify="space-between">
              <HStack>
                <FiXCircle color="#EF4444" />
                <Text>失败</Text>
              </HStack>
              <Text fontWeight="bold">{data.task_status.failed}</Text>
            </HStack>
          </VStack>
        </Box>

        {/* 审核状态 */}
        <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm">
          <Text fontSize="lg" fontWeight="bold" mb={4}>审核状态</Text>
          <VStack align="stretch" spacing={3}>
            <HStack 
              justify="space-between" 
              cursor="pointer"
              onClick={() => {
                // 触发打开待审核页面的自定义事件
                const event = new CustomEvent('openTab', {
                  detail: { type: 'invoice-review-pending' }
                })
                window.dispatchEvent(event)
              }}
              _hover={{ bg: "gray.50", borderRadius: "md", p: 1 }}
              transition="all 0.2s"
            >
              <HStack>
                <FiClock color="#F59E0B" />
                <Text>待审核</Text>
              </HStack>
              <Text fontWeight="bold">{data.review_status.pending}</Text>
            </HStack>
            <HStack justify="space-between">
              <HStack>
                <FiCheckCircle color="#10B981" />
                <Text>已通过</Text>
              </HStack>
              <Text fontWeight="bold">{data.review_status.approved}</Text>
            </HStack>
            <HStack justify="space-between">
              <HStack>
                <FiXCircle color="#EF4444" />
                <Text>已拒绝</Text>
              </HStack>
              <Text fontWeight="bold">{data.review_status.rejected}</Text>
            </HStack>
          </VStack>
        </Box>
      </Grid>

      {/* 最近7天趋势 - 卡片视图 */}
      <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm" mb={4}>
        <Text fontSize="lg" fontWeight="bold" mb={4}>最近7天趋势</Text>
        <Grid templateColumns={{ base: "1fr", md: "repeat(7, 1fr)" }} gap={2}>
          {data.daily_stats.map((stat, index) => (
            <Box key={index} p={3} bg="gray.50" borderRadius="md">
              <VStack align="stretch" spacing={1}>
                <Text fontSize="xs" color="gray.600">{stat.date}</Text>
                <Text fontSize="sm" fontWeight="bold">{stat.invoices} 张</Text>
                <Text fontSize="xs" color="green.600">¥{formatAmount(stat.amount)}</Text>
              </VStack>
            </Box>
          ))}
        </Grid>
      </Box>

      {/* 最近发票趋势 - 折线图 */}
      <Box p={4} bg="white" borderRadius="md" border="1px" borderColor="gray.200" shadow="sm" mb={6}>
        <Text fontSize="lg" fontWeight="bold" mb={4}>最近发票趋势</Text>
        <LineChart
          data={data.daily_stats.map(stat => ({
            date: stat.date,
            value: stat.invoices,
            label: `${stat.invoices} 张`
          }))}
          height={280}
          color="#3B82F6"
          title=""
        />
      </Box>
    </Box>
  )
}

export default Statistics

