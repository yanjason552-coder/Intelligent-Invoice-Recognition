/**
 * 将 JSON Schema 转换为模板字段列表
 */

export interface TemplateField {
  id?: string
  field_key: string
  field_name: string
  data_name?: string
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

/**
 * 将 JSON Schema 转换为字段列表
 * @param schema JSON Schema 对象
 * @param parentFieldId 父字段ID（用于嵌套字段）
 * @param parentKey 父字段的key（用于构建子字段的field_key）
 * @param sortOrderStart 起始排序号
 * @returns 字段列表
 */
export function schemaToFields(
  schema: any,
  parentFieldId?: string,
  parentKey: string = '',
  sortOrderStart: number = 0
): TemplateField[] {
  const fields: TemplateField[] = []
  let sortOrder = sortOrderStart

  // 字段名称映射（中文名称）
  const fieldNameMap: Record<string, string> = {
    invoice_title: '发票标题',
    invoice_no: '发票号码',
    invoice_number: '发票号码',
    docdate: '开票日期',
    issue_date: '开票日期',
    buyer_info: '采购方信息',
    seller_info: '供应商信息',
    items: '行项目',
    total_amount_exclusive_tax: '不含税合计',
    total_tax_amount: '税额合计',
    total_amount_inclusive_tax: '含税合计',
    remarks: '备注',
    issuer: '开票人',
    name: '名称',
    tax_id: '税号',
    model: '型号',
    unit: '单位',
    quantity: '数量',
    unit_price: '单价',
    amount: '金额',
    tax_rate: '税率',
    tax_amount: '税额',
    in_words: '大写金额',
    in_figures: '小写金额',
    purchase_order: '采购订单号码',
    reference_order: '销售方订单号码',
    supplier_no: '供应商编号',
    part_no: '零件号',
    invoice_array: '发票数组'
  }

  // 字段描述映射
  const fieldDescriptionMap: Record<string, string> = {
    invoice_title: '发票标题',
    invoice_no: '发票号码。如果内容中包含不同的发票号码，请把每个发票信息都作为独立对象，放入invoice_array数组中',
    invoice_number: '发票号码。如果内容中包含不同的发票号码，请把每个发票信息都作为独立对象，放入invoice_array数组中',
    docdate: '开票日期，统一输出为YYYY-MM-DD格式',
    issue_date: '开票日期，统一输出为YYYY-MM-DD格式',
    buyer_info: '采购方信息',
    seller_info: '供应商信息',
    items: '行项目数组。发票中的"项目名称"部分可能包含多个商品或服务，甚至可能包含折扣（金额为负数）。需要将每一个项目都作为一个独立的对象，放入items数组中',
    total_amount_exclusive_tax: '不含税合计。对于金额，只保留数字，去除货币符号（如¥）',
    total_tax_amount: '税额合计。对于金额，只保留数字，去除货币符号（如¥）',
    total_amount_inclusive_tax: '含税合计。对于金额，只保留数字，去除货币符号（如¥）',
    remarks: '备注。如果某一项信息在发票中不存在，请使用null或者空字符串""作为值',
    issuer: '开票人',
    name: '名称',
    tax_id: '税号',
    model: '型号',
    unit: '单位',
    quantity: '数量。对于数量，只保留数字，去除货币符号',
    unit_price: '单价。对于金额，只保留数字，去除货币符号（如¥）',
    amount: '金额。对于金额，只保留数字，去除货币符号（如¥）',
    tax_rate: '税率，输出百分比字符串，例如"13%"',
    tax_amount: '税额。对于金额，只保留数字，去除货币符号（如¥）',
    in_words: '大写金额',
    in_figures: '小写金额。对于金额，只保留数字，去除货币符号（如¥）',
    purchase_order: '采购订单号码（采购方订单）',
    reference_order: '销售方订单号码（销售方订单）',
    supplier_no: '供应商编号（销售方在采购方公司的编号）',
    part_no: '零件号',
    invoice_array: '发票数组。如果内容中包含不同的发票号码，请把每个发票信息都作为独立对象，放入此数组中'
  }

  // 获取字段的中文名称
  const getFieldName = (key: string): string => {
    return fieldNameMap[key] || key
  }

  // 获取字段描述
  const getFieldDescription = (key: string): string => {
    return fieldDescriptionMap[key] || ''
  }

  // 获取数据类型
  const getDataType = (type: string | string[]): string => {
    if (Array.isArray(type)) {
      return type[0] // 取第一个类型
    }
    return type || 'string'
  }

  // 处理对象类型的字段
  const processObject = (key: string, objSchema: any, parentId?: string, parentKeyPrefix: string = ''): TemplateField[] => {
    const result: TemplateField[] = []
    // 对于对象类型，field_key 就是 key 本身，不包含父级前缀
    const currentKey = key
    const fieldId = `field_${parentKeyPrefix ? `${parentKeyPrefix}_` : ''}${key}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // 创建父字段（对象类型）
    const parentField: TemplateField = {
      id: fieldId,
      field_key: currentKey,
      field_name: getFieldName(key),
      data_name: key,
      data_type: 'object',
      is_required: false,
      description: getFieldDescription(key) || '',
      sort_order: sortOrder++,
      parent_field_id: parentId
    }
    result.push(parentField)

    // 处理对象的属性
    if (objSchema.properties) {
      Object.keys(objSchema.properties).forEach(subKey => {
        const subSchema = objSchema.properties[subKey]
        // 子字段的 field_key 也是 key 本身，通过 parent_field_id 建立关系
        const subFields = processField(subKey, subSchema, fieldId, currentKey)
        result.push(...subFields)
      })
    }

    return result
  }

  // 处理数组类型的字段
  const processArray = (key: string, arraySchema: any, parentId?: string, parentKeyPrefix: string = ''): TemplateField[] => {
    const result: TemplateField[] = []
    // 对于数组类型，field_key 就是 key 本身，不包含父级前缀
    const currentKey = key
    const fieldId = `field_${parentKeyPrefix ? `${parentKeyPrefix}_` : ''}${key}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // 创建父字段（数组类型）
    const parentField: TemplateField = {
      id: fieldId,
      field_key: currentKey,
      field_name: getFieldName(key),
      data_name: key,
      data_type: 'array',
      is_required: false,
      description: getFieldDescription(key) || '',
      sort_order: sortOrder++,
      parent_field_id: parentId
    }
    result.push(parentField)

    // 处理数组项（items）
    if (arraySchema.items) {
      const itemsSchema = arraySchema.items
      if (itemsSchema.type === 'object' && itemsSchema.properties) {
        // 数组项是对象，需要创建子字段
        // 子字段的 field_key 也是 key 本身，通过 parent_field_id 建立关系
        Object.keys(itemsSchema.properties).forEach(subKey => {
          const subSchema = itemsSchema.properties[subKey]
          const subFields = processField(subKey, subSchema, fieldId, currentKey)
          result.push(...subFields)
        })
      }
    }

    return result
  }

  // 处理单个字段
  const processField = (
    key: string,
    fieldSchema: any,
    parentId?: string,
    parentKeyPrefix: string = ''
  ): TemplateField[] => {
    const result: TemplateField[] = []
    // field_key 就是 key 本身，不包含父级前缀，嵌套关系通过 parent_field_id 建立
    const currentKey = key
    const fieldId = `field_${parentKeyPrefix ? `${parentKeyPrefix}_` : ''}${key}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const dataType = getDataType(fieldSchema.type || 'string')

    // 处理不同类型的字段
    if (dataType === 'object') {
      return processObject(key, fieldSchema, parentId, parentKeyPrefix)
    } else if (dataType === 'array') {
      return processArray(key, fieldSchema, parentId, parentKeyPrefix)
    } else {
      // 基本类型字段
      const field: TemplateField = {
        id: fieldId,
        field_key: currentKey,
        field_name: getFieldName(key),
        data_name: key,
        data_type: dataType === 'number' ? 'number' : 'string',
        is_required: false,
        description: fieldSchema.description || getFieldDescription(key) || '',
        example: fieldSchema.example || '',
        sort_order: sortOrder++,
        parent_field_id: parentId
      }
      result.push(field)
    }

    return result
  }

  // 如果传入的是完整的 Schema 对象
  if (schema.properties) {
    Object.keys(schema.properties).forEach(key => {
      const fieldSchema = schema.properties[key]
      const fieldFields = processField(key, fieldSchema, parentFieldId, parentKey)
      fields.push(...fieldFields)
    })
  } else {
    // 如果传入的是直接的字段定义对象
    Object.keys(schema).forEach(key => {
      const fieldSchema = schema[key]
      const fieldFields = processField(key, fieldSchema, parentFieldId, parentKey)
      fields.push(...fieldFields)
    })
  }

  return fields
}

/**
 * 从提供的 JSON Schema 生成字段列表
 * 严格按照新的 Schema 结构：invoice_array 为顶层数组
 */
export function generateFieldsFromInvoiceSchema(): TemplateField[] {
  // 严格按照用户提供的 JSON Schema
  const standardSchema = {
    properties: {
      invoice_array: {
        type: "array",
        items: {
          type: "object",
          properties: {
            invoice_title: { type: "string" },
            invoice_number: { type: "string" },
            issue_date: { type: "string" },
            supplier_no: { type: "string" },
            items: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  name: { type: "string" },
                  part_no: { type: "string" },
                  unit: { type: "string" },
                  purchase_order: { type: "string" },
                  quantity: { type: ["number", "null"] },
                  unit_price: { type: ["number", "null"] },
                  amount: { type: "number" },
                  tax_rate: { type: "string" },
                  tax_amount: { type: "number" }
                }
              }
            },
            total_amount_exclusive_tax: { type: "number" },
            total_tax_amount: { type: "number" },
            remarks: { type: "string" },
            issuer: { type: "string" }
          }
        }
      }
    }
  }

  return schemaToFields(standardSchema)
}
