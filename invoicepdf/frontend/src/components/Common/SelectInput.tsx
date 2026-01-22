import React, { useState, useEffect } from 'react'
import { Box, Input, Button, Text, Flex, useDisclosure } from '@chakra-ui/react'
import { FiSearch, FiX } from 'react-icons/fi'

// 通用选择输入框组件接口
interface SelectInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  label?: string
  buttonText?: string
  buttonIcon?: React.ReactElement
  buttonSize?: 'xs' | 'sm' | 'md' | 'lg'
  inputSize?: 'xs' | 'sm' | 'md' | 'lg'
  isDisabled?: boolean
  width?: string | number
  height?: string | number
  // 选择窗体相关属性
  modalTitle?: string
  searchPlaceholder?: string
  // 表格列配置 - 完全由宿主页面指定
  columns: Array<{
    header: string                    // 列标题
    field: string                     // 数据字段名
    width?: number | string           // 列宽度
    minWidth?: number | string        // 最小宽度
    maxWidth?: number | string        // 最大宽度
    flex?: number                     // 弹性宽度比例
    render?: (value: any, row: any) => React.ReactNode  // 自定义渲染函数
    sortable?: boolean                // 是否可排序
    filterable?: boolean              // 是否可过滤
    align?: 'left' | 'center' | 'right'  // 对齐方式
    className?: string                // 自定义CSS类
  }>
  // 返回值配置 - 允许父页面指定
  valueField?: string                 // 返回值的字段名，默认 'id'
  displayField?: string               // 显示值的字段名，默认 'displayName'
  returnFormat?: 'field' | 'object'  // 返回格式：'field' 只返回字段值，'object' 返回整行数据
  // API相关属性
  apiUrl?: string
  apiMethod?: 'GET' | 'POST'
  apiParams?: any
  // 数据相关属性（当不使用API时）
  data?: any[]
  onSearch?: (searchTerm: string) => void
  loading?: boolean
  emptyMessage?: string
}

