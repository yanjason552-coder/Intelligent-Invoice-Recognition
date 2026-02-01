import { Box, Text, VStack, HStack, Button, Badge, IconButton, Flex } from "@chakra-ui/react"
import { useState, useRef, useEffect, useCallback, useMemo } from "react"
import { FiZoomIn, FiZoomOut, FiMaximize2, FiTrash2, FiEdit2, FiPlus, FiX } from "react-icons/fi"
import ImageAnnotator, { Annotation } from './ImageAnnotator'
import AnnotationDialog from './AnnotationDialog'

interface EnhancedImageAnnotatorProps {
  imageUrl: string | null
  annotations: Annotation[]
  onAnnotationsChange: (annotations: Annotation[]) => void
  fields?: Array<{
    id: string
    field_name: string
    field_key: string
  }>
  onFieldAssociate?: (annotationId: string, fieldId: string) => void
}

const EnhancedImageAnnotator = ({
  imageUrl,
  annotations,
  onAnnotationsChange,
  fields = [],
  onFieldAssociate
}: EnhancedImageAnnotatorProps) => {
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<string | null>(null)
  const [scale, setScale] = useState(1)
  const [isAnnotationMode, setIsAnnotationMode] = useState(false)
  const [showAnnotationList, setShowAnnotationList] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingAnnotation, setEditingAnnotation] = useState<Annotation | null>(null)

  // 按类型分组标注
  const groupedAnnotations = useMemo(() => {
    return {
      logo: annotations.filter(a => a.type === 'logo'),
      field: annotations.filter(a => a.type === 'field'),
      regex: annotations.filter(a => a.type === 'regex')
    }
  }, [annotations])

  // 处理标注添加
  const handleAnnotationAdd = useCallback((annotation: Annotation) => {
    // 创建新标注后，打开对话框让用户设置属性
    setEditingAnnotation(annotation)
    setDialogOpen(true)
    setIsAnnotationMode(false)
  }, [])

  // 处理标注保存（从对话框）
  const handleAnnotationSave = useCallback((updatedAnnotation: Annotation) => {
    const existingIndex = annotations.findIndex(a => a.id === updatedAnnotation.id)
    let newAnnotations: Annotation[]
    
    if (existingIndex >= 0) {
      // 更新现有标注
      newAnnotations = annotations.map((a, index) => 
        index === existingIndex ? updatedAnnotation : a
      )
    } else {
      // 添加新标注
      newAnnotations = [...annotations, updatedAnnotation]
    }
    
    onAnnotationsChange(newAnnotations)
    setSelectedAnnotationId(updatedAnnotation.id)
    setEditingAnnotation(null)
  }, [annotations, onAnnotationsChange])

  // 处理编辑标注
  const handleEditAnnotation = useCallback((annotation: Annotation) => {
    setEditingAnnotation(annotation)
    setDialogOpen(true)
  }, [])

  // 监听选中标注的变化，双击时打开编辑对话框
  useEffect(() => {
    if (selectedAnnotationId) {
      const annotation = annotations.find(a => a.id === selectedAnnotationId)
      // 注意：这里不自动打开对话框，避免与点击选中冲突
      // 用户可以通过点击编辑按钮或双击来打开对话框
    }
  }, [selectedAnnotationId, annotations])

  // 处理标注选中（双击时打开编辑对话框）
  const handleAnnotationSelect = useCallback((id: string | null) => {
    setSelectedAnnotationId(id)
    if (id) {
      const annotation = annotations.find(a => a.id === id)
      if (annotation) {
        // 延迟打开对话框，避免与点击事件冲突
        setTimeout(() => {
          setEditingAnnotation(annotation)
          setDialogOpen(true)
        }, 100)
      }
    }
  }, [annotations])

  // 处理标注更新
  const handleAnnotationChange = useCallback((newAnnotations: Annotation[]) => {
    onAnnotationsChange(newAnnotations)
  }, [onAnnotationsChange])

  // 处理标注删除
  const handleAnnotationDelete = useCallback((id: string) => {
    const newAnnotations = annotations.filter(a => a.id !== id)
    onAnnotationsChange(newAnnotations)
    if (selectedAnnotationId === id) {
      setSelectedAnnotationId(null)
    }
  }, [annotations, onAnnotationsChange, selectedAnnotationId])

  // 缩放控制
  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.1, 2))
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.1, 0.5))
  const handleFitToWindow = () => setScale(1)

  // 获取标注颜色
  const getAnnotationColor = (type: Annotation['type']) => {
    switch (type) {
      case 'logo': return '#10B981'
      case 'field': return '#3B82F6'
      case 'regex': return '#F59E0B'
      default: return '#3B82F6'
    }
  }

  // 获取标注类型标签
  const getTypeLabel = (type: Annotation['type']) => {
    switch (type) {
      case 'logo': return 'Logo'
      case 'field': return '字段'
      case 'regex': return '正则'
      default: return '未知'
    }
  }

  if (!imageUrl) {
    return (
      <Box
        border="2px dashed"
        borderColor="gray.300"
        borderRadius="md"
        p={12}
        textAlign="center"
        bg="gray.50"
      >
        <Text color="gray.500">请先上传示例文件</Text>
      </Box>
    )
  }

  return (
    <VStack spacing={4} align="stretch">
      {/* 工具栏 */}
      <Flex justify="space-between" align="center" wrap="wrap" gap={2}>
        <HStack spacing={2}>
          <Button
            size="sm"
            leftIcon={<FiPlus />}
            colorScheme={isAnnotationMode ? "blue" : "gray"}
            variant={isAnnotationMode ? "solid" : "outline"}
            onClick={() => setIsAnnotationMode(!isAnnotationMode)}
          >
            {isAnnotationMode ? "取消标注" : "开始标注"}
          </Button>
          {selectedAnnotationId && (
            <>
              <IconButton
                aria-label="删除标注"
                icon={<FiTrash2 />}
                size="sm"
                colorScheme="red"
                variant="outline"
                onClick={() => {
                  if (confirm('确定要删除此标注吗？')) {
                    handleAnnotationDelete(selectedAnnotationId)
                  }
                }}
              />
            </>
          )}
        </HStack>

        <HStack spacing={2}>
          <Text fontSize="sm" color="gray.600">缩放:</Text>
          <IconButton
            aria-label="缩小"
            icon={<FiZoomOut />}
            size="sm"
            onClick={handleZoomOut}
            isDisabled={scale <= 0.5}
          />
          <Text fontSize="sm" minW="50px" textAlign="center">
            {Math.round(scale * 100)}%
          </Text>
          <IconButton
            aria-label="放大"
            icon={<FiZoomIn />}
            size="sm"
            onClick={handleZoomIn}
            isDisabled={scale >= 2}
          />
          <Button
            size="sm"
            leftIcon={<FiMaximize2 />}
            variant="outline"
            onClick={handleFitToWindow}
          >
            适应窗口
          </Button>
        </HStack>
      </Flex>

      {/* 主要内容区域 */}
      <Flex gap={4} direction={{ base: 'column', lg: 'row' }}>
        {/* 标注画布区域 */}
        <Box flex="1" bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
          <Box
            style={{
              transform: `scale(${scale})`,
              transformOrigin: 'top left',
              transition: 'transform 0.2s'
            }}
          >
            <ImageAnnotator
              imageUrl={imageUrl}
              annotations={annotations}
              onAnnotationChange={handleAnnotationChange}
              onAnnotationAdd={handleAnnotationAdd}
              onAnnotationDelete={handleAnnotationDelete}
              editable={isAnnotationMode}
              selectedAnnotationId={selectedAnnotationId}
              onAnnotationSelect={handleAnnotationSelect}
              scale={scale}
            />
          </Box>
        </Box>

        {/* 标注列表面板 */}
        {showAnnotationList && (
          <Box
            w={{ base: '100%', lg: '300px' }}
            bg="white"
            p={4}
            borderRadius="md"
            border="1px"
            borderColor="gray.200"
            maxH="600px"
            overflowY="auto"
          >
            <Flex justify="space-between" align="center" mb={4}>
              <Text fontSize="lg" fontWeight="medium">
                标注列表 ({annotations.length})
              </Text>
              <IconButton
                aria-label="关闭列表"
                icon={<FiX />}
                size="sm"
                variant="ghost"
                onClick={() => setShowAnnotationList(false)}
                display={{ base: 'block', lg: 'none' }}
              />
            </Flex>

            {annotations.length === 0 ? (
              <Box textAlign="center" p={8} color="gray.500">
                <Text fontSize="sm">暂无标注</Text>
                <Text fontSize="xs" mt={2} color="gray.400">
                  点击"开始标注"按钮创建标注
                </Text>
              </Box>
            ) : (
              <VStack spacing={2} align="stretch">
                {/* Logo标注 */}
                {groupedAnnotations.logo.length > 0 && (
                  <Box>
                    <Text fontSize="xs" fontWeight="medium" color="gray.600" mb={2}>
                      Logo标注 ({groupedAnnotations.logo.length})
                    </Text>
                    {groupedAnnotations.logo.map(ann => (
                      <Box
                        key={ann.id}
                        p={2}
                        borderRadius="md"
                        border="1px"
                        borderColor={selectedAnnotationId === ann.id ? "green.500" : "gray.200"}
                        bg={selectedAnnotationId === ann.id ? "green.50" : "white"}
                        cursor="pointer"
                        onClick={() => setSelectedAnnotationId(ann.id)}
                        mb={2}
                      >
                        <Flex justify="space-between" align="start">
                          <VStack align="start" spacing={1} flex="1">
                            <HStack spacing={2}>
                              <Badge colorScheme="green" fontSize="xs">
                                {getTypeLabel(ann.type)}
                              </Badge>
                              <Text fontSize="sm" fontWeight="medium">
                                {ann.label || '未命名'}
                              </Text>
                            </HStack>
                            <Text fontSize="xs" color="gray.500">
                              位置: ({Math.round(ann.x)}, {Math.round(ann.y)})
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              大小: {Math.round(ann.width)} × {Math.round(ann.height)}
                            </Text>
                          </VStack>
                              <HStack spacing={1}>
                                <IconButton
                                  aria-label="编辑"
                                  icon={<FiEdit2 />}
                                  size="xs"
                                  colorScheme="blue"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleEditAnnotation(ann)
                                  }}
                                />
                                <IconButton
                                  aria-label="删除"
                                  icon={<FiTrash2 />}
                                  size="xs"
                                  colorScheme="red"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (confirm('确定要删除此标注吗？')) {
                                      handleAnnotationDelete(ann.id)
                                    }
                                  }}
                                />
                              </HStack>
                        </Flex>
                      </Box>
                    ))}
                  </Box>
                )}

                {/* 字段标注 */}
                {groupedAnnotations.field.length > 0 && (
                  <Box>
                    <Text fontSize="xs" fontWeight="medium" color="gray.600" mb={2}>
                      字段标注 ({groupedAnnotations.field.length})
                    </Text>
                    {groupedAnnotations.field.map(ann => {
                      const associatedField = fields.find(f => f.id === ann.label || f.field_name === ann.label)
                      return (
                        <Box
                          key={ann.id}
                          p={2}
                          borderRadius="md"
                          border="1px"
                          borderColor={selectedAnnotationId === ann.id ? "blue.500" : "gray.200"}
                          bg={selectedAnnotationId === ann.id ? "blue.50" : "white"}
                          cursor="pointer"
                          onClick={() => setSelectedAnnotationId(ann.id)}
                          mb={2}
                        >
                          <Flex justify="space-between" align="start">
                            <VStack align="start" spacing={1} flex="1">
                              <HStack spacing={2}>
                                <Badge colorScheme="blue" fontSize="xs">
                                  {getTypeLabel(ann.type)}
                                </Badge>
                                <Text fontSize="sm" fontWeight="medium">
                                  {ann.label || '未命名'}
                                </Text>
                                {associatedField && (
                                  <Badge colorScheme="green" fontSize="xs">
                                    已关联
                                  </Badge>
                                )}
                              </HStack>
                              {associatedField && (
                                <Text fontSize="xs" color="green.600">
                                  关联字段: {associatedField.field_name}
                                </Text>
                              )}
                              <Text fontSize="xs" color="gray.500">
                                位置: ({Math.round(ann.x)}, {Math.round(ann.y)})
                              </Text>
                              <Text fontSize="xs" color="gray.500">
                                大小: {Math.round(ann.width)} × {Math.round(ann.height)}
                              </Text>
                            </VStack>
                              <HStack spacing={1}>
                                <IconButton
                                  aria-label="编辑"
                                  icon={<FiEdit2 />}
                                  size="xs"
                                  colorScheme="blue"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleEditAnnotation(ann)
                                  }}
                                />
                                <IconButton
                                  aria-label="删除"
                                  icon={<FiTrash2 />}
                                  size="xs"
                                  colorScheme="red"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (confirm('确定要删除此标注吗？')) {
                                      handleAnnotationDelete(ann.id)
                                    }
                                  }}
                                />
                              </HStack>
                          </Flex>
                        </Box>
                      )
                    })}
                  </Box>
                )}

                {/* 正则标注 */}
                {groupedAnnotations.regex.length > 0 && (
                  <Box>
                    <Text fontSize="xs" fontWeight="medium" color="gray.600" mb={2}>
                      正则标注 ({groupedAnnotations.regex.length})
                    </Text>
                    {groupedAnnotations.regex.map(ann => (
                      <Box
                        key={ann.id}
                        p={2}
                        borderRadius="md"
                        border="1px"
                        borderColor={selectedAnnotationId === ann.id ? "orange.500" : "gray.200"}
                        bg={selectedAnnotationId === ann.id ? "orange.50" : "white"}
                        cursor="pointer"
                        onClick={() => setSelectedAnnotationId(ann.id)}
                        mb={2}
                      >
                        <Flex justify="space-between" align="start">
                          <VStack align="start" spacing={1} flex="1">
                            <HStack spacing={2}>
                              <Badge colorScheme="orange" fontSize="xs">
                                {getTypeLabel(ann.type)}
                              </Badge>
                              <Text fontSize="sm" fontWeight="medium">
                                {ann.label || '未命名'}
                              </Text>
                            </HStack>
                            <Text fontSize="xs" color="gray.500">
                              位置: ({Math.round(ann.x)}, {Math.round(ann.y)})
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              大小: {Math.round(ann.width)} × {Math.round(ann.height)}
                            </Text>
                          </VStack>
                              <HStack spacing={1}>
                                <IconButton
                                  aria-label="编辑"
                                  icon={<FiEdit2 />}
                                  size="xs"
                                  colorScheme="blue"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleEditAnnotation(ann)
                                  }}
                                />
                                <IconButton
                                  aria-label="删除"
                                  icon={<FiTrash2 />}
                                  size="xs"
                                  colorScheme="red"
                                  variant="ghost"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (confirm('确定要删除此标注吗？')) {
                                      handleAnnotationDelete(ann.id)
                                    }
                                  }}
                                />
                              </HStack>
                        </Flex>
                      </Box>
                    ))}
                  </Box>
                )}
              </VStack>
            )}
          </Box>
        )}

        {/* 移动端显示列表按钮 */}
        {!showAnnotationList && (
          <Button
            display={{ base: 'block', lg: 'none' }}
            onClick={() => setShowAnnotationList(true)}
            leftIcon={<FiPlus />}
            size="sm"
            variant="outline"
          >
            显示标注列表
          </Button>
        )}
      </Flex>

      {/* 操作提示 */}
      {isAnnotationMode && (
        <Box p={3} bg="blue.50" borderRadius="md" border="1px" borderColor="blue.200">
          <Text fontSize="sm" color="blue.700">
            💡 提示：在图片上拖拽创建标注框，创建后可以设置标注类型和关联字段
          </Text>
        </Box>
      )}

      {/* 标注属性对话框 */}
      <AnnotationDialog
        open={dialogOpen}
        annotation={editingAnnotation}
        fields={fields}
        onClose={() => {
          setDialogOpen(false)
          setEditingAnnotation(null)
          // 如果是在创建新标注时关闭对话框，删除未完成的标注
          if (editingAnnotation && !annotations.find(a => a.id === editingAnnotation.id)) {
            // 标注还未保存，不需要删除
          }
        }}
        onSave={handleAnnotationSave}
      />
    </VStack>
  )
}

export default EnhancedImageAnnotator

