import { Box, Text, Flex, VStack, Input } from "@chakra-ui/react"
import { FiSave, FiCheckCircle, FiXCircle } from "react-icons/fi"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Checkbox } from "@/components/ui/checkbox"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'

interface LLMConfigData {
  id?: string
  name: string
  endpoint: string
  api_key: string
  app_id?: string
  workflow_id?: string
  app_type: 'chat' | 'workflow' | 'completion'
  timeout: number
  max_retries: number
  is_active: boolean
  is_default?: boolean
  description?: string
  default_schema_id?: string
}

const LLMConfig = () => {
  const [config, setConfig] = useState<LLMConfigData>({
    name: '',
    endpoint: '',
    api_key: '',
    app_id: '',
    workflow_id: '',
    app_type: 'workflow',
    timeout: 300,
    max_retries: 3,
    is_active: true,
    is_default: false,
    description: '',
    default_schema_id: ''
  })
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [schemas, setSchemas] = useState<Array<{id: string, name: string, version: string, is_default: boolean}>>([])
  const { showSuccessToast, showErrorToast } = useCustomToast()

  useEffect(() => {
    loadConfig()
    loadSchemas()
  }, [])

  const loadConfig = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get('/api/v1/config/llm', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      if (response.data) {
        setConfig({
          ...response.data,
          api_key: response.data.api_key || '', // 如果后端返回脱敏的key，这里保持原值
          default_schema_id: response.data.default_schema_id || ''
        })
      }
    } catch (error: any) {
      console.error('加载配置失败:', error)
      // 如果配置不存在，使用默认值
    }
  }

  const loadSchemas = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get('/api/v1/config/schemas', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      if (response.data && response.data.data) {
        setSchemas(response.data.data.filter((s: any) => s.is_active))
      }
    } catch (error: any) {
      console.error('加载Schema列表失败:', error)
    }
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      await axios.post('/api/v1/config/llm', config, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      showSuccessToast('大模型配置保存成功')
      await loadConfig() // 重新加载配置
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    try {
      setTesting(true)
      setTestResult(null)
      
      // 测试API连接
      const token = localStorage.getItem('access_token')
      const testResponse = await axios.post('/api/v1/config/llm/test', {
        endpoint: config.endpoint,
        api_key: config.api_key,
        app_id: config.app_id,
        workflow_id: config.workflow_id,
        app_type: config.app_type
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      
      if (testResponse.data.success) {
        setTestResult({ success: true, message: '连接测试成功' })
        showSuccessToast('连接测试成功')
      } else {
        setTestResult({ success: false, message: testResponse.data.message || '连接测试失败' })
        showErrorToast(testResponse.data.message || '连接测试失败')
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || '连接测试失败'
      setTestResult({ success: false, message })
      showErrorToast(message)
    } finally {
      setTesting(false)
    }
  }

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={6}>
        <Text fontSize="xl" fontWeight="bold">
          大模型配置管理
        </Text>
      </Flex>

          <Box 
            pt={4}
            maxH="calc(100vh - 200px)"
            overflowY="auto"
            overflowX="hidden"
            pr={2}
            className="custom-scrollbar"
          >
            <Flex justify="space-between" align="center" mb={6}>
              <Text fontSize="lg" fontWeight="semibold">
                默认配置管理
              </Text>
              <Flex gap={2}>
                <Button
                  variant="outline"
                  onClick={handleTest}
                  disabled={testing || !config.endpoint || !config.api_key}
                >
                  {testing ? '测试中...' : '测试连接'}
                </Button>
                <Button onClick={handleSave} disabled={loading}>
                  <FiSave style={{ marginRight: '8px' }} />
                  {loading ? '保存中...' : '保存配置'}
                </Button>
              </Flex>
            </Flex>

            {testResult && (
              <Box
                mb={4}
                p={3}
                borderRadius="md"
                bg={testResult.success ? 'green.50' : 'red.50'}
                border="1px"
                borderColor={testResult.success ? 'green.200' : 'red.200'}
              >
                <Flex align="center" gap={2}>
                  {testResult.success ? (
                    <FiCheckCircle color="green" />
                  ) : (
                    <FiXCircle color="red" />
                  )}
                  <Text color={testResult.success ? 'green.700' : 'red.700'}>
                    {testResult.message}
                  </Text>
                </Flex>
              </Box>
            )}

            <VStack gap={6} align="stretch" maxW="900px">
              {/* 基础信息 */}
              <Box>
                <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
                  基础信息
                </Text>
                <VStack gap={4}>
                  <Field label="配置名称" required>
                    <Input
                      value={config.name}
                      onChange={(e) => setConfig({ ...config, name: e.target.value })}
                      placeholder="例如：SYNTAX生产环境"
                    />
                  </Field>

                  <Field label="配置描述">
                    <textarea
                      value={config.description || ''}
                      onChange={(e) => setConfig({ ...config, description: e.target.value })}
                      placeholder="配置说明（可选）"
                      rows={2}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontFamily: 'inherit',
                        resize: 'vertical'
                      }}
                    />
                  </Field>
                </VStack>
              </Box>

              {/* SYNTAX API配置 */}
              <Box>
                <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
                  SYNTAX API 配置
                </Text>
                <VStack gap={4}>
                  <Field label="API端点地址" required>
                    <Input
                      value={config.endpoint}
                      onChange={(e) => setConfig({ ...config, endpoint: e.target.value })}
                      placeholder="https://api.syntax.ai/v1"
                    />
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      例如：https://api.syntax.ai/v1 或 https://your-domain.com/v1
                    </Text>
                  </Field>

                  <Field label="API密钥" required>
                    <Input
                      type="password"
                      value={config.api_key}
                      onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                      placeholder="输入您的SYNTAX API密钥"
                    />
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      在SYNTAX平台获取API密钥
                    </Text>
                  </Field>

                  <Field label="应用类型" required>
                    <select
                      id="app-type"
                      value={config.app_type}
                      onChange={(e) => setConfig({ ...config, app_type: e.target.value as any })}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '14px',
                        backgroundColor: 'white'
                      }}
                    >
                      <option value="workflow">工作流 (Workflow)</option>
                      <option value="chat">对话 (Chat)</option>
                      <option value="completion">补全 (Completion)</option>
                    </select>
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      选择您的应用类型
                    </Text>
                  </Field>

                  {config.app_type === 'chat' && (
                    <Field label="应用ID (App ID)">
                      <Input
                        value={config.app_id || ''}
                        onChange={(e) => setConfig({ ...config, app_id: e.target.value })}
                        placeholder="对话型应用的App ID"
                      />
                      <Text fontSize="xs" color="gray.500" mt={1}>
                        用于对话型应用，在SYNTAX平台的应用设置中获取
                      </Text>
                    </Field>
                  )}

                  {config.app_type === 'workflow' && (
                    <Field label="工作流ID (Workflow ID)">
                      <Input
                        value={config.workflow_id || ''}
                        onChange={(e) => setConfig({ ...config, workflow_id: e.target.value })}
                        placeholder="工作流应用的Workflow ID"
                      />
                      <Text fontSize="xs" color="gray.500" mt={1}>
                        用于工作流应用，在SYNTAX平台的工作流设置中获取
                      </Text>
                    </Field>
                  )}
                </VStack>
              </Box>

              {/* Schema配置 */}
              <Box>
                <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
                  Schema配置
                </Text>
                <VStack gap={4}>
                  <Field label="默认输出Schema">
                    <select
                      value={config.default_schema_id || ''}
                      onChange={(e) => setConfig({ ...config, default_schema_id: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '14px',
                        backgroundColor: 'white'
                      }}
                    >
                      <option value="">不使用Schema（原有逻辑）</option>
                      {schemas.map((schema) => (
                        <option key={schema.id} value={schema.id}>
                          {schema.name} (v{schema.version}){schema.is_default ? ' - 默认' : ''}
                        </option>
                      ))}
                    </select>
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      选择该模型配置默认使用的输出结构标准。留空则不进行Schema验证。
                    </Text>
                  </Field>
                </VStack>
              </Box>

              {/* 高级配置 */}
              <Box>
                <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
                  高级配置
                </Text>
                <VStack gap={4}>
                  <Field label="请求超时时间（秒）">
                    <Input
                      type="number"
                      value={config.timeout}
                      onChange={(e) => setConfig({ ...config, timeout: parseInt(e.target.value) || 300 })}
                      min={10}
                      max={600}
                    />
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      建议值：300秒（5分钟）
                    </Text>
                  </Field>

                  <Field label="最大重试次数">
                    <Input
                      type="number"
                      value={config.max_retries}
                      onChange={(e) => setConfig({ ...config, max_retries: parseInt(e.target.value) || 3 })}
                      min={0}
                      max={10}
                    />
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      请求失败时的最大重试次数
                    </Text>
                  </Field>

                  <Flex align="center" gap={4}>
                    <Field>
                      <Checkbox
                        checked={config.is_active}
                        onCheckedChange={({ checked }) => setConfig({ ...config, is_active: checked === true })}
                      >
                        启用配置
                      </Checkbox>
                    </Field>

                    <Field>
                      <Checkbox
                        checked={config.is_default}
                        onCheckedChange={({ checked }) => setConfig({ ...config, is_default: checked === true })}
                      >
                        设为默认配置
                      </Checkbox>
                    </Field>
                  </Flex>
                </VStack>
              </Box>
            </VStack>
          </Box>
    </Box>
  )
}

export default LLMConfig