const SelectInput: React.FC<SelectInputProps> = ({
  value,
  onChange,
  placeholder = "请选择",
  label,
  buttonText = "选择",
  buttonIcon = <FiSearch />,
  buttonSize = "sm",
  inputSize = "sm",
  isDisabled = false,
  width = "100%",
  height = "auto",
  modalTitle = "选择数据",
  searchPlaceholder = "请输入搜索关键词",
  columns,
  // 返回值配置 - 允许父页面指定
  valueField = 'id',
  displayField = 'displayName',
  returnFormat = 'field',
  // API相关属性
  apiUrl,
  apiMethod = 'GET',
  apiParams = {},
  // 数据相关属性（当不使用API时）
  data = [],
  onSearch,
  loading = false,
  emptyMessage = "暂无数据"
}) => {
  const { open: isOpen, onOpen, onClose } = useDisclosure()
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredData, setFilteredData] = useState<any[]>([])
  const [apiData, setApiData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // 拖动相关状态
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 })

  // 处理拖动开始
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) { // 只在标题栏区域拖动
      setIsDragging(true)
      const rect = e.currentTarget.getBoundingClientRect()
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      })
    }
  }

  // 处理拖动移动
  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      const newX = e.clientX - dragOffset.x
      const newY = e.clientY - dragOffset.y
      
      // 限制窗体不超出屏幕边界
      const maxX = window.innerWidth - 600 // 窗体宽度
      const maxY = window.innerHeight - 400 // 窗体高度
      
      const clampedX = Math.max(0, Math.min(newX, maxX))
      const clampedY = Math.max(0, Math.min(newY, maxY))
      
      setModalPosition({
        x: clampedX,
        y: clampedY
      })
      
      // 调试信息
      console.log('拖动中 - 新位置:', { x: clampedX, y: clampedY })
    }
  }

  // 处理拖动结束
  const handleMouseUp = () => {
    setIsDragging(false)
    // 拖动结束后，位置已经通过 setModalPosition 保存，不需要额外处理
    console.log('拖动结束 - 最终位置:', modalPosition)
  }

  // 添加和移除全局鼠标事件监听器
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      
      // 只在首次打开时初始化窗体位置为屏幕中心
      if (modalPosition.x === 0 && modalPosition.y === 0) {
        setModalPosition({
          x: (window.innerWidth - 600) / 2,
          y: (window.innerHeight - 400) / 2
        })
      }
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isOpen, isDragging, dragOffset, modalPosition.x, modalPosition.y])

  // 获取数据的函数
  const fetchData = async (searchTerm: string = '') => {
    if (!apiUrl) return
    
    try {
      setIsLoading(true)
      setError(null)
      
      let url = apiUrl
      let requestOptions: RequestInit = {
        method: apiMethod,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      }
      
      if (apiMethod === 'GET') {
        // GET请求：将搜索词和参数添加到URL
        const params = new URLSearchParams()
        if (searchTerm) {
          params.append('search', searchTerm)
        }
        // 添加其他API参数
        Object.entries(apiParams).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, String(value))
          }
        })
        if (params.toString()) {
          url += `?${params.toString()}`
        }
      } else {
        // POST请求：将搜索词和参数添加到请求体
        const requestBody = {
          ...apiParams
        }
        // 如果有搜索词，添加到请求体中
        if (searchTerm) {
          requestBody.search = searchTerm
        }
        requestOptions.body = JSON.stringify(requestBody)
      }
      
      console.log('SelectInput API请求:', { url, method: apiMethod, body: requestOptions.body })
      
      const response = await fetch(url, requestOptions)
      
      console.log('SelectInput API响应状态:', response.status, response.statusText)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      console.log('SelectInput API响应数据:', result)
      
      // 处理API响应数据
      if (result.success && result.data) {
        setApiData(result.data)
        setFilteredData(result.data)
      } else {
        setApiData([])
        setFilteredData([])
        setError(result.message || '获取数据失败')
      }
    } catch (err) {
      console.error('SelectInput API请求失败:', err)
      setError(err instanceof Error ? err.message : '网络请求失败')
      setApiData([])
      setFilteredData([])
    } finally {
      setIsLoading(false)
    }
  }

  // 处理搜索
  const handleSearch = (term: string) => {
    setSearchTerm(term)
    
    if (apiUrl) {
      // 使用API搜索
      fetchData(term)
    } else if (onSearch) {
      // 使用自定义搜索
      onSearch(term)
    } else {
      // 本地搜索
      const filtered = data.filter(item =>
        Object.values(item).some(val =>
          val && val.toString().toLowerCase().includes(term.toLowerCase())
        )
      )
      setFilteredData(filtered)
    }
  }

  // 处理选择
  const handleSelect = (row: any) => {
    let selectedValue: string
    if (returnFormat === 'field') {
      selectedValue = row[valueField] || row.id || row.value || row
    } else {
      selectedValue = JSON.stringify(row)
    }
    onChange(selectedValue)
    onClose()
    setSearchTerm('')
  }

  // 清空选择
  const handleClear = () => {
    onChange('')
  }

  // 获取显示值
  const getDisplayValue = () => {
    if (!value) return ''
    
    const currentData = apiUrl ? apiData : data
    const selectedItem = currentData.find(item =>
      item.id === value || item.value === value || item === value
    )
    return selectedItem ?
      (selectedItem[displayField] || selectedItem.name || selectedItem.label || selectedItem.id || value) :
      value
  }

  // 当窗体打开时获取数据
  useEffect(() => {
    if (isOpen && apiUrl) {
      fetchData()
    }
  }, [isOpen, apiUrl])

  // 初始化过滤数据
  useEffect(() => {
    if (apiUrl) {
      setFilteredData(apiData)
    } else {
      setFilteredData(data)
    }
  }, [apiUrl, apiData, data])

  return (
    <>
      <Box width={width} height={height}>
        {label && (
          <Text fontSize="sm" fontWeight="medium" mb={0.5} color="gray.700">
            {label}
          </Text>
        )}
        <Flex align="center" gap={1}>
          <Input
            value={getDisplayValue()}
            placeholder={placeholder}
        
          
            flex="1"
            size="sm"
           
            fontSize="sm"
          />
          
          <Button
            size="sm"
            variant="outline"
            colorScheme="blue"
            onClick={onOpen}
            disabled={isDisabled}
         
            fontSize="sm"
            borderRadius="md"
            p={0}
          >
            {buttonIcon}
          </Button>
        </Flex>
      </Box>

      {/* 选择窗体 - 使用简单的覆盖层 */}
      {isOpen && (
        <Box
          position="fixed"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="rgba(0, 0, 0, 0.5)"
          zIndex={1000}
          onClick={onClose}
        >
          <Box
            position="absolute"
            top={`${modalPosition.y}px`}
            left={`${modalPosition.x}px`}
            bg="white"
            borderRadius="lg"
            p={4}
            minW="500px"
            maxW="700px"
            maxH="70vh"
            overflow="hidden"
            onClick={(e) => e.stopPropagation()}
            boxShadow="xl"
            border="1px"
            borderColor="gray.200"
            cursor={isDragging ? "grabbing" : "default"}
            onMouseDown={handleMouseDown}
          >
            {/* 标题栏 */}
            <Flex 
              justify="space-between" 
              align="center" 
              mb={3}
              cursor="grab"
              _active={{ cursor: "grabbing" }}
              onMouseDown={handleMouseDown}
              p={2}
              borderRadius="md"
              _hover={{ bg: "gray.50" }}
              transition="all 0.2s"
            >
              <Flex align="center" gap={2}>
                <Text fontSize="md" fontWeight="bold">{modalTitle}</Text>
              </Flex>
              <Text fontSize="xs" color="gray.500">
                共 {filteredData.length} 条数据
              </Text>
              <Button
                aria-label="关闭"
                size="sm"
                variant="ghost"
                onClick={onClose}
                minW="24px"
                h="28px"
                p={0}
                borderRadius="md"
              >
                <FiX size={14} />
              </Button>
            </Flex>

            {/* 搜索框 */}
            <Box mb={3}>
              <Input
                placeholder={searchPlaceholder}
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                size="sm"
                height="32px"
              />
            </Box>

            {/* 数据列表 */}
            <Box maxH="350px" overflowY="auto">
              {isLoading ? (
                <Flex justify="center" align="center" h="150px">
                  <Text color="gray.500">加载中...</Text>
                </Flex>
              ) : error ? (
                <Flex justify="center" align="center" h="150px">
                  <Text color="red.500">{error}</Text>
                </Flex>
              ) : filteredData.length === 0 ? (
                <Flex justify="center" align="center" h="150px">
                  <Text color="gray.500">{emptyMessage}</Text>
                </Flex>
              ) : (
                <Box>
                  {filteredData.map((row, index) => (
                    <Box
                      key={index}
                      p={2}
                      border="1px"
                      borderColor="gray.200"
                      borderRadius="md"
                      cursor="pointer"
                      mb={1}
                      _hover={{
                        bg: "blue.50",
                        borderColor: "blue.300"
                      }}
                      onClick={() => handleSelect(row)}
                    >
                      <Flex gap={3}>
                        {columns.map((col, colIndex) => (
                          <Box 
                            key={colIndex} 
                            flex={col.flex || 1}
                            minW={col.minWidth}
                            maxW={col.maxWidth}
                            w={col.width}
                            textAlign={col.align || "left"}
                            className={col.className}
                          >
                            <Text fontSize="sm" fontWeight="medium">
                              {col.render ? col.render(row[col.field], row) : (row[col.field] || '-')}
                            </Text>
                          </Box>
                        ))}
                      </Flex>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </Box>
        </Box>
      )}
    </>
  )
}

export default SelectInput 