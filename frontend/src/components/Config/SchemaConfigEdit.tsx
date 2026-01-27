import { Box, Text, Flex, VStack, Input, Textarea } from "@chakra-ui/react"
import { FiSave, FiCheckCircle, FiXCircle, FiArrowLeft } from "react-icons/fi"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Checkbox } from "@/components/ui/checkbox"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'

interface SchemaData {
  id?: string
  name: string
  version: string
  schema_definition: any
  is_active: boolean
  is_default: boolean
  description?: string
}

interface SchemaConfigEditProps {
  schemaData?: SchemaData | null
  isEdit?: boolean
}

const SchemaConfigEdit = ({ schemaData, isEdit = false }: SchemaConfigEditProps) => {
  const [schema, setSchema] = useState<SchemaData>({
    name: '',
    version: '1.0.0',
    schema_definition: {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {},
      "required": []
    },
    is_active: true,
    is_default: false,
    description: ''
  })
  const [loading, setLoading] = useState(false)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string; schema_info?: any } | null>(null)
  const [schemaText, setSchemaText] = useState('')
  const { showSuccessToast, showErrorToast } = useCustomToast()

  useEffect(() => {
    if (schemaData) {
      const schemaDef = typeof schemaData.schema_definition === 'string'
        ? JSON.parse(schemaData.schema_definition)
        : schemaData.schema_definition
      setSchema({
        ...schemaData,
        schema_definition: schemaDef
      })
      setSchemaText(JSON.stringify(schemaDef, null, 2))
    } else {
      // 创建模式，初始化schemaText
      setSchemaText(JSON.stringify(schema.schema_definition, null, 2))
    }
  }, [schemaData])

  const handleSave = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')

      const dataToSave = {
        ...schema,
        schema_definition: JSON.stringify(schema.schema_definition, null, 2)
      }

      if (isEdit && schema.id) {
        await axios.patch(`/api/v1/config/schemas/${schema.id}`, dataToSave, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        showSuccessToast('Schema更新成功')
      } else {
        await axios.post('/api/v1/config/schemas', dataToSave, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        showSuccessToast('Schema创建成功')
      }

      // 返回列表页面
      const event = new CustomEvent('openTab', {
        detail: {
          id: 'schema-list',
          title: 'Schema配置列表',
          type: 'schema-list',
          data: null
        }
      })
      window.dispatchEvent(event)
      window.location.href = '/'

    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const handleValidate = async () => {
    try {
      setValidating(true)
      setValidationResult(null)

      const token = localStorage.getItem('access_token')
      const response = await axios.post('/api/v1/config/schemas/validate', {
        schema_definition: JSON.stringify(schema.schema_definition, null, 2)
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      setValidationResult(response.data)
    } catch (error: any) {
      setValidationResult({
        valid: false,
        message: error.response?.data?.message || '验证失败'
      })
    } finally {
      setValidating(false)
    }
  }

  const handleBack = () => {
    const event = new CustomEvent('openTab', {
      detail: {
        id: 'schema-list',
        title: 'Schema配置列表',
        type: 'schema-list',
        data: null
      }
    })
    window.dispatchEvent(event)
    window.location.href = '/'
  }

  const handleSchemaDefinitionChange = (value: string) => {
    setSchemaText(value) // 总是更新文本内容

    try {
      const parsed = JSON.parse(value)
      setSchema({ ...schema, schema_definition: parsed })
      // 成功解析时清除验证结果
      if (validationResult && !validationResult.valid) {
        setValidationResult(null)
      }
    } catch (error) {
      // JSON格式错误时，只在有实际内容时显示错误
      // 空内容或编辑过程中的临时错误不显示
      if (value.trim() && value.trim() !== '{' && value.trim() !== '[') {
        setValidationResult({
          valid: false,
          message: 'JSON格式错误，请检查语法'
        })
      } else {
        setValidationResult(null)
      }
      // 不更新schema_definition，保持上一次的正确值
    }
  }

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={6}>
        <Flex align="center" gap={4}>
          <Button onClick={handleBack} variant="ghost" size="sm">
            <FiArrowLeft style={{ marginRight: '8px' }} />
            返回
          </Button>
          <Text fontSize="xl" fontWeight="bold">
            {isEdit ? `编辑Schema: ${schema.name}` : '创建Schema'}
          </Text>
        </Flex>
        <Flex gap={2}>
          <Button
            variant="outline"
            onClick={handleValidate}
            disabled={validating}
          >
            {validating ? '验证中...' : '验证Schema'}
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            <FiSave style={{ marginRight: '8px' }} />
            {loading ? '保存中...' : '保存Schema'}
          </Button>
        </Flex>
      </Flex>

      {validationResult && (
        <Box
          mb={4}
          p={3}
          borderRadius="md"
          bg={validationResult.valid ? 'green.50' : 'red.50'}
          border="1px"
          borderColor={validationResult.valid ? 'green.200' : 'red.200'}
        >
          <Flex align="center" gap={2}>
            {validationResult.valid ? (
              <FiCheckCircle color="green" />
            ) : (
              <FiXCircle color="red" />
            )}
            <Text color={validationResult.valid ? 'green.700' : 'red.700'}>
              {validationResult.message}
            </Text>
          </Flex>
          {validationResult.valid && validationResult.schema_info && (
            <Box mt={2} ml={6}>
              <Text fontSize="sm" color="green.700">
                类型: {validationResult.schema_info.type} |
                属性数量: {validationResult.schema_info.properties_count} |
                必填字段: {validationResult.schema_info.required_fields.join(', ') || '无'}
              </Text>
            </Box>
          )}
        </Box>
      )}

      <Box
        pt={4}
        maxH="calc(100vh - 200px)"
        overflowY="auto"
        overflowX="hidden"
        pr={2}
        className="custom-scrollbar"
      >
        <VStack gap={6} align="stretch" maxW="1200px">
          {/* 基础信息 */}
          <Box>
            <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
              基础信息
            </Text>
            <VStack gap={4}>
              <Field label="Schema名称" required>
                <Input
                  value={schema.name}
                  onChange={(e) => setSchema({ ...schema, name: e.target.value })}
                  placeholder="例如：发票识别结果Schema"
                />
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Schema的唯一标识名称
                </Text>
              </Field>

              <Field label="版本号">
                <Input
                  value={schema.version}
                  onChange={(e) => setSchema({ ...schema, version: e.target.value })}
                  placeholder="1.0.0"
                />
                <Text fontSize="xs" color="gray.500" mt={1}>
                  遵循语义化版本控制，如：1.0.0、1.1.0、2.0.0
                </Text>
              </Field>

              <Field label="描述">
                <Textarea
                  value={schema.description || ''}
                  onChange={(e) => setSchema({ ...schema, description: e.target.value })}
                  placeholder="Schema的描述信息（可选）"
                  rows={2}
                />
              </Field>
            </VStack>
          </Box>

          {/* Schema定义 */}
          <Box>
            <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
              Schema定义 (JSON格式)
            </Text>
            <Field label="JSON Schema" required>
              <Textarea
                value={schemaText}
                onChange={(e) => handleSchemaDefinitionChange(e.target.value)}
                placeholder='{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "invoice_no": {
      "type": "string",
      "description": "发票号码"
    }
  },
  "required": ["invoice_no"]
}'
                rows={20}
                fontFamily="monospace"
                fontSize="sm"
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                输入JSON Schema定义，支持JSON Schema Draft 7规范。
                <a
                  href="https://json-schema.org/understanding-json-schema/"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: '#3182ce', textDecoration: 'underline' }}
                >
                  查看JSON Schema文档
                </a>
              </Text>
            </Field>
          </Box>

          {/* 设置 */}
          <Box>
            <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
              设置
            </Text>
            <VStack gap={4}>
              <Flex align="center" gap={4}>
                <Field>
                  <Checkbox
                    checked={schema.is_active}
                    onCheckedChange={({ checked }) => setSchema({ ...schema, is_active: checked === true })}
                  >
                    启用Schema
                  </Checkbox>
                </Field>

                <Field>
                  <Checkbox
                    checked={schema.is_default}
                    onCheckedChange={({ checked }) => setSchema({ ...schema, is_default: checked === true })}
                  >
                    设为默认Schema
                  </Checkbox>
                </Field>
              </Flex>
              <Text fontSize="xs" color="gray.500">
                • 启用Schema：控制该Schema是否可被使用<br/>
                • 默认Schema：新创建的模型配置将自动关联此Schema
              </Text>
            </VStack>
          </Box>
        </VStack>
      </Box>
    </Box>
  )
}

export default SchemaConfigEdit
