import { Box, Text, Flex, VStack, HStack, Input, Badge, IconButton, Grid, GridItem, Textarea } from "@chakra-ui/react"
import { FiSave, FiX, FiPlus, FiTrash2, FiEdit2, FiEye, FiUpload, FiImage, FiFile, FiLink } from "react-icons/fi"
import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'

interface SchemaOption {
  id: string
  name: string
  version: string
  is_active: boolean
  description?: string
}

interface MatchingRule {
  logo?: {
    image_path?: string
    position?: { x: number, y: number, width: number, height: number }
    similarity_threshold: number
  }
  key_fields?: Array<{
    field_name: string
    position: { x: number, y: number, width: number, height: number }
    format_pattern?: string
  }>
  regex_rules?: Array<{
    name: string
    pattern: string
    position?: { x: number, y: number, width: number, height: number }
    priority: number
  }>
  matching_strategy: 'all' | 'any' | 'weighted'
  match_threshold: number
}

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

interface TemplateDetail {
  id: string
  name: string
  template_type: string
  description?: string
  status: string
  schema_id?: string
  schema_name?: string
  schema_version?: string
  sample_file_path?: string
  sample_file_type?: string
  matching_rules?: MatchingRule
  accuracy?: number
  prompt?: string  // 添加 prompt 字段
  version?: {
    id: string
    version: string
    status: string
  }
  fields?: TemplateField[]
  create_time?: string
  update_time?: string
}

