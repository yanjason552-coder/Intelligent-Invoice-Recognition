import {
  VStack,
  HStack,
  Text,
  Input,
  Button,
  Badge,
  Box,
  DialogTitle,
} from "@chakra-ui/react"
import { Field } from "@/components/ui/field"
import { useState, useEffect } from "react"
import { FiChevronDown, FiChevronUp } from "react-icons/fi"
import useCustomToast from '@/hooks/useCustomToast'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogBody,
  DialogFooter,
  DialogCloseTrigger,
} from "@/components/ui/dialog"

interface RecognitionParams {
  model_config_id: string
  recognition_mode: string
  template_strategy: string
  template_id?: string
  template_version?: string
  output_schema_id?: string
  language: string
  confidence_threshold: number
  page_range: string
  enhance_options: string
  callback_url?: string
}

interface RecognitionParamsModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (params: RecognitionParams) => void
  defaultParams?: Partial<RecognitionParams>
}

interface ConfigOptions {
  model_configs: Array<{
    id: string
    name: string
    provider: string
    cost_level: string
    default_mode: string
    allowed_modes: string[]
    model_name: string
    model_version?: string
    default_schema_id?: string
  }>
  modes: Array<{
    value: string
    label: string
  }>
  schemas: Array<{
    id: string
    name: string
    version: string
    is_default: boolean
    description?: string
  }>
  template_strategies: Array<{
    value: string
    label: string
  }>
  templates: Array<{
    id: string
    name: string
    template_type: string
    description?: string
    status: string
    schema_id?: string
    default_schema_id?: string
    current_version?: string
    accuracy?: number
  }>
  defaults: {
    language: string
    confidence_threshold: number
    page_range: string
    enhance_options: string
  }
}

