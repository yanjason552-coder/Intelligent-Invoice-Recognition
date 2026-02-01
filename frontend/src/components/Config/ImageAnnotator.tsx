import { Box, Text } from "@chakra-ui/react"
import { useState, useRef, useEffect } from "react"

interface Annotation {
  id: string
  type: 'logo' | 'field' | 'regex'
  x: number
  y: number
  width: number
  height: number
  label?: string
  color: string
}

interface ImageAnnotatorProps {
  imageUrl: string
  annotations: Annotation[]
  onAnnotationChange?: (annotations: Annotation[]) => void
  onAnnotationAdd?: (annotation: Annotation) => void
  onAnnotationDelete?: (id: string) => void
  editable?: boolean
  selectedAnnotationId?: string | null
  onAnnotationSelect?: (id: string | null) => void
  scale?: number
}

const ImageAnnotator = ({
  imageUrl,
  annotations = [],
  onAnnotationChange,
  onAnnotationAdd,
  onAnnotationDelete,
  editable = true,
  selectedAnnotationId: externalSelectedId,
  onAnnotationSelect,
  scale: externalScale = 1
}: ImageAnnotatorProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [startPos, setStartPos] = useState<{ x: number, y: number } | null>(null)
  const [currentAnnotation, setCurrentAnnotation] = useState<Annotation | null>(null)
  const [internalScale, setInternalScale] = useState(1)
  const [internalSelectedAnnotation, setInternalSelectedAnnotation] = useState<string | null>(null)
  
  // 使用外部传入的scale和selectedAnnotationId，如果没有则使用内部状态
  const scale = externalScale !== 1 ? externalScale : internalScale
  const selectedAnnotation = externalSelectedId !== undefined ? externalSelectedId : internalSelectedAnnotation
  
  const setSelectedAnnotation = (id: string | null) => {
    if (onAnnotationSelect) {
      onAnnotationSelect(id)
    } else {
      setInternalSelectedAnnotation(id)
    }
  }

  // 加载图片
  useEffect(() => {
    if (!imageUrl || !canvasRef.current) return

    const img = new Image()
    img.crossOrigin = 'anonymous'
    
    img.onload = () => {
      console.log('ImageAnnotator: 图片加载成功', imageUrl)
      imageRef.current = img
      const canvas = canvasRef.current!
      const container = containerRef.current!
      
      if (!container) {
        console.warn('ImageAnnotator: 容器未找到')
        return
      }
      
      // 计算缩放比例以适应容器（仅在未传入外部scale时）
      if (externalScale === 1) {
        const maxWidth = container.clientWidth - 40 || 800
        const maxHeight = 600
        const scaleX = maxWidth / img.width
        const scaleY = maxHeight / img.height
        const newScale = Math.min(scaleX, scaleY, 1)
        setInternalScale(newScale)
        
        canvas.width = img.width * newScale
        canvas.height = img.height * newScale
      } else {
        // 使用外部传入的scale
        canvas.width = img.width * externalScale
        canvas.height = img.height * externalScale
      }
      drawImage()
    }
    
    img.onerror = (error) => {
      console.error('ImageAnnotator: 图片加载失败', imageUrl, error)
    }
    
    // 处理不同类型的图片URL
    let finalUrl = imageUrl
    
    // data URL 和 blob URL 直接使用
    if (imageUrl.startsWith('data:') || imageUrl.startsWith('blob:')) {
      finalUrl = imageUrl
    } 
    // HTTP/HTTPS URL 直接使用
    else if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      finalUrl = imageUrl
    }
    // 相对路径需要转换为绝对路径
    else {
      if (imageUrl.startsWith('/')) {
        finalUrl = `${window.location.origin}${imageUrl}`
      } else {
        finalUrl = `${window.location.origin}/api/v1${imageUrl}`
      }
    }
    
    console.log('ImageAnnotator: 开始加载图片', finalUrl)
    
    // 对于 blob URL，移除 crossOrigin 属性（可能导致 CORS 错误）
    if (imageUrl.startsWith('blob:') || imageUrl.startsWith('data:')) {
      img.crossOrigin = null
    }
    
    img.src = finalUrl
  }, [imageUrl])

  // 绘制图片和标注
  const drawImage = () => {
    const canvas = canvasRef.current
    const img = imageRef.current
    if (!canvas || !img) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 绘制图片
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

    // 绘制所有标注
    annotations.forEach(annotation => {
      drawAnnotation(ctx, annotation, annotation.id === selectedAnnotation)
    })

    // 绘制当前正在绘制的标注
    if (currentAnnotation) {
      drawAnnotation(ctx, currentAnnotation, false)
    }
  }

  // 绘制单个标注
  const drawAnnotation = (
    ctx: CanvasRenderingContext2D,
    annotation: Annotation,
    selected: boolean = false
  ) => {
    const { x, y, width, height, label, color } = annotation

    // 绘制矩形框
    ctx.strokeStyle = selected ? '#FF0000' : color
    ctx.lineWidth = selected ? 3 : 2
    ctx.setLineDash([])
    ctx.strokeRect(x, y, width, height)

    // 绘制半透明填充
    ctx.fillStyle = color + '20'
    ctx.fillRect(x, y, width, height)

    // 绘制标签
    if (label) {
      ctx.fillStyle = color
      ctx.font = '12px Arial'
      ctx.fillText(label, x, y - 5)
    }

    // 绘制控制点（如果选中）
    if (selected && editable) {
      const points = [
        { x, y }, // 左上
        { x: x + width, y }, // 右上
        { x, y: y + height }, // 左下
        { x: x + width, y: y + height } // 右下
      ]

      points.forEach(point => {
        ctx.fillStyle = '#FFFFFF'
        ctx.fillRect(point.x - 4, point.y - 4, 8, 8)
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.strokeRect(point.x - 4, point.y - 4, 8, 8)
      })
    }
  }

  // 获取鼠标在画布上的坐标
  const getCanvasCoordinates = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return null

    const rect = canvas.getBoundingClientRect()
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    }
  }

  // 检查点击是否在标注框内
  const getAnnotationAtPoint = (x: number, y: number): Annotation | null => {
    for (let i = annotations.length - 1; i >= 0; i--) {
      const ann = annotations[i]
      if (x >= ann.x && x <= ann.x + ann.width &&
          y >= ann.y && y <= ann.y + ann.height) {
        return ann
      }
    }
    return null
  }

  // 鼠标按下
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!editable) return

    const pos = getCanvasCoordinates(e)
    if (!pos) return

    const clickedAnnotation = getAnnotationAtPoint(pos.x, pos.y)
    
    if (clickedAnnotation) {
      // 选中现有标注
      setSelectedAnnotation(clickedAnnotation.id)
      setStartPos(pos)
      setIsDrawing(true)
    } else {
      // 开始绘制新标注
      setSelectedAnnotation(null)
      setStartPos(pos)
      setIsDrawing(true)
    }
  }

  // 鼠标移动
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPos) return

    const pos = getCanvasCoordinates(e)
    if (!pos) return

    if (selectedAnnotation) {
      // 移动现有标注
      const annotation = annotations.find(a => a.id === selectedAnnotation)
      if (annotation) {
        const dx = pos.x - startPos.x
        const dy = pos.y - startPos.y
        const updatedAnnotation = {
          ...annotation,
          x: annotation.x + dx,
          y: annotation.y + dy
        }
        const updatedAnnotations = annotations.map(a =>
          a.id === selectedAnnotation ? updatedAnnotation : a
        )
        onAnnotationChange?.(updatedAnnotations)
        setStartPos(pos)
        drawImage()
      }
    } else {
      // 绘制新标注
      const x = Math.min(startPos.x, pos.x)
      const y = Math.min(startPos.y, pos.y)
      const width = Math.abs(pos.x - startPos.x)
      const height = Math.abs(pos.y - startPos.y)

      // 根据标注类型设置颜色
      const getColorByType = (type: Annotation['type']) => {
        switch (type) {
          case 'logo': return '#10B981'
          case 'field': return '#3B82F6'
          case 'regex': return '#F59E0B'
          default: return '#3B82F6'
        }
      }
      
      const newAnnotation: Annotation = {
        id: `annotation-${Date.now()}`,
        type: 'field', // 默认类型，可以在创建后通过对话框修改
        x,
        y,
        width,
        height,
        color: getColorByType('field')
      }
      setCurrentAnnotation(newAnnotation)
      drawImage()
    }
  }

  // 鼠标释放
  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return

    if (currentAnnotation && currentAnnotation.width > 10 && currentAnnotation.height > 10) {
      // 完成新标注
      onAnnotationAdd?.(currentAnnotation)
      setCurrentAnnotation(null)
    }

    setIsDrawing(false)
    setStartPos(null)
  }

  // 重新绘制
  useEffect(() => {
    drawImage()
  }, [annotations, selectedAnnotation, currentAnnotation, scale])
  
  // 监听外部scale变化
  useEffect(() => {
    if (externalScale !== 1 && imageRef.current && canvasRef.current) {
      const img = imageRef.current
      canvasRef.current.width = img.width * externalScale
      canvasRef.current.height = img.height * externalScale
      drawImage()
    }
  }, [externalScale])

  return (
    <Box ref={containerRef} position="relative" w="100%">
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onDoubleClick={(e) => {
          if (!editable) return
          const pos = getCanvasCoordinates(e)
          if (!pos) return
          const clickedAnnotation = getAnnotationAtPoint(pos.x, pos.y)
          if (clickedAnnotation && onAnnotationSelect) {
            // 双击标注时，由父组件处理（打开编辑对话框）
            onAnnotationSelect(clickedAnnotation.id)
          }
        }}
        style={{
          cursor: editable ? (isDrawing ? 'crosshair' : 'default') : 'default',
          border: '1px solid #e2e8f0',
          borderRadius: '4px',
          maxWidth: '100%',
          display: 'block'
        }}
      />
      {editable && (
        <Box mt={2} p={2} bg="blue.50" borderRadius="md">
          <Text fontSize="xs" color="blue.700">
            💡 提示：点击并拖拽创建标注框，点击标注框可选中并移动
          </Text>
        </Box>
      )}
    </Box>
  )
}

export default ImageAnnotator
export type { Annotation }