const TemplateEditEnhanced = ({ templateId }: { templateId?: string }) => {
  const [template, setTemplate] = useState<TemplateDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [isNew, setIsNew] = useState(!templateId)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Schema 列表
  const [schemas, setSchemas] = useState<SchemaOption[]>([])
  const [selectedSchemaId, setSelectedSchemaId] = useState<string>('')

  // 表单数据
  const [formData, setFormData] = useState({
    name: '',
    template_type: '其他',
    description: '',
    status: 'disabled' as 'enabled' | 'disabled'
  })

  // 示例文件
  const [sampleFile, setSampleFile] = useState<File | null>(null)
  const [sampleFilePreview, setSampleFilePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 匹配规则（暂时隐藏）
  const [matchingRules, setMatchingRules] = useState<MatchingRule>({
    matching_strategy: 'any',
    match_threshold: 0.7,
    similarity_threshold: 0.8
  })
  
  // 提示词
  const [templatePrompt, setTemplatePrompt] = useState<string>('')

  // 标注数据
  const [annotations, setAnnotations] = useState<Annotation[]>([])

  // 字段列表
  const [fields, setFields] = useState<TemplateField[]>([])

  // 加载 Schema 列表
  const loadSchemas = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get('/api/v1/config/schemas', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        params: { is_active: true }
      })
      if (response.data && response.data.data) {
        setSchemas(response.data.data)
      }
    } catch (error: any) {
      console.error('加载Schema列表失败:', error)
    }
  }

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
        console.log('加载模板数据:', data)
        console.log('模板提示词字段值:', data.prompt)
        setTemplate(data)
        setFormData({
          name: data.name || '',
          template_type: data.template_type || '其他',
          description: data.description || '',
          status: data.status || 'disabled'
        })
        setSelectedSchemaId(data.schema_id || '')
        setMatchingRules(data.matching_rules || {
          matching_strategy: 'any',
          match_threshold: 0.7,
          similarity_threshold: 0.8
        })
        // 设置提示词（确保正确处理 null/undefined）
        console.log('原始data.prompt值:', data.prompt, '类型:', typeof data.prompt)
        const promptValue = (data.prompt !== null && data.prompt !== undefined && data.prompt !== '') 
            ? String(data.prompt) 
            : ''
        console.log('处理后的promptValue:', promptValue)
        setTemplatePrompt(promptValue)
        console.log('设置模板提示词到状态:', promptValue)
        
        // 使用useEffect确保状态更新后再次检查
        setTimeout(() => {
          console.log('延迟检查templatePrompt状态:', templatePrompt)
        }, 100)
        
        // 加载字段列表
        setFields(data.fields || [])
        
        // 加载示例文件预览
        if (data.sample_file_path) {
          // TODO: 从服务器加载文件预览
          setSampleFilePreview(data.sample_file_path)
        }
      }
    } catch (error: any) {
      console.error('加载模板详情失败:', error)
      showErrorToast(error.response?.data?.detail || '加载模板详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSchemas()
    if (templateId) {
      loadTemplate()
    }
  }, [templateId])

  // 处理文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 验证文件类型
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
    if (!allowedTypes.includes(file.type)) {
      showErrorToast('仅支持 PDF、JPG、PNG 格式')
      return
    }

    // 验证文件大小（10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorToast('文件大小不能超过 10MB')
      return
    }

    setSampleFile(file)

    // 生成预览
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setSampleFilePreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    } else if (file.type === 'application/pdf') {
      // PDF 预览需要特殊处理
      setSampleFilePreview(URL.createObjectURL(file))
    }
  }

  // 处理保存
  const handleSave = async () => {
    if (!formData.name.trim()) {
      showErrorToast('请输入模板名称')
      return
    }

    try {
      setSaving(true)
      const token = localStorage.getItem('access_token')

      // 构建请求数据
      const requestData: any = {
        ...formData,
        schema_id: selectedSchemaId || undefined,
        prompt: templatePrompt !== null && templatePrompt !== undefined ? templatePrompt : '', // 确保总是发送prompt字段
        // matching_rules: matchingRules // 暂时隐藏匹配规则功能
      }
      console.log('保存模板，完整请求数据:', JSON.stringify(requestData, null, 2))
      console.log('保存模板，提示词内容:', requestData.prompt)
      console.log('保存模板，提示词类型:', typeof requestData.prompt)
      console.log('保存模板，提示词长度:', requestData.prompt ? requestData.prompt.length : 0)

      // 如果有示例文件，需要上传
      if (sampleFile) {
        const formDataObj = new FormData()
        formDataObj.append('file', sampleFile)
        formDataObj.append('data', JSON.stringify(requestData))
        
        // TODO: 实现文件上传API
        showErrorToast('文件上传功能开发中')
        return
      }

      if (isNew) {
        // 创建新模板
        const response = await axios.post('/api/v1/templates', requestData, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        if (response.data?.data?.template_id) {
          showSuccessToast('模板创建成功')
          // 触发刷新事件
          window.dispatchEvent(new Event('refreshTemplateList'))
          // 关闭当前tab
          const event = new CustomEvent('closeTab', { detail: { tabId: `template-edit-${templateId || 'new'}` } })
          window.dispatchEvent(event)
        }
      } else if (templateId) {
        // 更新模板基本信息
        console.log('发送PUT请求到:', `/api/v1/templates/${templateId}`)
        const response = await axios.put(`/api/v1/templates/${templateId}`, requestData, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        console.log('PUT请求响应:', response.data)
        
        // 如果有字段变更，需要更新字段（通过版本字段更新接口）
        if (template?.version?.id && fields.length > 0) {
          // TODO: 实现字段更新API
          // 目前先只更新基本信息
        }
        
        showSuccessToast('模板更新成功')
        // 等待一下再重新加载，确保数据库已更新
        setTimeout(() => {
          loadTemplate()
        }, 500)
      }
    } catch (error: any) {
      console.error('保存失败:', error)
      showErrorToast(error.response?.data?.detail || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  // 添加 Logo 规则
  const handleAddLogoRule = () => {
    setMatchingRules({
      ...matchingRules,
      logo: {
        similarity_threshold: 0.8
      }
    })
  }

  // 添加关键字段规则
  const handleAddKeyFieldRule = () => {
    const newField = {
      field_name: '',
      position: { x: 0, y: 0, width: 100, height: 30 },
      format_pattern: ''
    }
    setMatchingRules({
      ...matchingRules,
      key_fields: [...(matchingRules.key_fields || []), newField]
    })
  }

  // 添加正则规则
  const handleAddRegexRule = () => {
    const newRule = {
      name: '',
      pattern: '',
      priority: matchingRules.regex_rules?.length || 0
    }
    setMatchingRules({
      ...matchingRules,
      regex_rules: [...(matchingRules.regex_rules || []), newRule]
    })
  }

  // 删除规则
  const handleDeleteKeyField = (index: number) => {
    const newFields = matchingRules.key_fields?.filter((_, i) => i !== index) || []
    setMatchingRules({
      ...matchingRules,
      key_fields: newFields.length > 0 ? newFields : undefined
    })
  }

  const handleDeleteRegexRule = (index: number) => {
    const newRules = matchingRules.regex_rules?.filter((_, i) => i !== index) || []
    setMatchingRules({
      ...matchingRules,
      regex_rules: newRules.length > 0 ? newRules : undefined
    })
  }

  // 添加字段
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

  // 删除字段
  const handleDeleteField = (index: number) => {
    if (confirm('确定要删除此字段吗？')) {
      setFields(fields.filter((_, i) => i !== index))
    }
  }

  // 更新字段
  const handleFieldChange = (index: number, field: Partial<TemplateField>) => {
    const updatedFields = fields.map((f, i) => 
      i === index ? { ...f, ...field } : f
    )
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
    <Box p={6} h="100vh" display="flex" flexDirection="column" overflow="auto" bg="gray.50">
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
              const event = new CustomEvent('closeTab', { detail: { tabId: `template-edit-${templateId || 'new'}` } })
              window.dispatchEvent(event)
            }}
            leftIcon={<FiX />}
            variant="outline"
          >
            关闭
          </Button>
        </HStack>
      </Flex>

      {/* 主要内容区域 - 左右分栏 */}
      <Grid templateColumns={{ base: "1fr", lg: "300px 1fr" }} gap={4} flex="1">
        {/* 左侧：模板基本信息 */}
        <GridItem>
          <VStack spacing={4} align="stretch">
            {/* 模板基本信息 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Text fontSize="lg" fontWeight="medium" mb={4}>基本信息</Text>
              <VStack spacing={4} align="stretch">
                <Field label="模板名称" required>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="请输入模板名称"
                  />
                </Field>

                <Field label="单据类型" required>
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
                    <option value="其他">其他</option>
                  </select>
                </Field>

                <Field label="描述">
                  <Input
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="请输入模板描述（可选）"
                  />
                </Field>

                <Field label="状态">
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value as 'enabled' | 'disabled' })}
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #e2e8f0',
                      borderRadius: '4px'
                    }}
                  >
                    <option value="enabled">启用</option>
                    <option value="disabled">停用</option>
                  </select>
                </Field>
              </VStack>
            </Box>

            {/* Schema 绑定 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Text fontSize="lg" fontWeight="medium" mb={4}>绑定 Schema</Text>
              <Field label="选择 Schema">
                <select
                  value={selectedSchemaId}
                  onChange={(e) => setSelectedSchemaId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '4px'
                  }}
                >
                  <option value="">未绑定</option>
                  {schemas.map(schema => (
                    <option key={schema.id} value={schema.id}>
                      {schema.name} (v{schema.version})
                    </option>
                  ))}
                </select>
              </Field>
              {selectedSchemaId && (
                <Box mt={2} p={2} bg="blue.50" borderRadius="md">
                  <Text fontSize="sm" color="blue.700">
                    {schemas.find(s => s.id === selectedSchemaId)?.description || '已绑定 Schema'}
                  </Text>
                </Box>
              )}
            </Box>

            {/* 示例文件上传 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Text fontSize="lg" fontWeight="medium" mb={4}>示例文件</Text>
              <VStack spacing={3} align="stretch">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  leftIcon={<FiUpload />}
                  variant="outline"
                  size="sm"
                >
                  上传示例文件
                </Button>
                {sampleFile && (
                  <Box p={2} bg="gray.50" borderRadius="md">
                    <HStack spacing={2}>
                      <FiFile />
                      <Text fontSize="sm" flex="1" isTruncated>{sampleFile.name}</Text>
                      <Text fontSize="xs" color="gray.500">
                        {(sampleFile.size / 1024 / 1024).toFixed(2)} MB
                      </Text>
                    </HStack>
                  </Box>
                )}
                {template?.sample_file_path && !sampleFile && (
                  <Box p={2} bg="gray.50" borderRadius="md">
                    <HStack spacing={2}>
                      <FiFile />
                      <Text fontSize="sm" flex="1" isTruncated>
                        {template.sample_file_path.split('/').pop()}
                      </Text>
                    </HStack>
                  </Box>
                )}
              </VStack>
            </Box>

            {/* 字段管理 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Flex justify="space-between" align="center" mb={4}>
                <Text fontSize="lg" fontWeight="medium">字段管理 ({fields.length})</Text>
                <Button
                  onClick={handleAddField}
                  leftIcon={<FiPlus />}
                  size="sm"
                  colorScheme="blue"
                >
                  添加字段
                </Button>
              </Flex>
              <VStack spacing={2} align="stretch" maxH="400px" overflowY="auto">
                {fields.length === 0 ? (
                  <Box p={4} textAlign="center" color="gray.500">
                    <Text>暂无字段，点击"添加字段"开始配置</Text>
                  </Box>
                ) : (
                  fields.map((field, index) => (
                    <Box key={index} p={3} bg="gray.50" borderRadius="md" border="1px" borderColor="gray.200">
                      <Flex justify="space-between" align="start" mb={2}>
                        <Text fontSize="sm" fontWeight="medium">字段 {index + 1}</Text>
                        <IconButton
                          aria-label="删除"
                          icon={<FiTrash2 />}
                          size="xs"
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => handleDeleteField(index)}
                        />
                      </Flex>
                      <Grid templateColumns="1fr 1fr" gap={2}>
                        <Field label="字段标识">
                          <Input
                            size="sm"
                            value={field.field_key}
                            onChange={(e) => handleFieldChange(index, { field_key: e.target.value })}
                            placeholder="如：invoice_no"
                          />
                        </Field>
                        <Field label="字段名称">
                          <Input
                            size="sm"
                            value={field.field_name}
                            onChange={(e) => handleFieldChange(index, { field_name: e.target.value })}
                            placeholder="如：发票号码"
                          />
                        </Field>
                        <Field label="数据类型">
                          <select
                            value={field.data_type}
                            onChange={(e) => handleFieldChange(index, { data_type: e.target.value })}
                            style={{
                              width: '100%',
                              padding: '6px',
                              border: '1px solid #e2e8f0',
                              borderRadius: '4px',
                              fontSize: '14px'
                            }}
                          >
                            <option value="string">字符串</option>
                            <option value="number">数字</option>
                            <option value="date">日期</option>
                            <option value="datetime">日期时间</option>
                            <option value="boolean">布尔值</option>
                            <option value="enum">枚举</option>
                            <option value="object">对象</option>
                            <option value="array">数组</option>
                          </select>
                        </Field>
                        <Field label="必填">
                          <select
                            value={field.is_required ? 'true' : 'false'}
                            onChange={(e) => handleFieldChange(index, { is_required: e.target.value === 'true' })}
                            style={{
                              width: '100%',
                              padding: '6px',
                              border: '1px solid #e2e8f0',
                              borderRadius: '4px',
                              fontSize: '14px'
                            }}
                          >
                            <option value="false">否</option>
                            <option value="true">是</option>
                          </select>
                        </Field>
                        <Field label="描述">
                          <Input
                            size="sm"
                            value={field.description || ''}
                            onChange={(e) => handleFieldChange(index, { description: e.target.value })}
                            placeholder="字段描述（可选）"
                          />
                        </Field>
                        <Field label="示例值">
                          <Input
                            size="sm"
                            value={field.example || ''}
                            onChange={(e) => handleFieldChange(index, { example: e.target.value })}
                            placeholder="示例值（可选）"
                          />
                        </Field>
                      </Grid>
                    </Box>
                  ))
                )}
              </VStack>
            </Box>
          </VStack>
        </GridItem>

        {/* 右侧：预览和匹配规则 */}
        <GridItem>
          <VStack spacing={4} align="stretch">
            {/* 发票预览区域 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Text fontSize="lg" fontWeight="medium" mb={4}>发票预览与标注</Text>
              {sampleFilePreview ? (
                <Box>
                  {sampleFilePreview.includes('data:image') || sampleFilePreview.startsWith('blob:') ? (
                    <ImageAnnotator
                      imageUrl={sampleFilePreview}
                      annotations={annotations}
                      onAnnotationChange={(newAnnotations) => {
                        setAnnotations(newAnnotations)
                        // 更新匹配规则中的位置信息
                        const updatedRules = { ...matchingRules }
                        if (updatedRules.key_fields) {
                          updatedRules.key_fields = updatedRules.key_fields.map((field, index) => {
                            const annotation = newAnnotations.find(a => a.type === 'field' && a.label === field.field_name)
                            if (annotation) {
                              return {
                                ...field,
                                position: {
                                  x: annotation.x,
                                  y: annotation.y,
                                  width: annotation.width,
                                  height: annotation.height
                                }
                              }
                            }
                            return field
                          })
                        }
                        setMatchingRules(updatedRules)
                      }}
                      onAnnotationAdd={(annotation) => {
                        const newAnnotations = [...annotations, annotation]
                        setAnnotations(newAnnotations)
                        // 如果是字段标注，添加到关键字段规则
                        if (annotation.type === 'field') {
                          const newField = {
                            field_name: annotation.label || `字段${matchingRules.key_fields?.length || 0 + 1}`,
                            position: {
                              x: annotation.x,
                              y: annotation.y,
                              width: annotation.width,
                              height: annotation.height
                            },
                            format_pattern: ''
                          }
                          setMatchingRules({
                            ...matchingRules,
                            key_fields: [...(matchingRules.key_fields || []), newField]
                          })
                        }
                      }}
                      onAnnotationDelete={(id) => {
                        const newAnnotations = annotations.filter(a => a.id !== id)
                        setAnnotations(newAnnotations)
                      }}
                      editable={true}
                    />
                  ) : (
                    <Box
                      border="2px dashed"
                      borderColor="gray.300"
                      borderRadius="md"
                      p={8}
                      textAlign="center"
                      bg="gray.50"
                    >
                      <FiFile size={48} color="#718096" />
                      <Text color="gray.500" mt={2}>PDF 预览功能开发中</Text>
                      <Text fontSize="sm" color="gray.400" mt={1}>{sampleFile?.name}</Text>
                    </Box>
                  )}
                </Box>
              ) : (
                <Box
                  border="2px dashed"
                  borderColor="gray.300"
                  borderRadius="md"
                  p={8}
                  textAlign="center"
                  bg="gray.50"
                >
                  <FiImage size={48} color="#CBD5E0" style={{ margin: '0 auto 16px' }} />
                  <Text color="gray.500">请上传示例文件以预览</Text>
                  <Text fontSize="xs" color="gray.400" mt={2}>
                    支持 PDF、JPG、PNG 格式，单文件最大 10MB
                  </Text>
                </Box>
              )}
            </Box>

            {/* 提示词配置 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Text fontSize="lg" fontWeight="medium" mb={4}>请输入提示词</Text>
              <VStack spacing={4} align="stretch">
                <Field label="">
                  <Textarea
                    value={templatePrompt || ''}
                    onChange={(e) => {
                      console.log('Textarea onChange, 新值:', e.target.value)
                      setTemplatePrompt(e.target.value)
                    }}
                    placeholder="请输入提示词，用于指导AI识别和提取文档中的信息..."
                    rows={8}
                    fontSize="sm"
                    resize="vertical"
                  />
                  <Text fontSize="xs" color="gray.400" mt={1}>
                    当前值长度: {templatePrompt?.length || 0} 字符
                  </Text>
                  <Text fontSize="xs" color="gray.500" mt={2}>
                    提示：提示词将用于指导AI模型识别和提取文档中的关键信息，请详细描述需要提取的字段和要求
                  </Text>
                </Field>
              </VStack>
            </Box>
          </VStack>
        </GridItem>
      </Grid>
    </Box>
  )
}

export default TemplateEditEnhanced

