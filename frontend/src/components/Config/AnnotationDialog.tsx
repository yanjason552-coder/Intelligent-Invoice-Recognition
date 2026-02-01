import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogBody,
  DialogFooter,
  DialogTitle,
  DialogCloseTrigger,
} from "@/components/ui/dialog"
import { Box, Text, VStack, HStack, Select, Input, Textarea } from "@chakra-ui/react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { useState, useEffect } from "react"
import { Annotation } from "./ImageAnnotator"

interface AnnotationDialogProps {
  open: boolean
  annotation: Annotation | null
  fields?: Array<{
    id: string
    field_name: string
    field_key: string
  }>
  onClose: () => void
  onSave: (annotation: Annotation) => void
}

const AnnotationDialog = ({
  open,
  annotation,
  fields = [],
  onClose,
  onSave
}: AnnotationDialogProps) => {
  const [formData, setFormData] = useState<{
    type: Annotation['type']
    label: string
    fieldId: string
    regexPattern: string
  }>({
    type: 'field',
    label: '',
    fieldId: '',
    regexPattern: ''
  })

  // 当annotation变化时更新表单数据
  useEffect(() => {
    if (annotation) {
      const associatedField = fields.find(f => f.field_name === annotation.label)
      setFormData({
        type: annotation.type,
        label: annotation.label || '',
        fieldId: associatedField?.id || '',
        regexPattern: '' // 可以从annotation中提取，如果有的话
      })
    } else {
      // 重置表单
      setFormData({
        type: 'field',
        label: '',
        fieldId: '',
        regexPattern: ''
      })
    }
  }, [annotation, fields])

  const handleSave = () => {
    if (!annotation) return

    // 获取关联的字段名称
    let finalLabel = formData.label
    if (formData.type === 'field' && formData.fieldId) {
      const field = fields.find(f => f.id === formData.fieldId)
      if (field) {
        finalLabel = field.field_name
      }
    }

    // 根据类型设置颜色
    const getColorByType = (type: Annotation['type']) => {
      switch (type) {
        case 'logo': return '#10B981'
        case 'field': return '#3B82F6'
        case 'regex': return '#F59E0B'
        default: return '#3B82F6'
      }
    }

    const updatedAnnotation: Annotation = {
      ...annotation,
      type: formData.type,
      label: finalLabel,
      color: getColorByType(formData.type)
    }

    onSave(updatedAnnotation)
    onClose()
  }

  const handleTypeChange = (type: Annotation['type']) => {
    setFormData(prev => ({
      ...prev,
      type,
      // 切换类型时清空相关字段
      fieldId: type === 'field' ? prev.fieldId : '',
      regexPattern: type === 'regex' ? prev.regexPattern : ''
    }))
  }

  const handleFieldChange = (fieldId: string) => {
    const field = fields.find(f => f.id === fieldId)
    setFormData(prev => ({
      ...prev,
      fieldId,
      label: field ? field.field_name : prev.label
    }))
  }

  if (!annotation) return null

  return (
    <DialogRoot open={open} onOpenChange={({ open }) => !open && onClose()}>
      <DialogContent maxW="500px">
        <DialogHeader>
          <DialogTitle>标注属性</DialogTitle>
          <DialogCloseTrigger />
        </DialogHeader>
        <DialogBody>
          <VStack spacing={4} align="stretch">
            {/* 标注类型 */}
            <Field label="标注类型">
              <Select
                value={formData.type}
                onChange={(e) => handleTypeChange(e.target.value as Annotation['type'])}
              >
                <option value="field">字段标注</option>
                <option value="logo">Logo标注</option>
                <option value="regex">正则区域</option>
              </Select>
            </Field>

            {/* 标注名称/标签 */}
            {formData.type !== 'field' && (
              <Field label="标注名称">
                <Input
                  value={formData.label}
                  onChange={(e) => setFormData(prev => ({ ...prev, label: e.target.value }))}
                  placeholder="请输入标注名称"
                />
              </Field>
            )}

            {/* 字段关联（仅字段类型） */}
            {formData.type === 'field' && (
              <Field label="关联字段">
                <Select
                  value={formData.fieldId}
                  onChange={(e) => handleFieldChange(e.target.value)}
                >
                  <option value="">未关联</option>
                  {fields.map(field => (
                    <option key={field.id} value={field.id}>
                      {field.field_name} ({field.field_key})
                    </option>
                  ))}
                </Select>
                {formData.fieldId && (
                  <Text fontSize="xs" color="green.600" mt={1}>
                    ✓ 已关联到字段: {fields.find(f => f.id === formData.fieldId)?.field_name}
                  </Text>
                )}
              </Field>
            )}

            {/* 正则表达式（仅正则类型） */}
            {formData.type === 'regex' && (
              <Field label="正则表达式">
                <Input
                  value={formData.regexPattern}
                  onChange={(e) => setFormData(prev => ({ ...prev, regexPattern: e.target.value }))}
                  placeholder="例如: \d+\.\d{2}"
                />
                <Text fontSize="xs" color="gray.500" mt={1}>
                  用于匹配此区域的文本模式
                </Text>
              </Field>
            )}

            {/* 坐标信息（只读） */}
            <Box p={3} bg="gray.50" borderRadius="md">
              <Text fontSize="sm" fontWeight="medium" mb={2}>坐标信息</Text>
              <HStack spacing={4} fontSize="xs" color="gray.600">
                <Box>
                  <Text fontWeight="medium">X:</Text>
                  <Text>{Math.round(annotation.x)}</Text>
                </Box>
                <Box>
                  <Text fontWeight="medium">Y:</Text>
                  <Text>{Math.round(annotation.y)}</Text>
                </Box>
                <Box>
                  <Text fontWeight="medium">宽度:</Text>
                  <Text>{Math.round(annotation.width)}</Text>
                </Box>
                <Box>
                  <Text fontWeight="medium">高度:</Text>
                  <Text>{Math.round(annotation.height)}</Text>
                </Box>
              </HStack>
            </Box>

            {/* 提示信息 */}
            <Box p={2} bg="blue.50" borderRadius="md">
              <Text fontSize="xs" color="blue.700">
                {formData.type === 'field' && '💡 字段标注用于标识模板中的关键字段位置'}
                {formData.type === 'logo' && '💡 Logo标注用于标识发票上的Logo位置，用于模板匹配'}
                {formData.type === 'regex' && '💡 正则区域标注用于标识需要正则匹配的文本区域'}
              </Text>
            </Box>
          </VStack>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button colorScheme="blue" onClick={handleSave}>
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}

export default AnnotationDialog

