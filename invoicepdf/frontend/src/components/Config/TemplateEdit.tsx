import { Box, Text, Flex, VStack, HStack, Input, Badge, IconButton, Divider, Textarea, Collapse, useDisclosure } from "@chakra-ui/react"
import { FiSave, FiX, FiPlus, FiTrash2, FiEdit2, FiEye, FiChevronDown, FiChevronUp, FiFileText } from "react-icons/fi"
import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { ColDef, GridReadyEvent } from 'ag-grid-community'

interface TemplateField {
  id?: string
  field_key: string
  field_name: string
  data_type: string
  is_required: boolean
  description?: string
  example?: string
  validation?: any
  normalize?: any
  prompt_hint?: string
  confidence_threshold?: number
  sort_order?: number
  parent_field_id?: string
}

interface Template {
  id: string
  name: string
  template_type: string
  description?: string
  status: string
  current_version?: string
  accuracy?: number
  create_time?: string
  update_time?: string
}

interface TemplateDetail {
  id: string
  name: string
  template_type: string
  description?: string
  status: string
  accuracy?: number
  version: {
    id: string
    version: string
    status: string
    schema_snapshot?: any
    created_at?: string
    published_at?: string
  }
  fields: TemplateField[]
  create_time?: string
  update_time?: string
}

