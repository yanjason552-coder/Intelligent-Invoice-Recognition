import React from "react"
import { Box, Text } from "@chakra-ui/react"

interface DataPoint {
  date: string
  value: number
  label?: string
}

interface LineChartProps {
  data: DataPoint[]
  height?: number
  color?: string
  title?: string
}

const LineChart: React.FC<LineChartProps> = ({ 
  data, 
  height = 200, 
  color = "#3B82F6",
  title 
}) => {
  if (!data || data.length === 0) {
    return (
      <Box p={4} textAlign="center" color="gray.500">
        暂无数据
      </Box>
    )
  }

  // 计算最大值和最小值，用于缩放
  const values = data.map(d => d.value)
  const maxValue = Math.max(...values, 1) // 至少为1，避免除零
  const minValue = Math.min(...values, 0)
  const range = maxValue - minValue || 1

  // SVG 尺寸
  const width = 1000
  const padding = { top: 20, right: 40, bottom: 60, left: 60 } // 增加底部padding以显示日期
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  // 计算点的坐标
  const points = data.map((point, index) => {
    const x = padding.left + (index / (data.length - 1 || 1)) * chartWidth
    const y = padding.top + chartHeight - ((point.value - minValue) / range) * chartHeight
    return { x, y, value: point.value, date: point.date }
  })

  // 生成路径
  const pathData = points.map((point, index) => {
    return `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
  }).join(' ')

  // 生成区域路径（用于填充）
  const areaPath = `${pathData} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`

  return (
    <Box>
      {title && (
        <Text fontSize="md" fontWeight="bold" mb={2}>
          {title}
        </Text>
      )}
      <Box overflowX="auto" overflowY="visible">
        <svg width={width} height={height + 30} style={{ minWidth: '100%' }}>
          {/* 网格线 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = padding.top + chartHeight - ratio * chartHeight
            const value = minValue + ratio * range
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#E5E7EB"
                  strokeWidth="1"
                  strokeDasharray="4,4"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  fontSize="12"
                  fill="#6B7280"
                  textAnchor="end"
                >
                  {Math.round(value)}
                </text>
              </g>
            )
          })}

          {/* 填充区域 */}
          <path
            d={areaPath}
            fill={color}
            fillOpacity="0.1"
          />

          {/* 折线 */}
          <path
            d={pathData}
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* 数据点 */}
          {points.map((point, index) => (
            <g key={index}>
              <circle
                cx={point.x}
                cy={point.y}
                r="4"
                fill={color}
                stroke="white"
                strokeWidth="2"
              />
              {/* 悬停提示 */}
              <title>
                {point.date}: {point.value}
              </title>
            </g>
          ))}

          {/* X轴标签 - 显示所有日期 */}
          {points.map((point, index) => {
            // 格式化日期：显示月/日
            const dateParts = point.date.split('-')
            const monthDay = `${dateParts[1]}/${dateParts[2]}`
            
            return (
              <g key={index}>
                {/* X轴刻度线 */}
                <line
                  x1={point.x}
                  y1={padding.top + chartHeight}
                  x2={point.x}
                  y2={padding.top + chartHeight + 5}
                  stroke="#9CA3AF"
                  strokeWidth="1"
                />
                {/* 日期标签 */}
                <text
                  x={point.x}
                  y={height + 25}
                  fontSize="12"
                  fill="#374151"
                  fontWeight="500"
                  textAnchor="middle"
                >
                  {monthDay}
                </text>
              </g>
            )
          })}
        </svg>
      </Box>
    </Box>
  )
}

export default LineChart