const RecognitionParamsModal = ({
  isOpen,
  onClose,
  onConfirm,
  defaultParams = {},
}: RecognitionParamsModalProps) => {
  const { showErrorToast } = useCustomToast()
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false)
  const [configOptions, setConfigOptions] = useState<ConfigOptions | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const [params, setParams] = useState<RecognitionParams>({
    model_config_id: "",
    recognition_mode: "",
    template_strategy: "auto",
    language: "zh-CN",
    confidence_threshold: 0.8,
    page_range: "all",
    enhance_options: "auto",
    ...defaultParams,
  })

  const loadConfigOptions = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        showErrorToast('请先登录')
        return
      }

      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await axios.get(
        `${apiBaseUrl}/api/v1/config/recognition-config/options`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data) {
        setConfigOptions(response.data)
        
        // 设置默认值
        if (response.data.model_configs.length > 0 && !params.model_config_id) {
          const defaultConfig = response.data.model_configs[0]
          setParams(prev => ({
            ...prev,
            model_config_id: defaultConfig.id,
            recognition_mode: defaultConfig.default_mode || defaultConfig.allowed_modes[0] || "llm_extract",
            output_schema_id: defaultConfig.default_schema_id || response.data.schemas.find((s: any) => s.is_default)?.id,
          }))
        }
      }
    } catch (error: any) {
      console.error('加载配置选项失败:', error)
      showErrorToast(error?.response?.data?.detail || '加载配置选项失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 加载配置选项
  useEffect(() => {
    if (isOpen) {
      loadConfigOptions()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  // 当选择模型配置时，更新识别方式和默认schema
  const handleModelConfigChange = (modelConfigId: string) => {
    const modelConfig = configOptions?.model_configs.find(m => m.id === modelConfigId)
    if (modelConfig) {
      setParams(prev => ({
        ...prev,
        model_config_id: modelConfigId,
        recognition_mode: modelConfig.default_mode || modelConfig.allowed_modes[0] || prev.recognition_mode,
        output_schema_id: modelConfig.default_schema_id || prev.output_schema_id,
      }))
    }
  }

  // 获取当前模型配置允许的识别方式
  const getAllowedModes = () => {
    if (!params.model_config_id || !configOptions) return configOptions?.modes || []
    const modelConfig = configOptions.model_configs.find(m => m.id === params.model_config_id)
    if (!modelConfig) return configOptions.modes || []
    
    return configOptions.modes.filter(m => 
      modelConfig.allowed_modes.includes(m.value)
    )
  }

  const handleConfirm = () => {
    // 验证必填项
    if (!params.model_config_id) {
      showErrorToast('请选择模型配置')
      return
    }
    if (!params.recognition_mode) {
      showErrorToast('请选择识别方式')
      return
    }
    if (params.template_strategy === "fixed" && !params.template_id) {
      showErrorToast('指定模板策略时必须选择模板')
      return
    }

    onConfirm(params)
  }

  const costLevelMap: Record<string, { color: string; label: string }> = {
    low: { color: 'green', label: '低成本' },
    standard: { color: 'blue', label: '标准' },
    high: { color: 'red', label: '高成本' },
  }
  
  const selectedModelConfig = configOptions?.model_configs.find(m => m.id === params.model_config_id)
  const costInfo = selectedModelConfig ? costLevelMap[selectedModelConfig.cost_level] : null

  return (
    <DialogRoot
      size={{ base: "xs", md: "xl" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => {
        if (!open) {
          onClose()
        }
      }}
    >
      <DialogContent>
        <DialogCloseTrigger />
        <DialogHeader>
          <DialogTitle>识别参数选择</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {isLoading ? (
            <Text>加载配置选项...</Text>
          ) : configOptions ? (
            <VStack gap={4} align="stretch">
              {/* 模型配置 */}
              <Field label="模型配置">
                <select
                  value={params.model_config_id}
                  onChange={(e) => handleModelConfigChange(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="">请选择模型配置</option>
                  {configOptions.model_configs.map((config) => (
                    <option key={config.id} value={config.id}>
                      {config.name} ({config.model_name})
                    </option>
                  ))}
                </select>
                {selectedModelConfig && costInfo && (
                  <HStack mt={2} gap={2}>
                    <Badge colorScheme={costInfo.color}>
                      {costInfo.label}
                    </Badge>
                    <Text fontSize="sm" color="gray.600">
                      {selectedModelConfig.provider} | {selectedModelConfig.model_name}
                    </Text>
                  </HStack>
                )}
              </Field>

              {/* 识别方式 */}
              <Field label="识别方式">
                <select
                  value={params.recognition_mode}
                  onChange={(e) => setParams(prev => ({ ...prev, recognition_mode: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="">请选择识别方式</option>
                  {getAllowedModes().map((mode) => (
                    <option key={mode.value} value={mode.value}>
                      {mode.label}
                    </option>
                  ))}
                </select>
              </Field>

              {/* 模板策略 */}
              <Field label="模板策略">
                <select
                  value={params.template_strategy}
                  onChange={(e) => setParams(prev => ({ ...prev, template_strategy: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  {configOptions.template_strategies.map((strategy) => (
                    <option key={strategy.value} value={strategy.value}>
                      {strategy.label}
                    </option>
                  ))}
                </select>
              </Field>

              {/* 指定模板（当template_strategy为fixed时显示） */}
              {params.template_strategy === "fixed" && (
                <Field label="选择模板">
                  <select
                    value={params.template_id || ""}
                    onChange={(e) => {
                      const templateId = e.target.value
                      const selectedTemplate = configOptions?.templates.find(t => t.id === templateId)
                      
                      setParams(prev => {
                        const newParams = { ...prev, template_id: templateId }
                        // 如果模板有对应的 schema，自动设置 output_schema_id
                        if (selectedTemplate?.default_schema_id) {
                          newParams.output_schema_id = selectedTemplate.default_schema_id
                        }
                        return newParams
                      })
                    }}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px',
                      fontSize: '14px',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="">请选择模板</option>
                    {configOptions.templates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.name} ({template.template_type}){template.current_version ? ` - v${template.current_version}` : ''}
                      </option>
                    ))}
                  </select>
                  {/* 显示选中模板的详细信息 */}
                  {params.template_id && (() => {
                    const selectedTemplate = configOptions?.templates.find(t => t.id === params.template_id)
                    if (!selectedTemplate) return null
                    return (
                      <Box mt={2} p={3} bg="gray.50" borderRadius="md" fontSize="sm">
                        {selectedTemplate.description && (
                          <Text mb={1}><strong>描述：</strong>{selectedTemplate.description}</Text>
                        )}
                        <Text mb={1}><strong>类型：</strong>{selectedTemplate.template_type}</Text>
                        {selectedTemplate.current_version && (
                          <Text mb={1}><strong>版本：</strong>{selectedTemplate.current_version}</Text>
                        )}
                        {selectedTemplate.accuracy !== null && selectedTemplate.accuracy !== undefined && (
                          <Text mb={1}><strong>准确率：</strong>{(selectedTemplate.accuracy * 100).toFixed(1)}%</Text>
                        )}
                        {selectedTemplate.default_schema_id && (
                          <Text color="green.600" fontWeight="medium">
                            ✓ 已自动关联输出字段标准
                          </Text>
                        )}
                      </Box>
                    )
                  })()}
                </Field>
              )}

              {/* 输出字段标准 */}
              <Field label="输出字段标准">
                <select
                  value={params.output_schema_id || ""}
                  onChange={(e) => setParams(prev => ({ ...prev, output_schema_id: e.target.value || undefined }))}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    backgroundColor: 'white'
                  }}
                >
                  <option value="">使用默认</option>
                  {configOptions.schemas.map((schema) => (
                    <option key={schema.id} value={schema.id}>
                      {schema.name} v{schema.version} {schema.is_default && "(默认)"}
                    </option>
                  ))}
                </select>
              </Field>

              {/* 高级选项 */}
              <Box>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
                  mb={isAdvancedOpen ? 2 : 0}
                >
                  {isAdvancedOpen ? <FiChevronUp /> : <FiChevronDown />}
                  高级选项
                </Button>
                {isAdvancedOpen && (
                  <VStack gap={4} align="stretch" mt={2}>
                    <Field label="语言">
                      <select
                        value={params.language}
                        onChange={(e) => setParams(prev => ({ ...prev, language: e.target.value }))}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #e2e8f0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          backgroundColor: 'white'
                        }}
                      >
                        <option value="zh-CN">中文</option>
                        <option value="auto">自动检测</option>
                      </select>
                    </Field>

                    <Field label="置信度阈值">
                      <Input
                        type="number"
                        min={0}
                        max={1}
                        step={0.1}
                        value={params.confidence_threshold}
                        onChange={(e) => setParams(prev => ({ ...prev, confidence_threshold: parseFloat(e.target.value) }))}
                      />
                    </Field>

                    <Field label="页范围">
                      <select
                        value={params.page_range}
                        onChange={(e) => setParams(prev => ({ ...prev, page_range: e.target.value }))}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #e2e8f0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          backgroundColor: 'white'
                        }}
                      >
                        <option value="all">全部页面</option>
                        <option value="1st">仅第一页</option>
                        <option value="custom">自定义</option>
                      </select>
                    </Field>

                    <Field label="图像增强策略">
                      <select
                        value={params.enhance_options}
                        onChange={(e) => setParams(prev => ({ ...prev, enhance_options: e.target.value }))}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #e2e8f0',
                          borderRadius: '6px',
                          fontSize: '14px',
                          backgroundColor: 'white'
                        }}
                      >
                        <option value="auto">自动</option>
                        <option value="none">不使用</option>
                        <option value="strong">强增强</option>
                      </select>
                    </Field>
                  </VStack>
                )}
              </Box>
            </VStack>
          ) : (
            <Text>无法加载配置选项</Text>
          )}
        </DialogBody>
        <DialogFooter gap={2}>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleConfirm} disabled={isLoading}>
            确认
          </Button>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}

export default RecognitionParamsModal