const TemplateEdit = ({ templateId }: { templateId?: string }) => {
  const [template, setTemplate] = useState<TemplateDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [isNew, setIsNew] = useState(!templateId)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // 表单数据
  const [formData, setFormData] = useState({
    name: '',
    template_type: '其他',
    description: ''
  })

  // 字段列表
  const [fields, setFields] = useState<TemplateField[]>([])
  const gridRef = useRef<AgGridReact>(null)
  
  // 提示词填充功能（新建模板时默认展开）
  const { isOpen: isPromptOpen, onToggle: onPromptToggle } = useDisclosure({ defaultIsOpen: isNew })
  const [promptTemplate, setPromptTemplate] = useState('')
  const [promptPreview, setPromptPreview] = useState('')

  // 数据类型选项
  const dataTypeOptions = [
    { value: 'string', label: '字符串' },
    { value: 'number', label: '数字' },
    { value: 'date', label: '日期' },
    { value: 'datetime', label: '日期时间' },
    { value: 'boolean', label: '布尔值' },
    { value: 'enum', label: '枚举' },
    { value: 'object', label: '对象' },
    { value: 'array', label: '数组' }
  ]

  // AG Grid 列定义
  const columnDefs: ColDef[] = [
    {
      headerName: '字段标识',
      field: 'field_key',
      width: 150,
      editable: true,
      cellEditor: 'agTextCellEditor'
    },
    {
      headerName: '字段名称',
      field: 'field_name',
      width: 200,
      editable: true,
      cellEditor: 'agTextCellEditor'
    },
    {
      headerName: '数据类型',
      field: 'data_type',
      width: 120,
      editable: true,
      cellEditor: 'agSelectCellEditor',
      cellEditorParams: {
        values: dataTypeOptions.map(opt => opt.value)
      },
      cellRenderer: (params: any) => {
        const option = dataTypeOptions.find(opt => opt.value === params.value)
        return option ? option.label : params.value
      }
    },
    {
      headerName: '必填',
      field: 'is_required',
      width: 80,
      editable: true,
      cellEditor: 'agCheckboxCellEditor',
      cellRenderer: (params: any) => {
        return params.value ? (
          <Badge colorScheme="red">是</Badge>
        ) : (
          <Badge colorScheme="gray">否</Badge>
        )
      }
    },
    {
      headerName: '描述',
      field: 'description',
      width: 200,
      editable: true,
      cellEditor: 'agTextCellEditor'
    },
    {
      headerName: '示例值',
      field: 'example',
      width: 150,
      editable: true,
      cellEditor: 'agTextCellEditor'
    },
    {
      headerName: '提示词',
      field: 'prompt_hint',
      width: 200,
      editable: true,
      cellEditor: 'agTextCellEditor',
      cellRenderer: (params: any) => {
        return params.value ? (
          <Text fontSize="sm" color="blue.600" title={params.value}>
            {params.value.length > 20 ? params.value.substring(0, 20) + '...' : params.value}
          </Text>
        ) : (
          <Text fontSize="sm" color="gray.400">未设置</Text>
        )
      }
    },
    {
      headerName: '操作',
      field: 'actions',
      width: 100,
      cellRenderer: (params: any) => {
        return (
          <HStack spacing={1}>
            <IconButton
              aria-label="删除"
              icon={<FiTrash2 />}
              size="xs"
              colorScheme="red"
              variant="ghost"
              onClick={() => handleDeleteField(params.data)}
            />
          </HStack>
        )
      }
    }
  ]

  // 加载模板详情
  const loadTemplate = async () => {
    if (!templateId) return

    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`/api/v1/templates/${templateId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      if (response.data) {
        const data = response.data
        setTemplate(data)
        setFormData({
          name: data.name || '',
          template_type: data.template_type || '其他',
          description: data.description || ''
        })
        setFields(data.fields || [])
      }
    } catch (error: any) {
      console.error('加载模板详情失败:', error)
      showErrorToast(error.response?.data?.detail || '加载模板详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (templateId) {
      loadTemplate()
    }
  }, [templateId])

  // 处理保存
  const handleSave = async () => {
    if (!formData.name.trim()) {
      showErrorToast('请输入模板名称')
      return
    }

    try {
      setSaving(true)
      const token = localStorage.getItem('access_token')

      if (isNew) {
        // 创建新模板
        const response = await axios.post('/api/v1/templates', formData, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        if (response.data?.data?.template_id) {
          showSuccessToast('模板创建成功')
          // 刷新页面或跳转
          window.location.reload()
        }
      } else if (templateId) {
        // 更新模板（包含字段信息）
        const updateData = {
          ...formData,
          fields: fields.map(f => ({
            id: f.id,
            field_key: f.field_key,
            field_name: f.field_name,
            data_type: f.data_type,
            is_required: f.is_required,
            description: f.description,
            example: f.example,
            validation: f.validation,
            normalize: f.normalize,
            prompt_hint: f.prompt_hint,
            confidence_threshold: f.confidence_threshold,
            sort_order: f.sort_order,
            parent_field_id: f.parent_field_id
          }))
        }
        await axios.put(`/api/v1/templates/${templateId}`, updateData, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        showSuccessToast('模板更新成功')
        loadTemplate()
      }
    } catch (error: any) {
      console.error('保存失败:', error)
      showErrorToast(error.response?.data?.detail || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  // 处理添加字段
  const handleAddField = () => {
    const newField: TemplateField = {
      field_key: `field_${fields.length + 1}`,
      field_name: '',
      data_type: 'string',
      is_required: false,
      sort_order: fields.length
    }
    setFields([...fields, newField])
  }

  // 处理删除字段
  const handleDeleteField = (field: TemplateField) => {
    if (confirm('确定要删除此字段吗？')) {
      setFields(fields.filter(f => f.id !== field.id || f.field_key !== field.field_key))
    }
  }

  // 处理单元格值变化
  const onCellValueChanged = (params: any) => {
    const updatedFields = fields.map(field => {
      if (field.id === params.data.id || field.field_key === params.data.field_key) {
        return { ...field, [params.colDef.field]: params.newValue }
      }
      return field
    })
    setFields(updatedFields)
  }

  if (loading) {
    return (
      <Box p={6} textAlign="center">
        <Text>加载中...</Text>
      </Box>
    )
  }

  return (
    <Box p={6} h="100vh" display="flex" flexDirection="column" overflow="auto">
      {/* 标题栏 */}
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">
          {isNew ? '新建模板' : `编辑模板: ${template?.name || ''}`}
        </Text>
        <HStack spacing={2}>
          <Button
            onClick={handleSave}
            leftIcon={<FiSave />}
            colorScheme="blue"
            isLoading={saving}
          >
            保存
          </Button>
          <Button
            onClick={() => {
              // Tab id 由 layout 生成：template-edit-${templateId || 'new'}
              const tabId = `template-edit-${templateId || 'new'}`
              const event = new CustomEvent('closeTab', { detail: { tabId } })
              window.dispatchEvent(event)
            }}
            leftIcon={<FiX />}
            variant="outline"
          >
            关闭
          </Button>
        </HStack>
      </Flex>

      {/* 模板基本信息 */}
      <Box bg="white" p={6} borderRadius="md" border="1px" borderColor="gray.200" mb={4}>
        <VStack spacing={4} align="stretch">
          <Field label="模板名称" required>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="请输入模板名称"
            />
          </Field>

          <Field label="模板类型" required>
            <select
              value={formData.template_type}
              onChange={(e) => setFormData({ ...formData, template_type: e.target.value })}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #e2e8f0',
                borderRadius: '4px'
              }}
            >
              <option value="增值税发票">增值税发票</option>
              <option value="普通发票">普通发票</option>
              <option value="采购订单">采购订单</option>
              <option value="收据">收据</option>
              <option value="出库单">出库单</option>
              <option value="入库单">入库单</option>
              <option value="其他">其他</option>
            </select>
          </Field>

          <Field label="模板描述">
            <Input
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="请输入模板描述（可选）"
            />
          </Field>

          {template && (
            <HStack spacing={4}>
              <Text fontSize="sm" color="gray.600">
                状态: <Badge colorScheme="green">{template.status}</Badge>
              </Text>
              <Text fontSize="sm" color="gray.600">
                版本: <Badge colorScheme="blue">{template.version?.version || '无'}</Badge>
              </Text>
              {template.accuracy !== null && template.accuracy !== undefined && (
                <Text fontSize="sm" color="gray.600">
                  准确率: <Badge colorScheme="orange">{(template.accuracy * 100).toFixed(1)}%</Badge>
                </Text>
              )}
            </HStack>
          )}
        </VStack>
      </Box>

      {/* 提示词填充功能模块 */}
      <Box bg="white" p={6} borderRadius="md" border="1px" borderColor="gray.200" mb={4}>
        <Flex justify="space-between" align="center" mb={4}>
          <HStack spacing={2}>
            <IconButton
              aria-label={isPromptOpen ? "收起" : "展开"}
              icon={isPromptOpen ? <FiChevronUp /> : <FiChevronDown />}
              size="sm"
              variant="ghost"
              onClick={onPromptToggle}
            />
            <Text fontSize="lg" fontWeight="medium">
              提示词填充功能
            </Text>
            <Badge colorScheme="blue" fontSize="xs">批量配置</Badge>
          </HStack>
        </Flex>
        
        <Collapse in={isPromptOpen} animateOpacity>
          <VStack spacing={4} align="stretch">
            <Field label="提示词模板">
              <Textarea
                value={promptTemplate}
                onChange={(e) => setPromptTemplate(e.target.value)}
                placeholder="输入提示词模板，使用 {field_name} 和 {field_key} 作为占位符&#10;例如：请提取{field_name}字段，字段标识为{field_key}，数据类型为{data_type}"
                rows={4}
                fontSize="sm"
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                提示：使用 {'{field_name}'} 表示字段名称，{'{field_key}'} 表示字段标识，{'{data_type}'} 表示数据类型
              </Text>
            </Field>
            
            <HStack spacing={2}>
              <Button
                size="sm"
                colorScheme="blue"
                onClick={() => {
                  if (!promptTemplate.trim()) {
                    showErrorToast('请输入提示词模板')
                    return
                  }
                  
                  // 批量填充提示词
                  const updatedFields = fields.map(field => {
                    if (!field.prompt_hint) {
                      let hint = promptTemplate
                      hint = hint.replace(/{field_name}/g, field.field_name || '')
                      hint = hint.replace(/{field_key}/g, field.field_key || '')
                      hint = hint.replace(/{data_type}/g, field.data_type || '')
                      return { ...field, prompt_hint: hint }
                    }
                    return field
                  })
                  setFields(updatedFields)
                  showSuccessToast(`已为 ${updatedFields.filter(f => f.prompt_hint).length} 个字段填充提示词`)
                }}
              >
                批量填充提示词
              </Button>
              
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // 预览生成的提示词
                  if (!promptTemplate.trim()) {
                    showErrorToast('请输入提示词模板')
                    return
                  }
                  
                  const preview = fields.map(field => {
                    let hint = promptTemplate
                    hint = hint.replace(/{field_name}/g, field.field_name || '')
                    hint = hint.replace(/{field_key}/g, field.field_key || '')
                    hint = hint.replace(/{data_type}/g, field.data_type || '')
                    return `【${field.field_name || field.field_key}】: ${hint}`
                  }).join('\n\n')
                  
                  setPromptPreview(preview)
                }}
              >
                预览提示词
              </Button>
              
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // 清空所有提示词
                  if (confirm('确定要清空所有字段的提示词吗？')) {
                    const updatedFields = fields.map(field => ({ ...field, prompt_hint: '' }))
                    setFields(updatedFields)
                    showSuccessToast('已清空所有提示词')
                  }
                }}
              >
                清空所有提示词
              </Button>
            </HStack>
            
            {promptPreview && (
              <Box p={4} bg="gray.50" borderRadius="md" border="1px" borderColor="gray.200">
                <Flex justify="space-between" align="center" mb={2}>
                  <Text fontSize="sm" fontWeight="medium">提示词预览</Text>
                  <IconButton
                    aria-label="关闭预览"
                    icon={<FiX />}
                    size="xs"
                    variant="ghost"
                    onClick={() => setPromptPreview('')}
                  />
                </Flex>
                <Textarea
                  value={promptPreview}
                  readOnly
                  rows={8}
                  fontSize="xs"
                  fontFamily="mono"
                  bg="white"
                />
              </Box>
            )}
            
            {/* 常用提示词模板 */}
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={2}>常用提示词模板：</Text>
              <HStack spacing={2} flexWrap="wrap">
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => setPromptTemplate('请准确提取{field_name}字段')}
                >
                  基础提取
                </Button>
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => setPromptTemplate('请从文档中提取{field_name}（字段标识：{field_key}），数据类型为{data_type}')}
                >
                  详细提取
                </Button>
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => setPromptTemplate('请识别并提取{field_name}字段，确保数据准确无误')}
                >
                  强调准确
                </Button>
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => setPromptTemplate('{field_name}：请仔细识别此字段，如果文档中没有该信息，请留空')}
                >
                  允许为空
                </Button>
              </HStack>
            </Box>
          </VStack>
        </Collapse>
      </Box>

      {/* 字段配置 */}
      <Box flex="1" display="flex" flexDirection="column" bg="white" p={6} borderRadius="md" border="1px" borderColor="gray.200">
        <Flex justify="space-between" align="center" mb={4}>
          <Text fontSize="lg" fontWeight="medium">
            字段配置 ({fields.length})
          </Text>
          <Button
            onClick={handleAddField}
            leftIcon={<FiPlus />}
            size="sm"
            colorScheme="blue"
          >
            添加字段
          </Button>
        </Flex>

        <Box flex="1" minH="0" overflow="hidden" className="ag-theme-alpine" style={{ height: '100%', width: '100%' }}>
          <AgGridReact
            theme="legacy"
            ref={gridRef}
            rowData={fields}
            columnDefs={columnDefs}
            onCellValueChanged={onCellValueChanged}
            onGridReady={(params: GridReadyEvent) => {
              params.api.sizeColumnsToFit()
            }}
            defaultColDef={{
              resizable: true,
              sortable: true
            }}
            animateRows={true}
            rowHeight={40}
          />
        </Box>
      </Box>
    </Box>
  )
}

export default TemplateEdit

