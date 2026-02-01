import { Box, Text, Flex, VStack, HStack, Input, Badge, IconButton, Grid, Textarea, Table } from "@chakra-ui/react"
import { FiSave, FiX, FiPlus, FiTrash2, FiEdit2, FiLink, FiCheckCircle, FiChevronDown, FiChevronUp, FiUpload, FiDownload, FiMinus } from "react-icons/fi"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'
import * as XLSX from 'xlsx'

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
  data_name?: string  // 数据名称（新增）
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


  // 匹配规则（暂时隐藏）
  const [matchingRules, setMatchingRules] = useState<MatchingRule>({
    matching_strategy: 'any',
    match_threshold: 0.7,
    similarity_threshold: 0.8
  })
  
  // 提示词
  const [templatePrompt, setTemplatePrompt] = useState<string>('')
  
  // Schema JSON（新增）
  const [templateSchema, setTemplateSchema] = useState<string>('')
  const [schemaValidationResult, setSchemaValidationResult] = useState<{
    valid: boolean
    message: string
    errors?: any[]
  } | null>(null)

  // 字段列表
  const [fields, setFields] = useState<TemplateField[]>([])
  
  // 字段表格展开/收起
  const [isFieldsExpanded, setIsFieldsExpanded] = useState(false)
  const onFieldsToggle = () => {
    setIsFieldsExpanded(prev => !prev)
  }
  
  // 新添加的字段ID列表（用于红色高亮显示）
  const [newFieldIds, setNewFieldIds] = useState<Set<string>>(new Set())
  
  // AI建议提示词
  const [aiSuggestedPrompt, setAiSuggestedPrompt] = useState<string>('')
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false)
  const [lastGeneratedPrompt, setLastGeneratedPrompt] = useState<string>('')
  const [generationProgress, setGenerationProgress] = useState<{
    step: string
    percentage: number
  } | null>(null)

  // 加载 Schema 列表（已注释，不再使用）
  // const loadSchemas = async () => {
  //   try {
  //     const token = localStorage.getItem('access_token')
  //     const response = await axios.get('/api/v1/config/schemas', {
  //       headers: token ? { Authorization: `Bearer ${token}` } : {},
  //       params: { is_active: true }
  //     })
  //     if (response.data && response.data.data) {
  //       setSchemas(response.data.data)
  //     }
  //   } catch (error: any) {
  //     console.error('加载Schema列表失败:', error)
  //   }
  // }

  // JSON Schema 校验函数
  const validateJsonSchema = async () => {
    if (!templateSchema || !templateSchema.trim()) {
      showErrorToast('请先输入 Schema JSON')
      setSchemaValidationResult({
        valid: false,
        message: 'Schema 内容为空'
      })
      return
    }

    try {
      // 先验证 JSON 格式
      let parsedSchema: any
      try {
        parsedSchema = JSON.parse(templateSchema)
      } catch (e: any) {
        setSchemaValidationResult({
          valid: false,
          message: `JSON 格式错误: ${e.message}`
        })
        showErrorToast(`JSON 格式错误: ${e.message}`)
        return
      }

      // 调用后端 API 进行 JSON Schema 规范验证
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/config/schemas/validate`,
        { schema_definition: parsedSchema },
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )

      if (response.data) {
        const result = response.data
        setSchemaValidationResult({
          valid: result.valid || false,
          message: result.message || (result.valid ? 'Schema 格式验证通过' : 'Schema 格式验证失败'),
          errors: result.errors
        })

        if (result.valid) {
          showSuccessToast(result.message || 'Schema 格式验证通过')
        } else {
          showErrorToast(result.message || 'Schema 格式验证失败')
        }
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || '校验失败'
      setSchemaValidationResult({
        valid: false,
        message: errorMessage
      })
      showErrorToast(errorMessage)
    }
  }

  // 加载模板详情
  const loadTemplate = async () => {
    if (!templateId) return

    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await axios.get(`${apiBaseUrl}/api/v1/templates/${templateId}`, {
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
        // setSelectedSchemaId(data.schema_id || '') // 已注释，不再使用 Schema 绑定
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
        
        // 加载 Schema JSON（如果存在）
        const schemaValue = data.schema || ''
        setTemplateSchema(schemaValue ? (typeof schemaValue === 'string' ? schemaValue : JSON.stringify(schemaValue, null, 2)) : '')
        
        // 使用useEffect确保状态更新后再次检查
        setTimeout(() => {
          console.log('延迟检查templatePrompt状态:', templatePrompt)
        }, 100)
        
        // 加载字段列表
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
    // loadSchemas() // 已注释，不再加载 Schema 列表
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

      // 构建请求数据
      const requestData: any = {
        ...formData,
        // schema_id: selectedSchemaId || undefined, // 已注释，不再使用 Schema 绑定
        prompt: templatePrompt !== null && templatePrompt !== undefined ? templatePrompt : '', // 确保总是发送prompt字段
        schema: templateSchema && templateSchema.trim() ? (() => {
          try {
            return JSON.parse(templateSchema) // 解析为对象
          } catch {
            return templateSchema // 如果解析失败，保持字符串格式
          }
        })() : undefined, // 添加 schema 字段
        // matching_rules: matchingRules // 暂时隐藏匹配规则功能
        fields: fields.map((field, index) => ({
          field_key: field.field_key,
          field_name: field.field_name,
          data_name: field.data_name || field.field_key,
          data_type: field.data_type || 'string',
          is_required: field.is_required || false,
          description: field.description || '',
          example: field.example || '',
          validation: field.validation,
          normalize: field.normalize,
          prompt_hint: field.prompt_hint,
          confidence_threshold: field.confidence_threshold,
          sort_order: field.sort_order !== undefined ? field.sort_order : index,
          parent_field_id: field.parent_field_id
        })) // 添加字段数据
      }
      console.log('保存模板，完整请求数据:', JSON.stringify(requestData, null, 2))
      console.log('保存模板，提示词内容:', requestData.prompt)
      console.log('保存模板，提示词类型:', typeof requestData.prompt)
      console.log('保存模板，提示词长度:', requestData.prompt ? requestData.prompt.length : 0)

      if (isNew) {
        // 创建新模板
        const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const response = await axios.post(`${apiBaseUrl}/api/v1/templates`, requestData, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        if (response.data?.data?.template_id) {
          const newTemplateId = response.data.data.template_id
          showSuccessToast('模板创建成功')
          
          // 触发刷新事件
          window.dispatchEvent(new Event('refreshTemplateList'))
          // 关闭当前tab
          const event = new CustomEvent('closeTab', { detail: { tabId: `template-edit-${templateId || 'new'}` } })
          window.dispatchEvent(event)
        }
      } else if (templateId) {
        // 更新模板基本信息
        const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        console.log('发送PUT请求到:', `${apiBaseUrl}/api/v1/templates/${templateId}`)
        const response = await axios.put(`${apiBaseUrl}/api/v1/templates/${templateId}`, requestData, {
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
    const newFieldId = `new_field_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const newField: TemplateField = {
      id: newFieldId,
      field_key: `field_${fields.length + 1}`,
      field_name: '',
      data_name: '',
      data_type: 'string',
      is_required: false,
      sort_order: fields.length
    }
    setFields([...fields, newField])
    // 将新字段ID添加到新字段集合中
    setNewFieldIds(new Set([...newFieldIds, newFieldId]))
    // 自动展开以显示新添加的字段
    if (!isFieldsExpanded && fields.length >= 3) {
      onFieldsToggle()
    }
  }
  
  // 导入字段
  const handleImportFields = () => {
    // 创建文件输入元素
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json,.xlsx,.xls'
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0]
      if (!file) return
      
      const fileName = file.name.toLowerCase()
      const isExcel = fileName.endsWith('.xlsx') || fileName.endsWith('.xls')
      const isJson = fileName.endsWith('.json')
      
      try {
        let importedData: any[] = []
        
        if (isExcel) {
          // 读取 Excel 文件
          const reader = new FileReader()
          reader.onload = (event) => {
            try {
              const data = new Uint8Array(event.target?.result as ArrayBuffer)
              const workbook = XLSX.read(data, { type: 'array' })
              
              // 读取第一个工作表
              const firstSheetName = workbook.SheetNames[0]
              const worksheet = workbook.Sheets[firstSheetName]
              
              // 转换为 JSON
              const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
              
              if (jsonData.length < 2) {
                showErrorToast('Excel 文件格式错误：至少需要包含表头和数据行')
                return
              }
              
              // 第一行是表头
              const headers = jsonData[0] as string[]
              const headerMap: { [key: string]: string } = {}
              
              // 映射表头（支持中英文）
              headers.forEach((header, index) => {
                const h = String(header).trim()
                if (h.includes('字段标识') || h.includes('field_key') || h.includes('Field Key')) {
                  headerMap['field_key'] = String(index)
                } else if (h.includes('字段名称') || h.includes('field_name') || h.includes('Field Name')) {
                  headerMap['field_name'] = String(index)
                } else if (h.includes('数据名称') || h.includes('data_name') || h.includes('Data Name')) {
                  headerMap['data_name'] = String(index)
                } else if (h.includes('数据类型') || h.includes('data_type') || h.includes('Data Type')) {
                  headerMap['data_type'] = String(index)
                } else if (h.includes('是否必填') || h.includes('is_required') || h.includes('Required')) {
                  headerMap['is_required'] = String(index)
                } else if (h.includes('描述') || h.includes('description') || h.includes('Description')) {
                  headerMap['description'] = String(index)
                } else if (h.includes('示例值') || h.includes('example') || h.includes('Example')) {
                  headerMap['example'] = String(index)
                }
              })
              
              // 转换数据行
              importedData = jsonData.slice(1).map((row: any) => {
                const item: any = {}
                Object.keys(headerMap).forEach(key => {
                  const colIndex = parseInt(headerMap[key])
                  if (colIndex >= 0 && colIndex < row.length) {
                    item[key] = row[colIndex]
                  }
                })
                return item
              }).filter(item => item.field_key || item.field_name) // 过滤空行
              
            } catch (error: any) {
              console.error('读取 Excel 文件失败:', error)
              showErrorToast(`读取 Excel 文件失败: ${error.message || '文件格式错误'}`)
              return
            }
            
            // 处理导入的数据
            processImportedData(importedData)
          }
          
          reader.onerror = () => {
            showErrorToast('文件读取失败，请重试')
          }
          reader.readAsArrayBuffer(file)
        } else if (isJson) {
          // 读取 JSON 文件
          const reader = new FileReader()
          reader.onload = (event) => {
            try {
              const content = event.target?.result as string
              const jsonData = JSON.parse(content)
              
              // 验证数据格式
              if (!Array.isArray(jsonData)) {
                showErrorToast('导入的文件格式错误：必须是JSON数组格式')
                return
              }
              
              importedData = jsonData
              processImportedData(importedData)
            } catch (error: any) {
              console.error('导入字段失败:', error)
              showErrorToast(`导入失败: ${error.message || '文件格式错误'}`)
            }
          }
          reader.onerror = () => {
            showErrorToast('文件读取失败，请重试')
          }
          reader.readAsText(file)
        } else {
          showErrorToast('不支持的文件格式，请选择 JSON 或 Excel 文件')
        }
      } catch (error: any) {
        console.error('导入字段失败:', error)
        showErrorToast(`导入失败: ${error.message || '未知错误'}`)
      }
    }
    input.click()
  }
  
  // 处理导入的数据
  const processImportedData = (importedData: any[]) => {
    // 转换导入的数据为字段格式
    const importedFields: TemplateField[] = importedData.map((item: any, index: number) => {
      const newFieldId = `imported_field_${Date.now()}_${index}_${Math.random().toString(36).substr(2, 9)}`
      return {
        id: newFieldId,
        field_key: item['字段标识'] || item.field_key || `field_${fields.length + index + 1}`,
        field_name: item['字段名称'] || item.field_name || '',
        data_name: item['数据名称'] || item.data_name || item['字段标识'] || item.field_key || '',
        data_type: item['数据类型'] || item.data_type || 'string',
        is_required: item['是否必填'] === '是' || item['是否必填'] === true || item.is_required === true || item.is_required === 'true',
        description: item['描述'] || item.description || '',
        example: item['示例值'] || item.example || '',
        validation: item['validation'] || item.validation,
        normalize: item['normalize'] || item.normalize,
        prompt_hint: item['prompt_hint'] || item.prompt_hint,
        confidence_threshold: item['confidence_threshold'] || item.confidence_threshold,
        sort_order: fields.length + index
      }
    })
    
    if (importedFields.length === 0) {
      showErrorToast('导入的文件中没有有效的字段数据')
      return
    }
    
    // 将新导入的字段ID添加到新字段集合中
    const importedFieldIds = importedFields.map(f => f.id!).filter(Boolean)
    setNewFieldIds(new Set([...newFieldIds, ...importedFieldIds]))
    
    // 合并到现有字段（追加）
    setFields([...fields, ...importedFields])
    
    // 如果导入的字段较多，自动展开
    if (!isFieldsExpanded && fields.length + importedFields.length > 3) {
      onFieldsToggle()
    }
    
    showSuccessToast(`成功导入 ${importedFields.length} 个字段`)
  }
  
  // 导出字段到Excel
  const handleExportFields = () => {
    if (fields.length === 0) {
      showErrorToast('没有字段可导出')
      return
    }
    
    try {
      // 准备导出数据 - 只包含必要的字段属性
      const exportData = fields.map((field, index) => ({
        '序号': index + 1,
        '字段标识': field.field_key || '',
        '字段名称': field.field_name || '',
        '数据名称': field.data_name || field.field_key || '',
        '数据类型': field.data_type || 'string',
        '是否必填': field.is_required ? '是' : '否',
        '描述': field.description || ''
      }))
      
      // 创建工作簿
      const wb = XLSX.utils.book_new()
      const ws = XLSX.utils.json_to_sheet(exportData)
      
      // 设置列宽
      const colWidths = [
        { wch: 8 },  // 序号
        { wch: 20 }, // 字段标识
        { wch: 20 }, // 字段名称
        { wch: 20 }, // 数据名称
        { wch: 12 }, // 数据类型
        { wch: 12 }, // 是否必填
        { wch: 30 }  // 描述
      ]
      ws['!cols'] = colWidths
      
      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, '字段属性表')
      
      // 生成文件名
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
      const fileName = `字段属性表_${formData.name || '模板'}_${timestamp}.xlsx`
      
      // 导出文件
      XLSX.writeFile(wb, fileName)
      showSuccessToast(`成功导出 ${fields.length} 个字段到 Excel`)
    } catch (error: any) {
      console.error('导出字段失败:', error)
      showErrorToast(`导出失败: ${error.message || '未知错误'}`)
    }
  }
  
  // 将字段表格转换为JSON
  const convertFieldsToJson = (): any[] => {
    return fields.map(field => ({
      "字段标识": field.field_key || '',
      "字段名称": field.field_name || '',
      "数据名称": field.data_name || field.field_key || '',
      "是否必填": field.is_required ? '是' : '否',
      "描述": field.description || '',
      "示例值": field.example || ''
    }))
  }
  
  // 调用DIFY API生成提示词
  const generatePromptWithDify = async (fieldJson: any[], promptText?: string, llmConfigId?: string) => {
    const isUpdate = !!promptText
    const actionText = isUpdate ? '更新' : '生成'
    
    try {
      setIsGeneratingPrompt(true)
      setGenerationProgress({ step: `正在转换字段信息为JSON格式...`, percentage: 10 })
      
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      setGenerationProgress({ step: `正在准备API请求...`, percentage: 30 })
      
      const requestData: any = {
        field_definitions: fieldJson,
        mode: isUpdate ? 'update' : 'generate'
      }
      
      if (promptText) {
        requestData.prompt_text = promptText
      }
      
      // 如果指定了llm_config_id，添加到请求中
      if (llmConfigId) {
        requestData.llm_config_id = llmConfigId
      }
      
      setGenerationProgress({ step: `正在调用Dify API${actionText}提示词...`, percentage: 50 })
      
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/templates/${templateId || 'new'}/generate-prompt`,
        requestData,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )
      
      setGenerationProgress({ step: `正在处理API返回结果...`, percentage: 80 })
      
      if (response.data && response.data.success) {
        const generatedPrompt = response.data.data?.prompt || ''
        setAiSuggestedPrompt(generatedPrompt)
        setLastGeneratedPrompt(generatedPrompt)
        // 将生成的提示词自动设置到templatePrompt
        setTemplatePrompt(generatedPrompt)
        
        setGenerationProgress({ step: `提示词${actionText}完成！`, percentage: 100 })
        setTimeout(() => {
          setGenerationProgress(null)
        }, 1000)
        
        showSuccessToast(`提示词${actionText}成功`)
        return generatedPrompt
      } else {
        throw new Error(response.data?.message || `${actionText}提示词失败`)
      }
    } catch (error: any) {
      console.error(`${actionText}提示词失败:`, error)
      const errorMessage = error.response?.data?.detail || error.message || `${actionText}提示词失败`
      setGenerationProgress({ step: `${actionText}失败: ${errorMessage}`, percentage: 0 })
      setTimeout(() => {
        setGenerationProgress(null)
      }, 3000)
      showErrorToast(errorMessage)
      throw error
    } finally {
      setIsGeneratingPrompt(false)
    }
  }
  
  // 按钮A：AI 输出提示词
  const handleGeneratePrompt = async () => {
    if (fields.length === 0) {
      showErrorToast('请先添加字段')
      return
    }
    
    try {
      // 将字段属性表中的所有信息转换为JSON格式
      const fieldJson = convertFieldsToJson()
      console.log('字段JSON:', JSON.stringify(fieldJson, null, 2))
      
      // 调用指定的llm_config
      const specifiedLLMConfigId = '89a8938c-c0cb-4294-a874-f026204f997b'
      await generatePromptWithDify(fieldJson, undefined, specifiedLLMConfigId)
    } catch (error) {
      // 错误已在generatePromptWithDify中处理
    }
  }
  
  // 按钮B：AI 更新提示词
  const handleUpdatePrompt = async () => {
    if (!templatePrompt.trim()) {
      showErrorToast('请先生成或输入提示词')
      return
    }
    
    if (fields.length === 0) {
      showErrorToast('请先添加字段')
      return
    }
    
    try {
      // 将字段属性表中的所有信息转换为JSON格式
      const fieldJson = convertFieldsToJson()
      console.log('更新提示词 - 字段JSON:', JSON.stringify(fieldJson, null, 2))
      
      // 调用指定的llm_config
      const specifiedLLMConfigId = '89a8938c-c0cb-4294-a874-f026204f997b'
      const updatedPrompt = await generatePromptWithDify(fieldJson, templatePrompt, specifiedLLMConfigId)
      // 将更新后的提示词设置到templatePrompt
      if (updatedPrompt) {
        setTemplatePrompt(updatedPrompt)
      }
    } catch (error) {
      // 错误已在generatePromptWithDify中处理
    }
  }
  
  // 按钮C：自己补充提示词
  const handleManualPrompt = () => {
    // 如果AI建议提示词存在，将其复制到提示词区域
    if (aiSuggestedPrompt && aiSuggestedPrompt !== templatePrompt) {
      setTemplatePrompt(aiSuggestedPrompt)
      showSuccessToast('已应用AI建议提示词，您可以继续编辑')
    } else {
      showSuccessToast('您可以直接在提示词区域编辑')
    }
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
    
    // 如果字段被编辑（有内容），从新字段集合中移除红色标识
    const currentField = updatedFields[index]
    if (currentField.id && newFieldIds.has(currentField.id)) {
      // 检查字段是否有实际内容（不是空值）
      if (currentField.field_key || currentField.field_name || currentField.data_name) {
        const updatedNewFieldIds = new Set(newFieldIds)
        updatedNewFieldIds.delete(currentField.id)
        setNewFieldIds(updatedNewFieldIds)
      }
    }
  }

  if (loading) {
    return (
      <Box p={6} textAlign="center">
        <Text>加载中...</Text>
      </Box>
    )
  }

  return (
    <Box h="100vh" display="flex" flexDirection="column" overflow="hidden" bg="gray.50" width="100%">
      {/* 主内容区 */}
      <Box flex="1" display="flex" flexDirection="column" overflow="auto" p={6} minWidth={0}>
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

        {/* 主要内容区域 */}
        <VStack spacing={4} align="stretch">
          {/* 基本信息 - 横向布局 */}
          <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
            <Text fontSize="lg" fontWeight="medium" mb={4}>基本信息</Text>
            <Grid templateColumns={{ base: "1fr", md: "1fr 1fr", lg: "1fr 1fr 1fr 1fr" }} gap={4}>
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
            </Grid>
          </Box>

          {/* 字段属性表 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200" w="100%">
              <Flex justify="space-between" align="center" mb={4}>
                <Text fontSize="lg" fontWeight="medium">字段属性表 ({fields.length})</Text>
                <HStack spacing={2}>
                  <Button
                    onClick={handleImportFields}
                    leftIcon={<FiUpload />}
                    size="sm"
                    variant="outline"
                    colorScheme="blue"
                  >
                    导入字段
                  </Button>
                  <Button
                    onClick={handleExportFields}
                    leftIcon={<FiDownload />}
                    size="sm"
                    variant="outline"
                    colorScheme="green"
                  >
                    导出 EXCEL 表
                  </Button>
                  <Button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleAddField()
                    }}
                    leftIcon={<FiPlus />}
                    size="sm"
                    colorScheme="blue"
                  >
                    添加字段
                  </Button>
                  {fields.length > 3 && (
                    <Button
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        const willExpand = !isFieldsExpanded
                        onFieldsToggle()
                        // 展开后滚动到表格底部，确保展开的字段可见
                        if (willExpand) {
                          setTimeout(() => {
                            const tableElement = document.querySelector('[data-field-table]')
                            if (tableElement) {
                              tableElement.scrollIntoView({ behavior: 'smooth', block: 'end' })
                            }
                          }, 200)
                        }
                      }}
                      leftIcon={isFieldsExpanded ? <FiChevronUp /> : <FiChevronDown />}
                      size="sm"
                      variant="outline"
                    >
                      {isFieldsExpanded ? '收起' : `展开全部 (${fields.length - 3})`}
                    </Button>
                  )}
                </HStack>
              </Flex>
              {fields.length === 0 ? (
                <Box p={4} textAlign="center" color="gray.500">
                  <Text>暂无字段，点击"添加字段"开始配置</Text>
                </Box>
              ) : (
                <Box overflowX="auto" overflowY="visible" minH="0" data-field-table>
                  <Table.Root size="sm" variant="simple">
                    <Table.Header>
                      <Table.Row>
                        <Table.ColumnHeader>字段标识</Table.ColumnHeader>
                        <Table.ColumnHeader>字段名称</Table.ColumnHeader>
                        <Table.ColumnHeader>数据名称</Table.ColumnHeader>
                        <Table.ColumnHeader>是否必填</Table.ColumnHeader>
                        <Table.ColumnHeader>描述</Table.ColumnHeader>
                        <Table.ColumnHeader>示例值</Table.ColumnHeader>
                        <Table.ColumnHeader>操作</Table.ColumnHeader>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {/* 显示前3行 */}
                      {fields.slice(0, 3).map((field, displayIndex) => {
                        const actualIndex = displayIndex
                        const fieldKey = field.id || `field-${actualIndex}`
                        const isNewField = field.id && newFieldIds.has(field.id)
                        return (
                          <Table.Row 
                            key={fieldKey}
                            bg={isNewField ? "red.50" : undefined}
                            borderColor={isNewField ? "red.200" : undefined}
                            borderWidth={isNewField ? "1px" : undefined}
                          >
                            <Table.Cell>
                              <Input
                                size="sm"
                                value={field.field_key}
                                onChange={(e) => handleFieldChange(actualIndex, { field_key: e.target.value })}
                                placeholder="如：invoice_no"
                              />
                            </Table.Cell>
                            <Table.Cell>
                              <Input
                                size="sm"
                                value={field.field_name}
                                onChange={(e) => handleFieldChange(actualIndex, { field_name: e.target.value })}
                                placeholder="如：发票号码"
                              />
                            </Table.Cell>
                            <Table.Cell>
                              <Input
                                size="sm"
                                value={field.data_name || ''}
                                onChange={(e) => handleFieldChange(actualIndex, { data_name: e.target.value })}
                                placeholder="如：invoiceNo"
                              />
                            </Table.Cell>
                            <Table.Cell>
                              <select
                                value={field.is_required ? 'true' : 'false'}
                                onChange={(e) => handleFieldChange(actualIndex, { is_required: e.target.value === 'true' })}
                                style={{
                                  width: '100%',
                                  padding: '4px',
                                  border: '1px solid #e2e8f0',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}
                              >
                                <option value="false">否</option>
                                <option value="true">是</option>
                              </select>
                            </Table.Cell>
                            <Table.Cell>
                              <Input
                                size="sm"
                                value={field.description || ''}
                                onChange={(e) => handleFieldChange(actualIndex, { description: e.target.value })}
                                placeholder="字段描述"
                              />
                            </Table.Cell>
                            <Table.Cell>
                              <Input
                                size="sm"
                                value={field.example || ''}
                                onChange={(e) => handleFieldChange(actualIndex, { example: e.target.value })}
                                placeholder="示例值"
                              />
                            </Table.Cell>
                            <Table.Cell>
                              <Box display="flex" justifyContent="center">
                                <IconButton
                                  aria-label="删除"
                                  icon={<FiMinus />}
                                  size="xs"
                                  bg="white"
                                  color="red.500"
                                  borderRadius="full"
                                  border="1px solid"
                                  borderColor="gray.300"
                                  _hover={{ bg: "gray.50", borderColor: "red.400" }}
                                  _active={{ bg: "gray.100" }}
                                  title="删除字段"
                                  onClick={() => {
                                    // 从新字段集合中移除
                                    if (field.id) {
                                      const updatedNewFieldIds = new Set(newFieldIds)
                                      updatedNewFieldIds.delete(field.id)
                                      setNewFieldIds(updatedNewFieldIds)
                                    }
                                    handleDeleteField(actualIndex)
                                  }}
                                />
                              </Box>
                            </Table.Cell>
                          </Table.Row>
                        )
                      })}
                      {/* 展开时显示剩余的字段 */}
                      {isFieldsExpanded && fields.length > 3 && (
                        <>
                          {/* 分隔行提示 */}
                          <Table.Row bg="gray.50">
                            <Table.Cell colSpan={7} py={2} textAlign="center">
                              <Text fontSize="xs" color="gray.500" fontWeight="medium">
                                ─── 以下为展开的字段 ({fields.length - 3} 个) ───
                              </Text>
                            </Table.Cell>
                          </Table.Row>
                          {fields.slice(3).map((field, displayIndex) => {
                            const actualIndex = displayIndex + 3
                            const fieldKey = field.id || `field-${actualIndex}`
                            const isNewField = field.id && newFieldIds.has(field.id)
                            return (
                              <Table.Row 
                                key={fieldKey}
                                bg={isNewField ? "red.50" : undefined}
                                borderColor={isNewField ? "red.200" : undefined}
                                borderWidth={isNewField ? "1px" : undefined}
                              >
                                <Table.Cell>
                                  <Input
                                    size="sm"
                                    value={field.field_key}
                                    onChange={(e) => handleFieldChange(actualIndex, { field_key: e.target.value })}
                                    placeholder="如：invoice_no"
                                  />
                                </Table.Cell>
                                <Table.Cell>
                                  <Input
                                    size="sm"
                                    value={field.field_name}
                                    onChange={(e) => handleFieldChange(actualIndex, { field_name: e.target.value })}
                                    placeholder="如：发票号码"
                                  />
                                </Table.Cell>
                                <Table.Cell>
                                  <Input
                                    size="sm"
                                    value={field.data_name || ''}
                                    onChange={(e) => handleFieldChange(actualIndex, { data_name: e.target.value })}
                                    placeholder="如：invoiceNo"
                                  />
                                </Table.Cell>
                                <Table.Cell>
                                  <select
                                    value={field.is_required ? 'true' : 'false'}
                                    onChange={(e) => handleFieldChange(actualIndex, { is_required: e.target.value === 'true' })}
                                    style={{
                                      width: '100%',
                                      padding: '4px',
                                      border: '1px solid #e2e8f0',
                                      borderRadius: '4px',
                                      fontSize: '12px'
                                    }}
                                  >
                                    <option value="false">否</option>
                                    <option value="true">是</option>
                                  </select>
                                </Table.Cell>
                                <Table.Cell>
                                  <Input
                                    size="sm"
                                    value={field.description || ''}
                                    onChange={(e) => handleFieldChange(actualIndex, { description: e.target.value })}
                                    placeholder="字段描述"
                                  />
                                </Table.Cell>
                                <Table.Cell>
                                  <Input
                                    size="sm"
                                    value={field.example || ''}
                                    onChange={(e) => handleFieldChange(actualIndex, { example: e.target.value })}
                                    placeholder="示例值"
                                  />
                                </Table.Cell>
                                <Table.Cell>
                                  <Box display="flex" justifyContent="center">
                                    <IconButton
                                      aria-label="删除"
                                      icon={<FiMinus />}
                                      size="xs"
                                      bg="white"
                                      color="red.500"
                                      borderRadius="full"
                                      border="1px solid"
                                      borderColor="gray.300"
                                      _hover={{ bg: "gray.50", borderColor: "red.400" }}
                                      _active={{ bg: "gray.100" }}
                                      title="删除字段"
                                      onClick={() => {
                                        // 从新字段集合中移除
                                        if (field.id) {
                                          const updatedNewFieldIds = new Set(newFieldIds)
                                          updatedNewFieldIds.delete(field.id)
                                          setNewFieldIds(updatedNewFieldIds)
                                        }
                                        handleDeleteField(actualIndex)
                                      }}
                                    />
                                  </Box>
                                </Table.Cell>
                              </Table.Row>
                            )
                          })}
                        </>
                      )}
                    </Table.Body>
                  </Table.Root>
                </Box>
              )}
            </Box>

            {/* 提示词配置 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Flex justify="space-between" align="center" mb={4}>
                <Text fontSize="lg" fontWeight="medium">提示词配置</Text>
                <HStack spacing={2}>
                  <Button
                    onClick={handleGeneratePrompt}
                    leftIcon={<FiCheckCircle />}
                    size="sm"
                    colorScheme="blue"
                    isLoading={isGeneratingPrompt}
                    loadingText="生成中..."
                  >
                    AI 输出提示词
                  </Button>
                  <Button
                    onClick={handleUpdatePrompt}
                    size="sm"
                    variant="outline"
                    colorScheme="blue"
                    isLoading={isGeneratingPrompt}
                    loadingText="更新中..."
                  >
                    AI 更新提示词
                  </Button>
                  <Button
                    onClick={handleManualPrompt}
                    size="sm"
                    variant="outline"
                  >
                    手动更新提示词
                  </Button>
                </HStack>
              </Flex>
              <VStack spacing={4} align="stretch">
                {/* 进度显示 */}
                {generationProgress && (
                  <Box
                    p={3}
                    bg="blue.50"
                    borderRadius="md"
                    border="1px"
                    borderColor="blue.200"
                  >
                    <Flex justify="space-between" align="center" mb={2}>
                      <Text fontSize="sm" fontWeight="medium" color="blue.700">
                        {generationProgress.step}
                      </Text>
                      <Text fontSize="sm" color="blue.600">
                        {generationProgress.percentage}%
                      </Text>
                    </Flex>
                    <Box
                      w="100%"
                      h="8px"
                      bg="blue.100"
                      borderRadius="full"
                      overflow="hidden"
                    >
                      <Box
                        h="100%"
                        bg="blue.500"
                        width={`${generationProgress.percentage}%`}
                        transition="width 0.3s"
                        borderRadius="full"
                      />
                    </Box>
                  </Box>
                )}
                
                {/* 提示词 */}
                <Box>
                  <Text fontSize="md" fontWeight="medium" mb={2}>提示词</Text>
                  <Textarea
                    value={templatePrompt || ''}
                    onChange={(e) => {
                      console.log('Textarea onChange, 新值:', e.target.value)
                      setTemplatePrompt(e.target.value)
                    }}
                    placeholder="请输入提示词，用于指导AI识别和提取文档中的信息..."
                    rows={10}
                    fontSize="sm"
                    resize="vertical"
                    bg={aiSuggestedPrompt && templatePrompt === aiSuggestedPrompt ? "blue.50" : "white"}
                    borderColor={aiSuggestedPrompt && templatePrompt === aiSuggestedPrompt ? "blue.200" : "gray.200"}
                  />
                  <Text fontSize="xs" color="gray.400" mt={1}>
                    当前值长度: {templatePrompt?.length || 0} 字符
                  </Text>
                  <Text fontSize="xs" color="gray.500" mt={2}>
                    提示：提示词将用于指导AI模型识别和提取文档中的关键信息，请详细描述需要提取的字段和要求
                  </Text>
                </Box>
              </VStack>
            </Box>

            {/* Schema JSON 配置 */}
            <Box bg="white" p={4} borderRadius="md" border="1px" borderColor="gray.200">
              <Flex justify="space-between" align="center" mb={4}>
                <Text fontSize="lg" fontWeight="medium">请输入 Schema</Text>
                <Button
                  size="sm"
                  colorScheme="blue"
                  variant="outline"
                  leftIcon={<FiCheckCircle />}
                  onClick={validateJsonSchema}
                >
                  JSON Schema 校验
                </Button>
              </Flex>
              <VStack spacing={4} align="stretch">
                <Field label="">
                  <Textarea
                    value={templateSchema || ''}
                    onChange={(e) => {
                      setTemplateSchema(e.target.value)
                      setSchemaValidationResult(null) // 清除之前的校验结果
                    }}
                    placeholder='请输入 JSON Schema，例如：{"type": "object", "properties": {...}}'
                    rows={12}
                    fontSize="sm"
                    resize="vertical"
                    fontFamily="monospace"
                  />
                  <Text fontSize="xs" color="gray.400" mt={1}>
                    当前值长度: {templateSchema?.length || 0} 字符
                  </Text>
                  {schemaValidationResult && (
                    <Box
                      mt={2}
                      p={3}
                      bg={schemaValidationResult.valid ? "green.50" : "red.50"}
                      borderRadius="md"
                      border="1px"
                      borderColor={schemaValidationResult.valid ? "green.200" : "red.200"}
                    >
                      <Flex align="center" gap={2}>
                        <FiCheckCircle color={schemaValidationResult.valid ? "#10b981" : "#ef4444"} />
                        <Text fontSize="sm" color={schemaValidationResult.valid ? "green.700" : "red.700"}>
                          {schemaValidationResult.message}
                        </Text>
                      </Flex>
                      {schemaValidationResult.errors && schemaValidationResult.errors.length > 0 && (
                        <Box mt={2}>
                          <Text fontSize="xs" fontWeight="medium" color="red.600" mb={1}>错误详情：</Text>
                          {schemaValidationResult.errors.map((error: any, index: number) => (
                            <Text key={index} fontSize="xs" color="red.600" ml={2}>
                              • {error.message || JSON.stringify(error)}
                            </Text>
                          ))}
                        </Box>
                      )}
                    </Box>
                  )}
                  <Text fontSize="xs" color="gray.500" mt={2}>
                    提示：请输入符合 JSON Schema Draft 7 规范的 Schema 定义，用于定义AI模型输出的数据结构
                  </Text>
                </Field>
              </VStack>
            </Box>
        </VStack>
      </Box>
    </Box>
  )
}

export default TemplateEditEnhanced

