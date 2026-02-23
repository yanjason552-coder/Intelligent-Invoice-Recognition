import { Box, Text, Flex, VStack, HStack, Input, Badge, IconButton, Grid, Textarea, Table, Icon, Stack } from "@chakra-ui/react"
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogBody,
  DialogFooter,
  DialogCloseTrigger,
  DialogTitle,
} from "@/components/ui/dialog"
import { FiSave, FiX, FiPlus, FiTrash2, FiEdit2, FiLink, FiCheckCircle, FiChevronDown, FiChevronUp, FiUpload, FiDownload, FiMinus, FiRefreshCw, FiCopy, FiXCircle, FiAlertCircle } from "react-icons/fi"
import { useState, useEffect, useMemo } from "react"
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
    status: string  // draft/published/deprecated
    created_at?: string
    published_at?: string
    prompt?: string | null
    prompt_status?: string | null
    prompt_hash?: string | null
    prompt_updated_at?: string | null
  }
  fields?: TemplateField[]
  create_time?: string
  update_time?: string
}

// 从字段列表生成简单的JSON结构（根据数据名称和数据类型）
function generateSimpleJsonFromFields(fields: TemplateField[]): any {
  const result: any = {}

  // 按字段层级分组
  const topLevelFields = fields.filter(field => !field.parent_field_id)
  const fieldMap = new Map(fields.map(field => [field.id, field]))

  // 处理顶级字段
  topLevelFields.forEach(field => {
    const fieldKey = field.data_name || field.field_key

    if (field.data_type === 'array') {
      // 数组类型的字段，查找其子字段
      const childFields = fields.filter(f => f.parent_field_id === field.id)
      if (childFields.length > 0) {
        // 创建数组项的对象结构
        const arrayItem: any = {}
        childFields.forEach(childField => {
          const childKey = childField.data_name || childField.field_key
          arrayItem[childKey] = getFieldTypeString(childField)
        })
        result[fieldKey] = [arrayItem]
      } else {
        result[fieldKey] = []
      }
    } else {
      // 普通字段
      result[fieldKey] = getFieldTypeString(field)
    }
  })

  return result
}

// 获取字段的类型字符串
function getFieldTypeString(field: TemplateField): string {
  let typeString = mapDataTypeToSimpleType(field.data_type)

  // 如果不是必填字段，添加"| null"
  if (!field.is_required) {
    typeString += ' | null'
  }

  return typeString
}

// 数据类型映射为简单类型字符串
function mapDataTypeToSimpleType(dataType: string): string {
  const typeMapping: Record<string, string> = {
    'string': 'string',
    'integer': 'integer',
    'number': 'number',
    'boolean': 'boolean',
    'array': 'array',
    'object': 'object',
    'enum': 'pass | fail | unknown' // 对于枚举类型，使用固定的枚举值
  }

  return typeMapping[dataType.toLowerCase()] || 'string'
}

// 从字段列表生成JSON Schema
function generateSchemaFromFields(fields: TemplateField[]): any {
  const schema: any = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {},
    "required": []
  }

  // 按字段层级组织
  const fieldMap = new Map<string, TemplateField>()

  // 首先建立字段映射
  fields.forEach(field => {
    fieldMap.set(field.field_key, field)
  })

  // 处理顶级字段和嵌套字段
  fields.forEach(field => {
    if (!field.parent_field_id) {
      // 顶级字段
      if (field.data_type === 'array') {
        // 数组类型字段
        schema.properties[field.field_key] = {
          "type": "array",
          "items": generateNestedSchema(field, fields, fieldMap)
        }
      } else {
        // 普通字段
        schema.properties[field.field_key] = generateFieldSchema(field)
      }

      // 如果是必填字段，添加到required数组
      if (field.is_required) {
        schema.required.push(field.field_key)
      }
    }
  })

  return schema
}

// 生成嵌套Schema（用于数组项）
function generateNestedSchema(parentField: TemplateField, allFields: TemplateField[], fieldMap: Map<string, TemplateField>): any {
  const nestedSchema: any = {
    "type": "object",
    "properties": {},
    "required": []
  }

  // 找到这个父字段的所有子字段
  allFields.forEach(field => {
    if (field.parent_field_id === parentField.id) {
      nestedSchema.properties[field.field_key] = generateFieldSchema(field)

      if (field.is_required) {
        nestedSchema.required.push(field.field_key)
      }
    }
  })

  return nestedSchema
}

// 生成单个字段的Schema
function generateFieldSchema(field: TemplateField): any {
  const fieldSchema: any = {
    "type": mapDataTypeToJsonType(field.data_type),
    "description": field.description || field.field_name
  }

  // 如果有示例值，添加到schema
  if (field.example) {
    fieldSchema.example = field.example
  }

  return fieldSchema
}

// 数据类型映射
function mapDataTypeToJsonType(dataType: string): string {
  const typeMapping: Record<string, string> = {
    'string': 'string',
    'integer': 'integer',
    'number': 'number',
    'boolean': 'boolean',
    'array': 'array',
    'object': 'object',
    'enum': 'string' // enum类型在JSON Schema中通常用string+enum表示
  }

  return typeMapping[dataType.toLowerCase()] || 'string'
}

// 解析嵌套JSON结构为字段列表
function parseNestedJsonToFields(
  data: any,
  parentKey: string = '',
  parentFieldKey: string | null = null,
  sortOrderStart: number = 0
): any[] {
  const fields: any[] = []
  let sortOrder = sortOrderStart

  if (typeof data !== 'object' || data === null) {
    // 如果不是对象，返回单个字段
    return [{
      field_key: parentKey || 'root',
      field_name: keyToFieldName(parentKey || 'root'),
      data_type: inferDataType(data),
      parent_field_key: parentFieldKey,
      sort_order: sortOrder,
      description: null,
      example: data !== null && data !== undefined ? String(data).substring(0, 200) : null,
    }]
  }

  if (Array.isArray(data)) {
    // 数组类型：处理第一个元素（如果存在且是对象）
    if (data.length > 0 && typeof data[0] === 'object' && data[0] !== null) {
      const arrayFieldKey = parentKey || 'items'
      const arrayField = {
        field_key: arrayFieldKey,
        field_name: keyToFieldName(arrayFieldKey),
        data_type: 'array',
        parent_field_key: parentFieldKey,
        sort_order: sortOrder,
        description: null,
        example: null,
      }
      fields.push(arrayField)
      sortOrder++

      // 递归处理数组元素的字段
      const subFields = parseNestedJsonToFields(
        data[0],
        arrayFieldKey,
        arrayFieldKey,
        sortOrder
      )
      fields.push(...subFields)
      sortOrder += subFields.length
    } else {
      // 简单数组
      fields.push({
        field_key: parentKey || 'items',
        field_name: keyToFieldName(parentKey || 'items'),
        data_type: 'array',
        parent_field_key: parentFieldKey,
        sort_order: sortOrder,
        description: null,
        example: JSON.stringify(data).substring(0, 200),
      })
    }
    return fields
  }

  // 对象类型：遍历所有属性
  for (const [key, value] of Object.entries(data)) {
    const fieldKey = parentKey ? `${parentKey}.${key}` : key

    // 推断数据类型
    let dataType = inferDataType(value)

    // 创建当前字段
    const currentField: any = {
      field_key: fieldKey,
      field_name: keyToFieldName(key),
      data_type: dataType,
      parent_field_key: parentFieldKey,
      sort_order: sortOrder,
      description: null,
      example: null,
    }

    // 设置示例值（如果不是对象或数组）
    if (value !== null && value !== undefined && typeof value !== 'object') {
      currentField.example = String(value).substring(0, 200)
    }

    fields.push(currentField)
    sortOrder++

    // 如果是对象或数组，递归处理子字段
    if (typeof value === 'object' && value !== null) {
      if (Array.isArray(value)) {
        // 数组类型：如果元素是对象，处理第一个元素的字段
        if (value.length > 0 && typeof value[0] === 'object' && value[0] !== null) {
          const subFields = parseNestedJsonToFields(
            value[0],
            fieldKey,
            fieldKey,
            sortOrder
          )
          fields.push(...subFields)
          sortOrder += subFields.length
        }
      } else {
        // 对象类型：递归处理子字段
        const subFields = parseNestedJsonToFields(
          value,
          fieldKey,
          fieldKey,
          sortOrder
        )
        fields.push(...subFields)
        sortOrder += subFields.length
      }
    }
  }

  return fields
}

