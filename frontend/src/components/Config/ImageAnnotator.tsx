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
}

const ImageAnnotator = ({
  imageUrl,
  annotations = [],
  onAnnotationChange,
  onAnnotationAdd,
  onAnnotationDelete,
  editable = true
}: ImageAnnotatorProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [startPos, setStartPos] = useState<{ x: number, y: number } | null>(null)
  const [currentAnnotation, setCurrentAnnotation] = useState<Annotation | null>(null)
  const [scale, setScale] = useState(1)
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null)

  // 加载图片
  useEffect(() => {
    if (!imageUrl || !canvasRef.current) return

    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      imageRef.current = img
      const canvas = canvasRef.current!
      const container = containerRef.current!
      
      // 计算缩放比例以适应容器
      const maxWidth = container.clientWidth - 40
      const maxHeight = 600
      const scaleX = maxWidth / img.width
      const scaleY = maxHeight / img.height
      const newScale = Math.min(scaleX, scaleY, 1)
      setScale(newScale)

      canvas.width = img.width * newScale
      canvas.height = img.height * newScale
      drawImage()
    }
    img.src = imageUrl
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

      const newAnnotation: Annotation = {
        id: `annotation-${Date.now()}`,
        type: 'field',
        x,
        y,
        width,
        height,
        color: '#3B82F6'
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
  }, [annotations, selectedAnnotation, currentAnnotation])

  return (
    <Box ref={containerRef} position="relative" w="100%">
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        style={{
          cursor: editable ? 'crosshair' : 'default',
          border: '1px solid #e2e8f0',
          borderRadius: '4px',
          maxWidth: '100%'
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

