import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react'
import { Box, Input, Button, Text, Flex, useDisclosure } from '@chakra-ui/react'
import { FiSearch, FiX } from 'react-icons/fi'

// AG-Grid 单元格编辑器接口
interface ICellEditorParams {
  value: string
  data: any
  column: any
  api: any
  columnApi: any
  node: any
  rowIndex: number
  colDef: any
  field: string
}

// AG-Grid 单元格编辑器引用接口
interface ICellEditorComp {
  getValue(): string
  isPopup?(): boolean
  isCancelBeforeStart?(): boolean
  isCancelAfterEnd?(): boolean
  focusIn?(): void
  focusOut?(): void
}

// SelectInput 单元格编辑器组件
const SelectInputCellEditor = forwardRef<ICellEditorComp, ICellEditorParams>((props, ref) => {
  const { value, data, field } = props
  const { open: isOpen, onOpen, onClose } = useDisclosure()
  const [selectedValue, setSelectedValue] = useState(value || '')
  const [searchTerm, setSearchTerm] = useState('')
  const [apiData, setApiData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // 拖动相关状态
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 })

  // 配置参数 - 从 colDef 中获取
  const config = props.colDef.selectInputConfig || {}
  const {
    apiUrl = '/api/v1/feature/unified',
    apiMethod = 'POST',
    apiParams = { action: 'list', module: 'feature' },
    columns = [
      { header: '属性代码', field: 'featureCode', width: 120 },
      { header: '属性描述', field: 'featureDesc', width: 150 }
    ],
    valueField = 'featureCode',
    displayField = 'featureDesc',
    returnFormat = 'field',
    modalTitle = '选择属性'
  } = config

  // 实现 AG-Grid 接口
  useImperativeHandle(ref, () => ({
    getValue: () => selectedValue,
    isPopup: () => true,
    focusIn: () => {
      // 自动打开选择框
      onOpen()
    }
  }))

  // 处理拖动开始
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      setIsDragging(true)
      const rect = e.currentTarget.getBoundingClientRect()
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      })
    }
  }

  // 处理拖动移动
  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setModalPosition({
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y
      })
    }
  }

  // 处理拖动结束
  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // 获取数据
  const fetchData = async (search?: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const requestParams = {
        ...apiParams,
        search: search || ''
      }
      
      const response = await fetch(apiUrl, {
        method: apiMethod,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: apiMethod === 'POST' ? JSON.stringify(requestParams) : undefined
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      if (result.success && result.data) {
        setApiData(result.data.items || result.data || [])
      } else {
        setApiData([])
      }
    } catch (err) {
      console.error('获取数据失败:', err)
      setError(err instanceof Error ? err.message : '获取数据失败')
      setApiData([])
    } finally {
      setIsLoading(false)
    }
  }

  // 处理选择
  const handleSelect = (item: any) => {
    let newValue = ''
    
    if (returnFormat === 'object') {
      // 返回对象格式
      newValue = JSON.stringify(item)
    } else {
      // 返回字段值
      newValue = item[valueField] || ''
    }
    
    setSelectedValue(newValue)
    onClose()
  }

  // 处理搜索
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value
    setSearchTerm(term)
    fetchData(term)
  }

  // 清空搜索
  const clearSearch = () => {
    setSearchTerm('')
    fetchData()
  }

  // 打开模态框时获取数据
  useEffect(() => {
    if (isOpen) {
      fetchData()
    }
  }, [isOpen])

  // 设置初始位置
  useEffect(() => {
    if (isOpen && modalPosition.x === 0 && modalPosition.y === 0) {
      setModalPosition({
        x: window.innerWidth / 2 - 300,
        y: window.innerHeight / 2 - 250
      })
    }
  }, [isOpen, modalPosition])

  return (
    <>
      {/* 输入框 */}
      <Input
        value={selectedValue}
        onChange={(e) => setSelectedValue(e.target.value)}
        placeholder="请选择"
        size="sm"
        readOnly
        onClick={onOpen}
        cursor="pointer"
        bg="white"
        _hover={{ bg: 'gray.50' }}
      />
      
      {/* 选择模态框 */}
      {isOpen && (
        <Box
          position="fixed"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="rgba(0, 0, 0, 0.5)"
          zIndex={9999}
          onClick={onClose}
        >
          <Box
            position="absolute"
            left={`${modalPosition.x}px`}
            top={`${modalPosition.y}px`}
            w="600px"
            maxH="500px"
            bg="white"
            borderRadius="md"
            boxShadow="xl"
            overflow="hidden"
            onClick={(e) => e.stopPropagation()}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            {/* 标题栏 */}
            <Box
              bg="blue.500"
              color="white"
              p={3}
              cursor="move"
              onMouseDown={handleMouseDown}
              userSelect="none"
            >
              <Flex justify="space-between" align="center">
                <Text fontWeight="bold">{modalTitle}</Text>
                <Button
                  size="sm"
                  variant="ghost"
                  color="white"
                  _hover={{ bg: 'blue.600' }}
                  onClick={onClose}
                >
                  <FiX />
                </Button>
              </Flex>
            </Box>
            
            {/* 搜索栏 */}
            <Box p={3} borderBottom="1px" borderColor="gray.200">
              <Flex gap={2}>
                <Input
                  placeholder="请输入搜索关键词"
                  value={searchTerm}
                  onChange={handleSearch}
                  size="sm"
                />
                <Button size="sm" onClick={clearSearch} variant="outline">
                  清空
                </Button>
              </Flex>
            </Box>
            
            {/* 数据表格 */}
            <Box flex={1} overflow="auto" maxH="350px">
              {isLoading ? (
                <Box p={4} textAlign="center">
                  <Text>加载中...</Text>
                </Box>
              ) : error ? (
                <Box p={4} textAlign="center" color="red.500">
                  <Text>{error}</Text>
                </Box>
              ) : apiData.length === 0 ? (
                <Box p={4} textAlign="center" color="gray.500">
                  <Text>暂无数据</Text>
                </Box>
              ) : (
                <Box>
                  {/* 表头 */}
                  <Box
                    display="grid"
                    gridTemplateColumns={`repeat(${columns.length}, 1fr)`}
                    bg="gray.100"
                    p={2}
                    borderBottom="1px"
                    borderColor="gray.200"
                    fontWeight="bold"
                    fontSize="sm"
                  >
                    {columns.map((col, index) => (
                      <Box key={index} textAlign="center">
                        {col.header}
                      </Box>
                    ))}
                  </Box>
                  
                  {/* 数据行 */}
                  {apiData.map((item, rowIndex) => (
                    <Box
                      key={rowIndex}
                      display="grid"
                      gridTemplateColumns={`repeat(${columns.length}, 1fr)`}
                      p={2}
                      borderBottom="1px"
                      borderColor="gray.200"
                      cursor="pointer"
                      _hover={{ bg: "blue.50" }}
                      onClick={() => handleSelect(item)}
                    >
                      {columns.map((col, colIndex) => (
                        <Box key={colIndex} textAlign="center" fontSize="sm">
                          {col.render ? col.render(item[col.field], item) : item[col.field] || ''}
                        </Box>
                      ))}
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
})

SelectInputCellEditor.displayName = 'SelectInputCellEditor'

export default SelectInputCellEditor 