// 推断数据类型
function inferDataType(value: any): string {
  if (value === null || value === undefined) {
    return 'string'
  }
  if (typeof value === 'boolean') {
    return 'boolean'
  }
  if (typeof value === 'number') {
    return 'number'
  }
  if (typeof value === 'string') {
    // 尝试判断是否为日期
    if (value.length === 10 && value.split('-').length === 3) {
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/
      if (dateRegex.test(value)) {
        return 'date'
      }
    }
    return 'string'
  }
  if (Array.isArray(value)) {
    return 'array'
  }
  if (typeof value === 'object') {
    return 'object'
  }
  return 'string'
}

// 将字段key转换为中文名称
function keyToFieldName(key: string): string {
  const nameMap: { [key: string]: string } = {
    // 基础字段
    invoice_title: '发票抬头',
    invoice_no: '发票号码',
    purchase_order: '采购订单号',
    reference_order: '参考订单号',
    supplier_no: '供应商编号',
    docdate: '开票日期',
    currency: '币种',
    remarks: '备注',
    issuer: '开票人',
    
    // 嵌套对象
    buyer_info: '购买方信息',
    seller_info: '销售方信息',
    total_amount_inclusive_tax: '含税合计',
    
    // buyer_info 子字段
    name: '名称',
    tax_id: '税号',
    company_code: '公司代码',
    
    // seller_info 子字段（name 和 tax_id 已在上方定义）
    
    // items 数组
    items: '商品明细',
    LineId: '行号',
    part_no: '零件号',
    supplier_partno: '供应商零件号',
    po_no: '采购订单号',
    model: '规格型号',
    unit: '单位',
    quantity: '数量',
    unit_price: '单价',
    amount: '金额',
    tax_rate: '税率',
    tax_amount: '税额',
    
    // total_amount_inclusive_tax 子字段
    total_amount_exclusive_tax: '不含税合计',
    total_tax_amount: '税额合计',
    in_words: '大写金额',
    in_figures: '小写金额',
  }

  // 处理嵌套字段（如 buyer_info.name）
  if (key.includes('.')) {
    const parts = key.split('.')
    const lastPart = parts[parts.length - 1]
    if (nameMap[lastPart]) {
      return nameMap[lastPart]
    }
    // 如果最后一部分没有映射，尝试整个key
    if (nameMap[key]) {
      return nameMap[key]
    }
  }

  if (nameMap[key]) {
    return nameMap[key]
  }

  // 如果没有映射，尝试将下划线分隔的key转换为中文
  return key.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

// 计算字段的嵌套层级和缩进
function getFieldDisplayInfo(field: TemplateField, allFields: TemplateField[]): {
  level: number
  indent: number
  displayKey: string
  isNested: boolean
} {
  let level = 0
  let currentField: TemplateField | undefined = field
  const fieldMap = new Map<string, TemplateField>()
  allFields.forEach(f => {
    if (f.id) {
      fieldMap.set(f.id, f)
    }
  })

  // 向上查找父字段，计算层级
  while (currentField?.parent_field_id) {
    level++
    const parentId = currentField.parent_field_id
    currentField = fieldMap.get(parentId)
    if (!currentField) break
  }

  // 如果通过 parent_field_id 没有找到层级，尝试通过 field_key 判断
  // 例如：buyer_info.name 应该是 level 1
  if (level === 0 && field.field_key) {
    const keyParts = field.field_key.split('.')
    if (keyParts.length > 1) {
      // 通过 field_key 的层级来判断
      level = keyParts.length - 1
    }
  }

  // 计算缩进（每级缩进24px）
  const indent = level * 24

  // 显示字段标识（如果包含点号，说明是嵌套字段）
  const displayKey = field.field_key || ''
  const isNested = displayKey.includes('.') || level > 0

  return {
    level,
    indent,
    displayKey,
    isNested
  }
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
  const [promptHash, setPromptHash] = useState<string | null>(null)  // 提示词hash（用于过期检测）
  const [promptStale, setPromptStale] = useState<boolean>(false)  // 提示词是否过期
  const [isPromptReadOnly, setIsPromptReadOnly] = useState<boolean>(true)  // 提示词是否只读
  
  // Schema JSON（新增）
  const [templateSchema, setTemplateSchema] = useState<string>('')
  const [schemaValidationResult, setSchemaValidationResult] = useState<{
    valid: boolean
    message: string
    errors?: any[]
  } | null>(null)

  // 字段列表
  const [fields, setFields] = useState<TemplateField[]>([])
  
  // 原始字段列表（加载时的字段，用于检测新增）
  const [originalFields, setOriginalFields] = useState<TemplateField[]>([])
  
  // 排序后的字段列表（确保父字段在子字段之前）
  const sortedFields = useMemo(() => {
    return [...fields].sort((a, b) => {
      // 首先按 sort_order 排序
      const orderA = a.sort_order || 0
      const orderB = b.sort_order || 0
      if (orderA !== orderB) {
        return orderA - orderB
      }
      
      // 如果 sort_order 相同，按 field_key 的层级排序（父字段在前）
      const keyA = a.field_key || ''
      const keyB = b.field_key || ''
      const levelA = keyA.split('.').length
      const levelB = keyB.split('.').length
      if (levelA !== levelB) {
        return levelA - levelB
      }
      
      // 如果层级相同，按字母顺序排序
      return keyA.localeCompare(keyB)
    })
  }, [fields])
  
  // 字段表格展开/收起
  const [isFieldsExpanded, setIsFieldsExpanded] = useState(false)
  const onFieldsToggle = () => {
    setIsFieldsExpanded(prev => !prev)
  }
  
  // 新添加的字段ID列表（用于红色高亮显示）
  const [newFieldIds, setNewFieldIds] = useState<Set<string>>(new Set())
  
  // 检测是否有新增字段（用于提醒用户更新 JSON Schema）
  const hasNewFields = useMemo(() => {
    if (!templateId || originalFields.length === 0) {
      // 新建模板或没有原始字段，不显示提醒
      return false
    }
    
    // 比较当前字段和原始字段，检测新增字段
    const originalFieldKeys = new Set(originalFields.map(f => f.field_key))
    const currentFieldKeys = new Set(fields.map(f => f.field_key))
    
    // 检查是否有新增的字段（在当前字段中存在，但在原始字段中不存在）
    const newFields = fields.filter(f => !originalFieldKeys.has(f.field_key))
    
    return newFields.length > 0
  }, [fields, originalFields, templateId])
  
  // 获取新增字段列表（用于显示提醒）
  const newFieldsList = useMemo(() => {
    if (!templateId || originalFields.length === 0) {
      return []
    }
    
    const originalFieldKeys = new Set(originalFields.map(f => f.field_key))
    return fields.filter(f => !originalFieldKeys.has(f.field_key))
  }, [fields, originalFields, templateId])
  
  // AI建议提示词
  const [aiSuggestedPrompt, setAiSuggestedPrompt] = useState<string>('')
  const [isGeneratingPrompt, setIsGeneratingPrompt] = useState(false)
  const [lastGeneratedPrompt, setLastGeneratedPrompt] = useState<string>('')
  const [generationProgress, setGenerationProgress] = useState<{
    step: string
    percentage: number
  } | null>(null)
  
  // 模型选择弹框
  const [isModelModalOpen, setIsModelModalOpen] = useState(false)
  const [llmConfigs, setLlmConfigs] = useState<Array<{
    id: string
    name: string
    description?: string
    is_default: boolean
    is_active: boolean
  }>>([])
  const [selectedLlmConfigId, setSelectedLlmConfigId] = useState<string>('')
  const [pendingPromptAction, setPendingPromptAction] = useState<'generate' | 'update' | null>(null)
  
  const onModelModalOpen = () => setIsModelModalOpen(true)
  const onModelModalClose = () => setIsModelModalOpen(false)

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

  // JSON Schema 校验及纠正函数（合并功能）
  const validateAndFixJsonSchema = async () => {
    if (!templateSchema || !templateSchema.trim()) {
      showErrorToast('请先输入 Schema JSON')
      setSchemaValidationResult({
        valid: false,
        message: 'Schema 内容为空'
      })
      return
    }

    try {
      let fixedJson = templateSchema.trim()
      let wasFixed = false
      
      // 先尝试直接解析，如果成功则只格式化
      try {
        const parsed = JSON.parse(fixedJson)
        // 格式化 JSON（美化）
        fixedJson = JSON.stringify(parsed, null, 2)
        if (fixedJson !== templateSchema) {
          setTemplateSchema(fixedJson)
          wasFixed = true
        }
      } catch (e) {
        // 如果解析失败，尝试修复常见问题
        // 1. 将单引号替换为双引号
        fixedJson = fixedJson.replace(/'/g, '"')
        // 2. 修复尾随逗号
        fixedJson = fixedJson.replace(/,(\s*[}\]])/g, '$1')
        
        try {
          const parsed = JSON.parse(fixedJson)
          fixedJson = JSON.stringify(parsed, null, 2)
          setTemplateSchema(fixedJson)
          wasFixed = true
        } catch (parseError: any) {
          // 如果仍然无法解析，尝试移除注释
          fixedJson = fixedJson.replace(/\/\/.*$/gm, '') // 单行注释
          fixedJson = fixedJson.replace(/\/\*[\s\S]*?\*\//g, '') // 多行注释
          
          try {
            const parsed = JSON.parse(fixedJson)
            fixedJson = JSON.stringify(parsed, null, 2)
            setTemplateSchema(fixedJson)
            wasFixed = true
            showSuccessToast('JSON 格式已自动纠正并美化（已移除注释）')
          } catch (finalError: any) {
            // 无法自动纠正，继续校验流程，让后端返回详细错误
            setSchemaValidationResult({
              valid: false,
              message: `JSON 格式错误，无法自动纠正: ${finalError.message}`
            })
            showErrorToast(`无法自动纠正 JSON 格式: ${finalError.message}`)
            return
          }
        }
      }

      if (wasFixed) {
        setSchemaValidationResult(null) // 清除之前的校验结果
      }

      // 然后进行 Schema 校验
      const parsedSchema = JSON.parse(fixedJson)
      
      // 调用后端 API 进行 JSON Schema 规范验证
      const token = localStorage.getItem('access_token')
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
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
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
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

  // JSON 格式自动纠正函数
  const autoFixJsonFormat = () => {
    if (!templateSchema || !templateSchema.trim()) {
      showErrorToast('请先输入 Schema JSON')
      return
    }

    try {
      let fixedJson = templateSchema.trim()
      
      // 尝试直接解析，如果成功则只格式化
      try {
        const parsed = JSON.parse(fixedJson)
        // 格式化 JSON（美化）
        const formatted = JSON.stringify(parsed, null, 2)
        setTemplateSchema(formatted)
        setSchemaValidationResult(null) // 清除之前的校验结果
        showSuccessToast('JSON 格式已自动纠正并美化')
        return
      } catch (e) {
        // 如果解析失败，尝试修复常见问题
      }

      // 修复常见 JSON 格式问题
      // 1. 将单引号替换为双引号（JSON 标准要求使用双引号）
      // 使用正则表达式智能替换：将键和值的单引号替换为双引号
      fixedJson = fixedJson.replace(/'/g, '"')
      
      // 2. 修复对象和数组末尾的尾随逗号
      // 移除对象属性后的尾随逗号
      fixedJson = fixedJson.replace(/,(\s*[}\]])/g, '$1')
      
      // 3. 修复未转义的换行符（在字符串值中）
      // 这个比较复杂，先尝试基本修复
      
      // 4. 尝试再次解析
      try {
        const parsed = JSON.parse(fixedJson)
        // 格式化 JSON
        const formatted = JSON.stringify(parsed, null, 2)
        setTemplateSchema(formatted)
        setSchemaValidationResult(null) // 清除之前的校验结果
        showSuccessToast('JSON 格式已自动纠正并美化')
      } catch (parseError: any) {
        // 如果仍然无法解析，尝试更激进的修复
        // 移除注释（单行和多行）
        fixedJson = fixedJson.replace(/\/\/.*$/gm, '') // 单行注释
        fixedJson = fixedJson.replace(/\/\*[\s\S]*?\*\//g, '') // 多行注释
        
        // 再次尝试解析
        try {
          const parsed = JSON.parse(fixedJson)
          const formatted = JSON.stringify(parsed, null, 2)
          setTemplateSchema(formatted)
          setSchemaValidationResult(null)
          showSuccessToast('JSON 格式已自动纠正并美化（已移除注释）')
        } catch (finalError: any) {
          showErrorToast(`无法自动纠正 JSON 格式: ${finalError.message}`)
          setSchemaValidationResult({
            valid: false,
            message: `JSON 格式错误，无法自动纠正: ${finalError.message}`
          })
        }
      }
    } catch (error: any) {
      showErrorToast(`自动纠正失败: ${error.message || '未知错误'}`)
      setSchemaValidationResult({
        valid: false,
        message: `自动纠正失败: ${error.message || '未知错误'}`
      })
    }
  }

  // 加载模板详情
  const loadTemplate = async () => {
    if (!templateId) return

    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      // 如果设置了 VITE_API_URL，使用它；否则使用相对路径（空字符串）
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      const url = apiBaseUrl ? `${apiBaseUrl}/api/v1/templates/${templateId}` : `/api/v1/templates/${templateId}`
      
      console.log('加载模板，URL:', url, 'API Base URL:', apiBaseUrl)
      
      const response = await axios.get(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        timeout: 30000, // 30秒超时
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
        // 设置提示词（优先从version获取，否则从template获取）
        let promptValue = ''
        if (data.version?.prompt) {
          promptValue = String(data.version.prompt)
          setIsPromptReadOnly(true)  // 如果version有prompt，设置为只读
        } else if (data.prompt) {
          promptValue = String(data.prompt)
          setIsPromptReadOnly(true)  // 如果template有prompt，也设置为只读
        } else {
          promptValue = ''
          setIsPromptReadOnly(false)  // 没有prompt时，允许编辑（但实际不会显示编辑框）
        }
        
        // 保存prompt_hash（用于过期检测）
        if (data.version?.prompt_hash) {
          setPromptHash(data.version.prompt_hash)
        } else {
          setPromptHash(null)
        }
        
        // 检查prompt是否过期（如果字段或schema有变化）
        if (promptValue && data.version?.prompt_status === 'stale') {
          setPromptStale(true)
        } else {
          setPromptStale(false)
        }
        
        setTemplatePrompt(promptValue)
        setIsPromptReadOnly(true)  // 始终只读，不允许手动编辑
        
        // 加载 Schema JSON（如果存在）
        const schemaValue = data.schema || ''
        setTemplateSchema(schemaValue ? (typeof schemaValue === 'string' ? schemaValue : JSON.stringify(schemaValue, null, 2)) : '')
        
        // 使用useEffect确保状态更新后再次检查
        setTimeout(() => {
          console.log('延迟检查templatePrompt状态:', templatePrompt)
        }, 100)
        
        // 加载字段列表
        const loadedFields = data.fields || []
        console.log('加载的字段列表:', loadedFields)
        console.log('字段数量:', loadedFields.length)
        // 检查是否有嵌套字段
        const nestedFields = loadedFields.filter(f => f.field_key && f.field_key.includes('.'))
        console.log('嵌套字段数量:', nestedFields.length)
        if (nestedFields.length > 0) {
          console.log('嵌套字段示例:', nestedFields.slice(0, 3))
        }
        setFields(loadedFields)
        // 保存原始字段列表（用于检测新增字段）
        setOriginalFields(JSON.parse(JSON.stringify(loadedFields))) // 深拷贝
      }
    } catch (error: any) {
      console.error('加载模板详情失败:', error)
      
      // 更详细的错误信息
      let errorMessage = '加载模板详情失败'
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        errorMessage = '网络连接失败，请检查后端服务是否运行（http://localhost:8000）'
      } else if (error.response) {
        errorMessage = error.response.data?.detail || `服务器错误: ${error.response.status}`
      } else if (error.message) {
        errorMessage = error.message
      }
      
      showErrorToast(errorMessage)
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
  // 处理发布版本
  const handlePublish = async () => {
    if (!templateId || !template?.version?.id) {
      showErrorToast('模板或版本信息不存在')
      return
    }

    if (template.version.status === 'published') {
      showErrorToast('版本已发布，无需重复发布')
      return
    }

    if (!confirm(`确定要发布版本 ${template.version.version} 吗？发布后版本将不可修改。`)) {
      return
    }

    try {
      setSaving(true)
      const token = localStorage.getItem('access_token')
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      
      await axios.post(
        `${apiBaseUrl}/api/v1/templates/${templateId}/versions/${template.version.id}/publish`,
        {},
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )
      
      showSuccessToast('版本发布成功')
      loadTemplate() // 重新加载模板信息
    } catch (error: any) {
      console.error('发布失败:', error)
      showErrorToast(error.response?.data?.detail || '发布失败')
    } finally {
      setSaving(false)
    }
  }

  // 处理创建新版本（从当前版本）
  const handleCreateNewVersion = async () => {
    if (!templateId || !template?.version?.id) {
      showErrorToast('模板或版本信息不存在')
      return
    }

    try {
      setSaving(true)
      const token = localStorage.getItem('access_token')
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      
      const response = await axios.post(
        `${apiBaseUrl}/api/v1/templates/${templateId}/versions/${template.version.id}/create-draft`,
        {},
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )
      
      showSuccessToast(response.data?.message || '已创建新版本')
      loadTemplate() // 重新加载模板信息
    } catch (error: any) {
      console.error('创建新版本失败:', error)
      showErrorToast(error.response?.data?.detail || '创建新版本失败')
    } finally {
      setSaving(false)
    }
  }

  // 处理废弃版本
  const handleDeprecateVersion = async () => {
    if (!templateId || !template?.version?.id) {
      showErrorToast('模板或版本信息不存在')
      return
    }

    if (!confirm(`确定要废弃版本 ${template.version.version} 吗？废弃后将不再使用此版本。`)) {
      return
    }

    try {
      setSaving(true)
      const token = localStorage.getItem('access_token')
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      
      await axios.post(
        `${apiBaseUrl}/api/v1/templates/${templateId}/versions/${template.version.id}/deprecate`,
        {},
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )
      
      showSuccessToast('版本已废弃')
      loadTemplate() // 重新加载模板信息
    } catch (error: any) {
      console.error('废弃版本失败:', error)
      showErrorToast(error.response?.data?.detail || '废弃版本失败')
    } finally {
      setSaving(false)
    }
  }

  // 自动生成Schema的函数（根据数据名称和数据类型生成简单结构）
  const generateAndUpdateSchema = () => {
    if (fields.length === 0) {
      console.log('没有字段，跳过Schema生成')
      return
    }

    try {
      const generatedSchema = generateSimpleJsonFromFields(fields)
      const schemaString = JSON.stringify(generatedSchema, null, 2)
      setTemplateSchema(schemaString)
      console.log('自动生成Schema:', generatedSchema)
      return generatedSchema
    } catch (error) {
      console.error('自动生成JSON Schema失败:', error)
      showErrorToast('自动生成JSON Schema失败')
      return null
    }
  }

  const handleSave = async () => {
    if (!formData.name.trim()) {
      showErrorToast('请输入模板名称')
      return
    }

    // 自动生成最新的Schema
    const latestSchema = generateAndUpdateSchema()
    if (!latestSchema) {
      return // 如果Schema生成失败，不继续保存
    }

    // 如果当前版本是已发布状态，提示用户会创建新版本
    if (template && template.version && template.version.status === 'published') {
      const confirmed = confirm(
        `当前版本 ${template.version.version} 已发布。保存修改将自动创建新版本（草稿状态）。\n\n是否继续？`
      )
      if (!confirmed) {
        return
      }
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
      console.log('保存模板，当前 fields 状态数量:', fields.length)
      console.log('保存模板，字段数量:', requestData.fields?.length || 0)
      console.log('保存模板，字段列表:', requestData.fields?.map((f: any) => ({ field_key: f.field_key, parent_field_id: f.parent_field_id })))
      console.log('保存模板，完整请求数据:', JSON.stringify(requestData, null, 2))
      console.log('保存模板，提示词内容:', requestData.prompt)
      console.log('保存模板，提示词类型:', typeof requestData.prompt)
      console.log('保存模板，提示词长度:', requestData.prompt ? requestData.prompt.length : 0)

      if (isNew) {
        // 创建新模板
        // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
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
        // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
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
        
        const message = template?.version?.status === 'published' 
          ? '已创建新版本（草稿状态），请发布新版本以生效' 
          : '模板更新成功'
        showSuccessToast(message)
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
  
  // 添加子字段
  const handleAddSubField = (parentField: TemplateField, parentIndex: number) => {
    if (!parentField.id) {
      showErrorToast('父字段ID不存在，无法添加子字段')
      return
    }
    
    const newFieldId = `new_subfield_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const parentKey = parentField.field_key || ''
    
    // 计算子字段的 field_key（格式：parent_key.sub_key）
    const timestamp = Date.now()
    const subFieldKey = parentKey ? `${parentKey}.sub_field_${timestamp}` : `sub_field_${timestamp}`
    
    // 找到父字段在原始 fields 数组中的索引
    const parentFieldIndex = fields.findIndex(f => f.id === parentField.id)
    if (parentFieldIndex < 0) {
      showErrorToast('找不到父字段')
      return
    }
    
    // 找到父字段的所有子字段，确定插入位置
    // 查找父字段之后的所有子字段
    let lastChildIndex = parentFieldIndex
    for (let i = parentFieldIndex + 1; i < fields.length; i++) {
      const field = fields[i]
      if (field.parent_field_id === parentField.id) {
        lastChildIndex = i
      } else {
        // 如果遇到不是当前父字段的子字段，停止查找
        break
      }
    }
    
    // 计算新的 sort_order（确保在父字段之后）
    const baseSortOrder = parentField.sort_order ?? parentFieldIndex
    // 找到最后一个子字段的 sort_order
    let maxChildSortOrder = baseSortOrder
    for (let i = parentFieldIndex + 1; i <= lastChildIndex && i < fields.length; i++) {
      const field = fields[i]
      if (field.parent_field_id === parentField.id && field.sort_order !== undefined) {
        maxChildSortOrder = Math.max(maxChildSortOrder, field.sort_order)
      }
    }
    const newSortOrder = maxChildSortOrder + 1
    
    const newSubField: TemplateField = {
      id: newFieldId,
      field_key: subFieldKey,
      field_name: '',
      data_name: '',
      data_type: 'string',
      is_required: false,
      parent_field_id: parentField.id,
      sort_order: newSortOrder
    }
    
    // 插入到最后一个子字段之后
    const newFields = [...fields]
    newFields.splice(lastChildIndex + 1, 0, newSubField)
    
    setFields(newFields)
    // 将新字段ID添加到新字段集合中
    setNewFieldIds(new Set([...newFieldIds, newFieldId]))
    
    // 自动展开以显示新添加的子字段
    if (!isFieldsExpanded) {
      onFieldsToggle()
    }
    
    showSuccessToast('子字段已添加')
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
              
              // 支持两种格式：
              // 1. 数组格式（扁平化字段列表）
              // 2. 对象格式（嵌套JSON结构）
              if (Array.isArray(jsonData)) {
                importedData = jsonData
              } else if (typeof jsonData === 'object' && jsonData !== null) {
                // 嵌套JSON结构：解析为字段列表
                importedData = parseNestedJsonToFields(jsonData)
              } else {
                showErrorToast('导入的文件格式错误：必须是JSON对象或数组格式')
                return
              }
              
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
  
  // 根据 Schema 更新字段
  const handleUpdateFieldsFromSchema = async () => {
    if (!templateId) {
      showErrorToast('模板ID不存在')
      return
    }

    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      
      // 根据模板名称选择正确的 Schema 文件
      const templateName = template?.name || formData.name || ''
      let schemaFileName = '/fixed_schema.json' // 默认使用发票模板的 Schema
      
      // 如果是"孔位类"模板，使用尺寸检验记录的 Schema
      if (templateName.includes('孔位类') || templateName.includes('孔类')) {
        schemaFileName = '/dimension_inspection_schema.json'
      }
      
      // 读取对应的 Schema 文件
      const schemaResponse = await fetch(schemaFileName)
      if (!schemaResponse.ok) {
        // 如果文件不存在，根据模板名称使用默认的 Schema
        let defaultSchema: any
        
        if (templateName.includes('孔位类') || templateName.includes('孔类')) {
          // 尺寸检验记录的默认 Schema
          defaultSchema = {
            doc_type: "dimension_inspection",
            form_title: null,
            drawing_no: null,
            part_name: null,
            part_no: null,
            date: null,
            inspector_name: null,
            overall_result: "unknown",
            remarks: null,
            items: [
              {
                item_no: null,
                inspection_item: null,
                spec_requirement: null,
                actual_value: null,
                judgement: "unknown",
                measurements: [
                  {
                    angle: null,
                    point_label: null,
                    value: null
                  }
                ],
                notes: null
              }
            ]
          }
        } else {
          // 发票模板的默认 Schema
          defaultSchema = {
            invoice_title: "string",
            invoice_no: "string",
            purchase_order: "string",
            reference_order: "string",
            supplier_no: "string",
            docdate: "string",
            buyer_info: {
              name: "string",
              tax_id: "string",
              company_code: "string"
            },
            seller_info: {
              name: "string",
              tax_id: "string"
            },
            items: [
              {
                LineId: "string",
                name: "string",
                part_no: "string",
                supplier_partno: "string",
                po_no: "string",
                unit: "string",
                quantity: "number | null",
                unit_price: "number | null",
                amount: "number",
                tax_rate: "string",
                tax_amount: "number"
              }
            ],
            total_amount_exclusive_tax: "number",
            currency: "string",
            total_tax_amount: "number",
            total_amount_inclusive_tax: {
              in_words: "string",
              in_figures: "number"
            },
            remarks: "string",
            issuer: "string"
          }
        }
        
        const url = apiBaseUrl ? `${apiBaseUrl}/api/v1/templates/${templateId}/update-fields-from-schema` : `/api/v1/templates/${templateId}/update-fields-from-schema`
        const response = await axios.post(url, {
          schema: defaultSchema
        }, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          timeout: 30000
        })
        
        if (response.data) {
          showSuccessToast('字段已根据 Schema 更新成功')
          // 重新加载模板数据
          await loadTemplate()
        }
        return
      }
      
      const schemaData = await schemaResponse.json()
      const url = apiBaseUrl ? `${apiBaseUrl}/api/v1/templates/${templateId}/update-fields-from-schema` : `/api/v1/templates/${templateId}/update-fields-from-schema`
      
      const response = await axios.post(url, {
        schema: schemaData
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        timeout: 30000
      })
      
      if (response.data) {
        showSuccessToast('字段已根据 Schema 更新成功')
        // 重新加载模板数据
        await loadTemplate()
      }
    } catch (error: any) {
      console.error('根据 Schema 更新字段失败:', error)
      let errorMessage = '根据 Schema 更新字段失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      showErrorToast(errorMessage)
    } finally {
      setLoading(false)
    }
  }
  
  // 处理导入的数据
  const processImportedData = (importedData: any[]) => {
    // 转换导入的数据为字段格式
    const fieldMap = new Map<string, TemplateField>() // 用于存储字段，key为field_key
    const importedFields: TemplateField[] = []
    
    // 第一遍：创建所有字段（不设置parent_field_id）
    importedData.forEach((item: any, index: number) => {
      const newFieldId = `imported_field_${Date.now()}_${index}_${Math.random().toString(36).substr(2, 9)}`
      const fieldKey = item['字段标识'] || item.field_key || `field_${fields.length + index + 1}`
      
      const field: TemplateField = {
        id: newFieldId,
        field_key: fieldKey,
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
        sort_order: fields.length + index,
        parent_field_id: undefined // 稍后设置
      }
      
      fieldMap.set(fieldKey, field)
      importedFields.push(field)
    })
    
    // 第二遍：建立父子关系：根据parent_field_key设置parent_field_id
    importedFields.forEach(field => {
      const item = importedData.find((item: any) => 
        (item['字段标识'] || item.field_key) === field.field_key
      )
      if (item && item.parent_field_key) {
        const parentField = fieldMap.get(item.parent_field_key)
        if (parentField && parentField.id) {
          field.parent_field_id = parentField.id
        }
      }
    })
    
    // 按sort_order排序，确保父字段在子字段之前
    importedFields.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    
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
  
  // 将字段表格转换为JSON（用于Excel导出）
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
  
  // 将字段转换为用于 Dify API 的 JSON 格式
  const convertFieldsToDifyJson = (): any[] => {
    return fields.map(field => ({
      key: field.field_key || '',
      fieldName: field.field_name || '',
      dataName: field.data_name || field.field_key || '',
      dataType: field.data_type || 'string',
      required: field.is_required || false,
      desc: field.description || '',
      example: field.example || ''
    }))
  }
  
  // 输出字段 JSON（用于 Dify API）
  const handleExportFieldsJson = () => {
    if (fields.length === 0) {
      showErrorToast('没有字段可导出')
      return
    }
    
    try {
      const fieldJson = convertFieldsToDifyJson()
      const jsonString = JSON.stringify(fieldJson, null, 2)
      
      // 创建 Blob 对象并下载
      const blob = new Blob([jsonString], { type: 'application/json;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
      link.download = `字段定义_${formData.name || '模板'}_${timestamp}.json`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      showSuccessToast(`成功导出 ${fields.length} 个字段的 JSON 定义`)
    } catch (error: any) {
      console.error('导出字段 JSON 失败:', error)
      showErrorToast(`导出失败: ${error.message || '未知错误'}`)
    }
  }
  
  // 调用DIFY API生成提示词
  const generatePromptWithDify = async (fieldJson: any[], promptText?: string, llmConfigId?: string) => {
    const isUpdate = !!promptText
    const actionText = isUpdate ? '更新' : '生成'
    
    try {
      setIsGeneratingPrompt(true)
      setGenerationProgress({ step: `正在转换字段信息为JSON格式...`, percentage: 10 })
      
      const token = localStorage.getItem('access_token')
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      
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
        const promptHashFromApi = response.data.data?.prompt_hash || null
        setAiSuggestedPrompt(generatedPrompt)
        setLastGeneratedPrompt(generatedPrompt)
        // 将生成的提示词自动设置到templatePrompt，并设置为只读
        setTemplatePrompt(generatedPrompt)
        setIsPromptReadOnly(true)  // 生成后设置为只读
        setPromptStale(false)  // 重置过期状态
        setPromptHash(promptHashFromApi)  // 保存hash
        
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
  
  // 获取模型配置列表
  const loadLlmConfigs = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = import.meta.env.VITE_API_URL || ''
      console.log('加载模型配置列表，API URL:', `${apiBaseUrl}/api/v1/config/llm/list`)
      
      const response = await axios.get(`${apiBaseUrl}/api/v1/config/llm/list`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      
      console.log('模型配置列表响应:', response.data)
      
      if (response.data && response.data.data) {
        const configs = response.data.data.filter((config: any) => config.is_active)
        console.log('过滤后的模型配置数量:', configs.length)
        setLlmConfigs(configs)
        
        // 如果有默认配置，自动选中
        const defaultConfig = configs.find((config: any) => config.is_default)
        if (defaultConfig) {
          setSelectedLlmConfigId(defaultConfig.id)
          console.log('选中默认配置:', defaultConfig.id, defaultConfig.name)
        } else if (configs.length > 0) {
          setSelectedLlmConfigId(configs[0].id)
          console.log('选中第一个配置:', configs[0].id, configs[0].name)
        } else {
          console.warn('没有可用的模型配置')
        }
      } else {
        console.warn('响应数据格式不正确:', response.data)
      }
    } catch (error: any) {
      console.error('获取模型配置列表失败:', error)
      console.error('错误详情:', error.response?.data)
      showErrorToast('获取模型配置列表失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  // 确认选择模型并执行提示词操作
  const handleConfirmModelSelection = async () => {
    if (!selectedLlmConfigId) {
      showErrorToast('请选择一个模型')
      return
    }
    
    onModelModalClose()
    
    if (pendingPromptAction === 'generate') {
      await executeGeneratePrompt()
    } else if (pendingPromptAction === 'update') {
      await executeUpdatePrompt()
    }
    
    setPendingPromptAction(null)
  }
  
  // 执行生成提示词
  const executeGeneratePrompt = async () => {
    if (fields.length === 0) {
      showErrorToast('请先添加字段')
      return
    }
    
    try {
      const fieldJson = convertFieldsToDifyJson()
      console.log('字段JSON:', JSON.stringify(fieldJson, null, 2))
      await generatePromptWithDify(fieldJson, undefined, selectedLlmConfigId)
    } catch (error) {
      // 错误已在generatePromptWithDify中处理
    }
  }
  
  // 执行更新提示词
  const executeUpdatePrompt = async () => {
    if (!templatePrompt.trim()) {
      showErrorToast('请先生成或输入提示词')
      return
    }
    
    if (fields.length === 0) {
      showErrorToast('请先添加字段')
      return
    }
    
    try {
      const fieldJson = convertFieldsToDifyJson()
      console.log('更新提示词 - 字段JSON:', JSON.stringify(fieldJson, null, 2))
      const updatedPrompt = await generatePromptWithDify(fieldJson, templatePrompt, selectedLlmConfigId)
      if (updatedPrompt) {
        setTemplatePrompt(updatedPrompt)
      }
    } catch (error) {
      // 错误已在generatePromptWithDify中处理
    }
  }
  
  // 按钮A：AI 输出提示词
  const handleGeneratePrompt = async () => {
    if (fields.length === 0) {
      showErrorToast('请先添加字段')
      return
    }
    
    // 加载模型列表并显示选择弹框
    await loadLlmConfigs()
    setPendingPromptAction('generate')
    onModelModalOpen()
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
    
    // 加载模型列表并显示选择弹框
    await loadLlmConfigs()
    setPendingPromptAction('update')
    onModelModalOpen()
  }
  
  // 监听字段和Schema变化，计算hash并检测prompt是否过期
  useEffect(() => {
    if (templatePrompt && promptHash && (fields.length > 0 || templateSchema)) {
      // 计算当前字段和Schema的hash
      const calculateHash = async () => {
        try {
          // 使用Web Crypto API计算hash（浏览器环境）
          const hashData = {
            fields: fields.map(f => ({
              field_key: f.field_key,
              field_name: f.field_name,
              data_type: f.data_type,
              is_required: f.is_required,
              description: f.description,
              sort_order: f.sort_order
            })).sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0)),
            schema: templateSchema ? (() => {
              try {
                return JSON.parse(templateSchema)
              } catch {
                return null
              }
            })() : null
          }
          const hashStr = JSON.stringify(hashData, Object.keys(hashData).sort())
          
          // 使用SHA-256计算hash
          const encoder = new TextEncoder()
          const data = encoder.encode(hashStr)
          const hashBuffer = await crypto.subtle.digest('SHA-256', data)
          const hashArray = Array.from(new Uint8Array(hashBuffer))
          const currentHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
          
          // 如果hash不一致，标记为过期
          if (currentHash !== promptHash) {
            setPromptStale(true)
          } else {
            setPromptStale(false)
          }
        } catch (error) {
          // hash计算失败，不标记过期（避免误报）
          console.warn('计算hash失败:', error)
        }
      }
      
      calculateHash()
    } else if (templatePrompt && !promptHash) {
      // 如果没有hash但有prompt，可能是旧数据，不标记过期
      setPromptStale(false)
    }
  }, [fields, templateSchema, templatePrompt, promptHash])

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
              {template?.version?.status === 'published' ? '保存（将创建新版本）' : '保存'}
            </Button>
            {template && template.version && (
              <>
                {template.version.status === 'draft' && (
                  <Button
                    onClick={handlePublish}
                    leftIcon={<FiUpload />}
                    colorScheme="green"
                    isLoading={saving}
                  >
                    发布版本
                  </Button>
                )}
                {template.version.status === 'published' && (
                  <>
                    <Button
                      onClick={handleCreateNewVersion}
                      leftIcon={<FiCopy />}
                      colorScheme="blue"
                      variant="outline"
                      isLoading={saving}
                    >
                      创建新版本
                    </Button>
                    <Button
                      onClick={handleDeprecateVersion}
                      leftIcon={<FiXCircle />}
                      colorScheme="red"
                      variant="outline"
                      isLoading={saving}
                    >
                      废弃版本
                    </Button>
                  </>
                )}
              </>
            )}
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
            
            {/* 版本信息显示 */}
            {template && template.version && (
              <Box mt={4} pt={4} borderTop="1px" borderColor="gray.200">
                <HStack spacing={4} flexWrap="wrap">
                  <Text fontSize="sm" color="gray.600">
                    模板状态: <Badge colorScheme="green">{template.status === 'enabled' ? '启用' : '停用'}</Badge>
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    版本号: <Badge colorScheme="blue">{template.version.version || '无'}</Badge>
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    版本状态: 
                    <Badge 
                      colorScheme={
                        template.version.status === 'published' ? 'green' :
                        template.version.status === 'deprecated' ? 'red' : 'gray'
                      }
                      ml={1}
                    >
                      {template.version.status === 'draft' ? '草稿' :
                       template.version.status === 'published' ? '已发布' :
                       template.version.status === 'deprecated' ? '已废弃' : template.version.status}
                    </Badge>
                  </Text>
                  {template.version.created_at && (
                    <Text fontSize="sm" color="gray.600">
                      创建时间: {new Date(template.version.created_at).toLocaleString('zh-CN')}
                    </Text>
                  )}
                  {template.version.published_at && (
                    <Text fontSize="sm" color="gray.600">
                      发布时间: {new Date(template.version.published_at).toLocaleString('zh-CN')}
                    </Text>
                  )}
                  {template.accuracy !== null && template.accuracy !== undefined && (
                    <Text fontSize="sm" color="gray.600">
                      准确率: <Badge colorScheme="orange">{(template.accuracy * 100).toFixed(1)}%</Badge>
                    </Text>
                  )}
                </HStack>
              </Box>
            )}
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
                  {templateId && (
                    <Button
                      onClick={handleUpdateFieldsFromSchema}
                      leftIcon={<FiRefreshCw />}
                      size="sm"
                      variant="outline"
                      colorScheme="purple"
                      title="根据 fixed_schema.json 更新字段结构为嵌套格式"
                      isLoading={loading}
                    >
                      从 Schema 更新
                    </Button>
                  )}
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
                      {isFieldsExpanded ? '收起' : `展开全部 (${sortedFields.length - 3})`}
                    </Button>
                  )}
                </HStack>
              </Flex>
              {sortedFields.length === 0 ? (
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
                        <Table.ColumnHeader>数据类型</Table.ColumnHeader>
                        <Table.ColumnHeader>是否必填</Table.ColumnHeader>
                        <Table.ColumnHeader>描述</Table.ColumnHeader>
                        <Table.ColumnHeader>示例值</Table.ColumnHeader>
                        <Table.ColumnHeader>操作</Table.ColumnHeader>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {/* 显示前3行 */}
                      {sortedFields.slice(0, 3).map((field, displayIndex) => {
                        const actualIndex = displayIndex
                        const fieldKey = field.id || `field-${actualIndex}`
                        const isNewField = field.id && newFieldIds.has(field.id)
                        const displayInfo = getFieldDisplayInfo(field, sortedFields)
                        return (
                          <Table.Row 
                            key={fieldKey}
                            bg={isNewField ? "red.50" : displayInfo.level > 0 ? "blue.50" : undefined}
                            borderColor={isNewField ? "red.200" : undefined}
                            borderWidth={isNewField ? "1px" : undefined}
                          >
                            <Table.Cell>
                              <Box display="flex" alignItems="center" width="100%">
                                {displayInfo.level > 0 && (
                                  <Box
                                    width={`${displayInfo.indent}px`}
                                    display="inline-flex"
                                    alignItems="center"
                                    justifyContent="flex-start"
                                    mr={1}
                                    height="100%"
                                    position="relative"
                                    flexShrink={0}
                                  >
                                    {/* 连接线 */}
                                    <Box
                                      width="2px"
                                      height="100%"
                                      bg="blue.300"
                                      position="absolute"
                                      left="8px"
                                    />
                                    {/* 连接点 */}
                                    <Box
                                      width="8px"
                                      height="8px"
                                      borderRadius="full"
                                      bg="blue.400"
                                      position="absolute"
                                      left="4px"
                                      top="50%"
                                      transform="translateY(-50%)"
                                      zIndex={1}
                                    />
                                  </Box>
                                )}
                                <Input
                                  size="sm"
                                  value={field.field_key}
                                  onChange={(e) => handleFieldChange(actualIndex, { field_key: e.target.value })}
                                  placeholder={displayInfo.isNested ? "如：buyer_info.name" : "如：invoice_no"}
                                  flex={1}
                                  fontFamily={displayInfo.isNested ? "monospace" : "inherit"}
                                  fontSize={displayInfo.isNested ? "xs" : "sm"}
                                />
                              </Box>
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
                                value={field.data_type || 'string'}
                                onChange={(e) => handleFieldChange(actualIndex, { data_type: e.target.value })}
                                style={{
                                  width: '100%',
                                  padding: '4px',
                                  border: '1px solid #e2e8f0',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}
                              >
                                <option value="string">string</option>
                                <option value="number">number</option>
                                <option value="boolean">boolean</option>
                                <option value="date">date</option>
                                <option value="datetime">datetime</option>
                                <option value="enum">enum</option>
                                <option value="object">object</option>
                                <option value="array">array</option>
                              </select>
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
                              <Box display="flex" justifyContent="center" gap={1}>
                                <IconButton
                                  aria-label="添加子字段"
                                  icon={<FiPlus />}
                                  size="xs"
                                  bg="white"
                                  color="blue.500"
                                  borderRadius="full"
                                  border="1px solid"
                                  borderColor="gray.300"
                                  _hover={{ bg: "blue.50", borderColor: "blue.400" }}
                                  _active={{ bg: "blue.100" }}
                                  title="添加子字段"
                                  onClick={() => {
                                    const fieldInSorted = sortedFields[actualIndex]
                                    if (fieldInSorted) {
                                      handleAddSubField(fieldInSorted, actualIndex)
                                    }
                                  }}
                                />
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
                      {isFieldsExpanded && sortedFields.length > 3 && (
                        <>
                          {/* 分隔行提示 */}
                          <Table.Row bg="gray.50">
                            <Table.Cell colSpan={8} py={2} textAlign="center">
                              <Text fontSize="xs" color="gray.500" fontWeight="medium">
                                ─── 以下为展开的字段 ({sortedFields.length - 3} 个) ───
                              </Text>
                            </Table.Cell>
                          </Table.Row>
                          {sortedFields.slice(3).map((field, displayIndex) => {
                            const actualIndex = displayIndex + 3
                            const fieldKey = field.id || `field-${actualIndex}`
                            const isNewField = field.id && newFieldIds.has(field.id)
                            const displayInfo = getFieldDisplayInfo(field, sortedFields)
                            return (
                              <Table.Row 
                                key={fieldKey}
                                bg={isNewField ? "red.50" : displayInfo.level > 0 ? "blue.50" : undefined}
                                borderColor={isNewField ? "red.200" : undefined}
                                borderWidth={isNewField ? "1px" : undefined}
                              >
                                <Table.Cell>
                                  <Box display="flex" alignItems="center" width="100%">
                                    {displayInfo.level > 0 && (
                                      <Box
                                        width={`${displayInfo.indent}px`}
                                        display="inline-flex"
                                        alignItems="center"
                                        justifyContent="flex-start"
                                        mr={1}
                                        height="100%"
                                        position="relative"
                                        flexShrink={0}
                                      >
                                        {/* 连接线 */}
                                        <Box
                                          width="2px"
                                          height="100%"
                                          bg="blue.300"
                                          position="absolute"
                                          left="8px"
                                        />
                                        {/* 连接点 */}
                                        <Box
                                          width="8px"
                                          height="8px"
                                          borderRadius="full"
                                          bg="blue.400"
                                          position="absolute"
                                          left="4px"
                                          top="50%"
                                          transform="translateY(-50%)"
                                          zIndex={1}
                                        />
                                      </Box>
                                    )}
                                    <Input
                                      size="sm"
                                      value={field.field_key}
                                      onChange={(e) => handleFieldChange(actualIndex, { field_key: e.target.value })}
                                      placeholder={displayInfo.isNested ? "如：buyer_info.name" : "如：invoice_no"}
                                      flex={1}
                                      fontFamily={displayInfo.isNested ? "monospace" : "inherit"}
                                      fontSize={displayInfo.isNested ? "xs" : "sm"}
                                    />
                                  </Box>
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
                                    value={field.data_type || 'string'}
                                    onChange={(e) => handleFieldChange(actualIndex, { data_type: e.target.value })}
                                    style={{
                                      width: '100%',
                                      padding: '4px',
                                      border: '1px solid #e2e8f0',
                                      borderRadius: '4px',
                                      fontSize: '12px'
                                    }}
                                  >
                                    <option value="string">string</option>
                                    <option value="number">number</option>
                                    <option value="boolean">boolean</option>
                                    <option value="date">date</option>
                                    <option value="datetime">datetime</option>
                                    <option value="enum">enum</option>
                                    <option value="object">object</option>
                                    <option value="array">array</option>
                                  </select>
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
                                  <Box display="flex" justifyContent="center" gap={1}>
                                    <IconButton
                                      aria-label="添加子字段"
                                      icon={<FiPlus />}
                                      size="xs"
                                      bg="white"
                                      color="blue.500"
                                      borderRadius="full"
                                      border="1px solid"
                                      borderColor="gray.300"
                                      _hover={{ bg: "blue.50", borderColor: "blue.400" }}
                                      _active={{ bg: "blue.100" }}
                                      title="添加子字段"
                                      onClick={() => {
                                        const fieldInSorted = sortedFields[actualIndex]
                                        if (fieldInSorted) {
                                          handleAddSubField(fieldInSorted, actualIndex)
                                        }
                                      }}
                                    />
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
                {!templatePrompt || templatePrompt.trim() === '' ? (
                  <Button
                    onClick={handleGeneratePrompt}
                    leftIcon={<FiCheckCircle />}
                    size="sm"
                    colorScheme="blue"
                    variant="outline"
                    isLoading={isGeneratingPrompt}
                    loadingText="生成中..."
                    isDisabled={isGeneratingPrompt || (template?.version?.status !== 'draft' && template?.version?.status)}
                  >
                    AI 输出提示词
                  </Button>
                ) : (
                  <Button
                    onClick={handleUpdatePrompt}
                    leftIcon={<FiCheckCircle />}
                    size="sm"
                    colorScheme="blue"
                    variant="outline"
                    isLoading={isGeneratingPrompt}
                    loadingText="更新中..."
                    isDisabled={isGeneratingPrompt || (template?.version?.status !== 'draft' && template?.version?.status)}
                  >
                    AI 更新提示词
                  </Button>
                )}
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
                  <Flex justify="space-between" align="center" mb={2}>
                    <Text fontSize="md" fontWeight="medium">提示词</Text>
                    <HStack spacing={2}>
                      {template?.version?.prompt_status === 'generated' && (
                        <Badge colorScheme="green" fontSize="xs">
                          已生成
                        </Badge>
                      )}
                      {template?.version?.status && template?.version?.status !== 'draft' && (
                        <Badge colorScheme="gray" fontSize="xs">
                          仅草稿版本可更新
                        </Badge>
                      )}
                    </HStack>
                  </Flex>
                  <Textarea
                    value={templatePrompt || ''}
                    readOnly={true}  // 始终只读，不允许手动编辑
                    placeholder={templatePrompt ? "提示词已生成，请使用'AI 更新提示词'按钮进行更新" : "请使用'AI 输出提示词'按钮生成提示词"}
                    rows={10}
                    fontSize="sm"
                    resize="vertical"
                    bg="gray.50"  // 始终使用灰色背景，表示只读
                    borderColor="gray.300"
                    cursor="not-allowed"  // 始终显示不可编辑光标
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
                <HStack gap={2}>
                  <Button
                    size="sm"
                    colorScheme="green"
                    variant="outline"
                    leftIcon={<FiRefreshCw />}
                    onClick={generateAndUpdateSchema}
                  >
                    自动生成
                  </Button>
                  <Button
                    size="sm"
                    colorScheme="blue"
                    variant="outline"
                    leftIcon={<FiCheckCircle />}
                    onClick={validateAndFixJsonSchema}
                  >
                    校验及纠正
                  </Button>
                </HStack>
              </Flex>
              <VStack spacing={4} align="stretch">
                {/* 新增字段提醒 */}
                {hasNewFields && (
                  <Box
                    p={3}
                    bg="orange.50"
                    borderRadius="md"
                    border="1px"
                    borderColor="orange.300"
                  >
                    <Flex align="start" gap={2}>
                      <Icon as={FiAlertCircle} color="orange.500" mt={0.5} boxSize={5} />
                      <Box flex={1}>
                        <Text fontSize="sm" fontWeight="medium" color="orange.700" mb={1}>
                          检测到新增字段，请更新 JSON Schema
                        </Text>
                        <Text fontSize="xs" color="orange.600" mb={2}>
                          您已添加了以下新字段，请确保在 JSON Schema 的 properties 中包含这些字段：
                        </Text>
                        <VStack align="start" spacing={1} ml={4}>
                          {newFieldsList.map((field, index) => (
                            <Text key={index} fontSize="xs" color="orange.700">
                              • <Text as="span" fontWeight="medium">{field.field_key}</Text>
                              {field.field_name && ` (${field.field_name})`}
                              {field.data_type && ` - 类型: ${field.data_type}`}
                            </Text>
                          ))}
                        </VStack>
                        <Text fontSize="xs" color="orange.600" mt={2}>
                          提示：JSON Schema 的 properties 中应包含所有字段的 key，否则识别结果可能不完整。
                        </Text>
                      </Box>
                    </Flex>
                  </Box>
                )}
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
      
      {/* 模型选择弹框 */}
      <DialogRoot open={isModelModalOpen} onOpenChange={(e) => setIsModelModalOpen(e.open)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>请选择要输出提示词的模型</DialogTitle>
            <DialogCloseTrigger />
          </DialogHeader>
          <DialogBody>
            <VStack spacing={4} align="stretch">
              {llmConfigs.length === 0 ? (
                <Text color="gray.500" textAlign="center" py={4}>
                  暂无可用模型配置
                </Text>
              ) : (
                <Box>
                  <Text fontSize="sm" fontWeight="medium" mb={2}>
                    请选择模型配置：
                  </Text>
                  <select
                    value={selectedLlmConfigId}
                    onChange={(e) => setSelectedLlmConfigId(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px',
                      fontSize: '14px',
                      backgroundColor: 'white',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="">请选择模型配置</option>
                    {llmConfigs.map((config) => (
                      <option key={config.id} value={config.id}>
                        {config.name}{config.is_default ? ' (默认)' : ''}
                      </option>
                    ))}
                  </select>
                  {selectedLlmConfigId && (() => {
                    const selectedConfig = llmConfigs.find(c => c.id === selectedLlmConfigId)
                    return selectedConfig ? (
                      <Box mt={3} p={3} bg="gray.50" borderRadius="md">
                        <HStack spacing={2} mb={1}>
                          <Text fontSize="sm" fontWeight="medium">{selectedConfig.name}</Text>
                          {selectedConfig.is_default && (
                            <Badge colorScheme="green" fontSize="xs">默认</Badge>
                          )}
                        </HStack>
                        {selectedConfig.description && (
                          <Text fontSize="xs" color="gray.600" mt={1}>
                            {selectedConfig.description}
                          </Text>
                        )}
                      </Box>
                    ) : null
                  })()}
                </Box>
              )}
            </VStack>
          </DialogBody>
          <DialogFooter>
            <Button variant="ghost" mr={3} onClick={onModelModalClose}>
              取消
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleConfirmModelSelection}
              isDisabled={!selectedLlmConfigId || llmConfigs.length === 0}
            >
              确认
            </Button>
          </DialogFooter>
        </DialogContent>
      </DialogRoot>
    </Box>
  )
}

export default TemplateEditEnhanced

