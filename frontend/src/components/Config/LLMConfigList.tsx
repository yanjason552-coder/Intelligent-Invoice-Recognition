import { Box, Text, Flex, VStack, Input } from "@chakra-ui/react"
import { FiSave, FiEdit2, FiRefreshCw, FiTrash2 } from "react-icons/fi"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
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
  create_time?: string
  update_time?: string
  default_schema_id?: string
}

interface SchemaData {
  id: string
  name: string
  version: string
  is_default: boolean
}

const LLMConfigList = () => {
  const [configs, setConfigs] = useState<LLMConfigData[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editedConfig, setEditedConfig] = useState<LLMConfigData | null>(null)
  const [deleteDialogConfig, setDeleteDialogConfig] = useState<LLMConfigData | null>(null)
  const [schemas, setSchemas] = useState<SchemaData[]>([])
  const { showSuccessToast, showErrorToast } = useCustomToast()

  useEffect(() => {
    loadConfigs()
    loadSchemas()
  }, [])

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

  const loadConfigs = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await axios.get('/api/v1/config/llm/list', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      if (response.data && response.data.data) {
        setConfigs(response.data.data)
      }
    } catch (error: any) {
      console.error('加载配置列表失败:', error)
      showErrorToast('加载配置列表失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (config: LLMConfigData) => {
    setEditingId(config.id || null)
    // 注意：列表接口可能不返回 api_key，设置为空字符串，用户需要重新输入
    setEditedConfig({ ...config, api_key: config.api_key || '' })
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditedConfig(null)
  }

  const handleSave = async (config: LLMConfigData) => {
    if (!config.id) {
      showErrorToast('配置ID不存在')
      return
    }

    // 验证必填字段
    if (!config.name || !config.endpoint) {
      showErrorToast('配置名称和端点地址为必填项')
      return
    }

    try {
      setSaving(config.id)
      const token = localStorage.getItem('access_token')
      // 如果 api_key 为空，不发送该字段（让后端保持原值）
      const dataToSave: any = { ...config }
      if (!dataToSave.api_key || dataToSave.api_key.trim() === '') {
        // 不发送 api_key，让后端保持原值
        delete dataToSave.api_key
      }
      await axios.post('/api/v1/config/llm', dataToSave, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      showSuccessToast('配置更新成功')
      setEditingId(null)
      setEditedConfig(null)
      await loadConfigs() // 重新加载列表
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '保存失败')
    } finally {
      setSaving(null)
    }
  }

  const handleFieldChange = (field: keyof LLMConfigData, value: any) => {
    if (editedConfig) {
      setEditedConfig({ ...editedConfig, [field]: value })
    }
  }

  const handleDelete = async (config: LLMConfigData) => {
    if (!config.id) {
      showErrorToast('配置ID不存在，无法删除')
      return
    }

    try {
      setDeleting(config.id)
      const token = localStorage.getItem('access_token')
      await axios.delete(`/api/v1/config/llm/${config.id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      showSuccessToast(`配置 "${config.name}" 删除成功`)
      setDeleteDialogConfig(null)
      await loadConfigs() // 重新加载列表
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '删除失败')
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <Box p={4} textAlign="center">
        <Text>加载中...</Text>
      </Box>
    )
  }

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Text fontSize="lg" fontWeight="semibold">
          配置列表管理
        </Text>
        <Button onClick={loadConfigs} variant="outline">
          <FiRefreshCw style={{ marginRight: '8px' }} />
          刷新
        </Button>
      </Flex>

      {configs.length === 0 ? (
        <Box p={8} textAlign="center" bg="gray.50" borderRadius="md">
          <Text color="gray.500">暂无配置数据</Text>
        </Box>
      ) : (
        <Box
          maxH="calc(100vh - 250px)"
          overflowY="auto"
          overflowX="hidden"
          pr={2}
          className="custom-scrollbar"
        >
          <VStack gap={6} align="stretch" maxW="900px">
          {configs.map((config) => (
            <Box
              key={config.id}
              p={6}
              border="1px"
              borderColor="gray.200"
              borderRadius="md"
              bg="white"
              boxShadow="sm"
            >
              {editingId === config.id && editedConfig ? (
                // 编辑模式 - 使用与 LLMConfig.tsx 相同的布局结构
                <VStack gap={6} align="stretch">
                  <Flex justify="space-between" align="center">
                    <Text fontSize="md" fontWeight="semibold" color="gray.700">
                      编辑配置: {editedConfig.name}
                    </Text>
                    <Flex gap={2}>
                      <Button
                        onClick={() => handleSave(editedConfig)}
                        disabled={saving === config.id}
                      >
                        <FiSave style={{ marginRight: '8px' }} />
                        {saving === config.id ? '保存中...' : '保存配置'}
                      </Button>
                      <Button
                        variant="outline"
                        colorPalette="red"
                        onClick={() => setDeleteDialogConfig(editedConfig)}
                        disabled={deleting === config.id}
                      >
                        <FiTrash2 style={{ marginRight: '8px' }} />
                        删除
                      </Button>
                      <Button
                        variant="outline"
                        onClick={handleCancelEdit}
                      >
                        取消
                      </Button>
                    </Flex>
                  </Flex>

                  {/* 基础信息 */}
                  <Box>
                    <Text fontSize="md" fontWeight="semibold" mb={4} color="gray.700">
                      基础信息
                    </Text>
                    <VStack gap={4}>
                      <Field label="配置名称" required>
                        <Input
                          value={editedConfig.name}
                          onChange={(e) => handleFieldChange('name', e.target.value)}
                          placeholder="例如：SYNTAX生产环境"
                        />
                      </Field>

                      <Field label="配置描述">
                        <textarea
                          value={editedConfig.description || ''}
                          onChange={(e) => handleFieldChange('description', e.target.value)}
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
                          value={editedConfig.endpoint}
                          onChange={(e) => handleFieldChange('endpoint', e.target.value)}
                          placeholder="https://api.syntax.ai/v1"
                        />
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          例如：https://api.syntax.ai/v1 或 https://your-domain.com/v1
                        </Text>
                      </Field>

                      <Field label="API密钥" required>
                        <Input
                          type="password"
                          value={editedConfig.api_key}
                          onChange={(e) => handleFieldChange('api_key', e.target.value)}
                          placeholder={editedConfig.api_key ? "输入新密钥以更新，留空保持原值" : "输入您的SYNTAX API密钥"}
                        />
                        <Text fontSize="xs" color="gray.500" mt={1}>
                          {editedConfig.api_key 
                            ? "输入新密钥以更新，留空将保持原值不变" 
                            : "在SYNTAX平台获取API密钥"}
                        </Text>
                      </Field>

                      <Field label="应用类型" required>
                        <select
                          value={editedConfig.app_type}
                          onChange={(e) => handleFieldChange('app_type', e.target.value)}
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

                      {editedConfig.app_type === 'chat' && (
                        <Field label="应用ID (App ID)">
                          <Input
                            value={editedConfig.app_id || ''}
                            onChange={(e) => handleFieldChange('app_id', e.target.value)}
                            placeholder="对话型应用的App ID"
                          />
                          <Text fontSize="xs" color="gray.500" mt={1}>
                            用于对话型应用，在SYNTAX平台的应用设置中获取
                          </Text>
                        </Field>
                      )}

                      {editedConfig.app_type === 'workflow' && (
                        <Field label="工作流ID (Workflow ID)">
                          <Input
                            value={editedConfig.workflow_id || ''}
                            onChange={(e) => handleFieldChange('workflow_id', e.target.value)}
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
                          value={editedConfig.default_schema_id || ''}
                          onChange={(e) => handleFieldChange('default_schema_id', e.target.value)}
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
                          value={editedConfig.timeout}
                          onChange={(e) => handleFieldChange('timeout', parseInt(e.target.value) || 300)}
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
                          value={editedConfig.max_retries}
                          onChange={(e) => handleFieldChange('max_retries', parseInt(e.target.value) || 3)}
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
                            checked={editedConfig.is_active}
                            onCheckedChange={({ checked }) => handleFieldChange('is_active', checked === true)}
                          >
                            启用配置
                          </Checkbox>
                        </Field>

                        <Field>
                          <Checkbox
                            checked={editedConfig.is_default}
                            onCheckedChange={({ checked }) => handleFieldChange('is_default', checked === true)}
                          >
                            设为默认配置
                          </Checkbox>
                        </Field>
                      </Flex>
                    </VStack>
                  </Box>
                </VStack>
              ) : (
                // 查看模式 - 优化显示
                <VStack gap={4} align="stretch">
                  <Flex justify="space-between" align="center">
                    <Flex align="center" gap={3}>
                      <Text fontSize="lg" fontWeight="semibold" color="gray.800">
                        {config.name}
                      </Text>
                      {config.is_default && (
                        <Box
                          px={2}
                          py={1}
                          bg="blue.100"
                          color="blue.700"
                          borderRadius="sm"
                          fontSize="xs"
                          fontWeight="bold"
                        >
                          默认
                        </Box>
                      )}
                      {config.is_active ? (
                        <Box
                          px={2}
                          py={1}
                          bg="green.100"
                          color="green.700"
                          borderRadius="sm"
                          fontSize="xs"
                          fontWeight="medium"
                        >
                          启用
                        </Box>
                      ) : (
                        <Box
                          px={2}
                          py={1}
                          bg="gray.100"
                          color="gray.700"
                          borderRadius="sm"
                          fontSize="xs"
                          fontWeight="medium"
                        >
                          停用
                        </Box>
                      )}
                    </Flex>
                    <Flex gap={2}>
                      <Button
                        variant="outline"
                        onClick={() => handleEdit(config)}
                      >
                        <FiEdit2 style={{ marginRight: '8px' }} />
                        编辑
                      </Button>
                      <Button
                        variant="outline"
                        colorPalette="red"
                        onClick={() => setDeleteDialogConfig(config)}
                        disabled={deleting === config.id}
                      >
                        <FiTrash2 style={{ marginRight: '8px' }} />
                        删除
                      </Button>
                    </Flex>
                  </Flex>

                  {config.description && (
                    <Box pb={2} borderBottom="1px" borderColor="gray.100">
                      <Text fontSize="sm" color="gray.600">
                        {config.description}
                      </Text>
                    </Box>
                  )}

                  <VStack gap={2} align="stretch" pt={2}>
                    <Flex gap={6} wrap="wrap">
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          端点地址
                        </Text>
                        <Text fontSize="sm" color="gray.800" fontWeight="medium">
                          {config.endpoint}
                        </Text>
                      </Box>
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          应用类型
                        </Text>
                        <Text fontSize="sm" color="gray.800" fontWeight="medium">
                          {config.app_type === 'workflow' ? '工作流' : config.app_type === 'chat' ? '对话' : '补全'}
                        </Text>
                      </Box>
                    </Flex>

                    {(config.app_id || config.workflow_id) && (
                      <Flex gap={6} wrap="wrap">
                        {config.app_id && (
                          <Box>
                            <Text fontSize="xs" color="gray.500" mb={1}>
                              应用ID
                            </Text>
                            <Text fontSize="sm" color="gray.800" fontWeight="medium">
                              {config.app_id}
                            </Text>
                          </Box>
                        )}
                        {config.workflow_id && (
                          <Box>
                            <Text fontSize="xs" color="gray.500" mb={1}>
                              工作流ID
                            </Text>
                            <Text fontSize="sm" color="gray.800" fontWeight="medium">
                              {config.workflow_id}
                            </Text>
                          </Box>
                        )}
                      </Flex>
                    )}

                    <Flex gap={6} wrap="wrap">
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          超时时间
                        </Text>
                        <Text fontSize="sm" color="gray.800" fontWeight="medium">
                          {config.timeout}秒
                        </Text>
                      </Box>
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          最大重试
                        </Text>
                        <Text fontSize="sm" color="gray.800" fontWeight="medium">
                          {config.max_retries}次
                        </Text>
                      </Box>
                      {config.create_time && (
                        <Box>
                          <Text fontSize="xs" color="gray.500" mb={1}>
                            创建时间
                          </Text>
                          <Text fontSize="sm" color="gray.800" fontWeight="medium">
                            {new Date(config.create_time).toLocaleString('zh-CN')}
                          </Text>
                        </Box>
                      )}
                    </Flex>
                  </VStack>
                </VStack>
              )}
            </Box>
          ))}
          </VStack>
        </Box>
      )}

      {/* 删除确认对话框 */}
      <DialogRoot
        size={{ base: "xs", md: "md" }}
        placement="center"
        role="alertdialog"
        open={deleteDialogConfig !== null}
        onOpenChange={({ open }) => !open && setDeleteDialogConfig(null)}
      >
        <DialogContent>
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>确认删除配置</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              您确定要删除配置 <strong>"{deleteDialogConfig?.name}"</strong> 吗？此操作将直接从数据库中删除该配置，且无法恢复。
            </Text>
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={deleting !== null}
              >
                取消
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="red"
              onClick={() => deleteDialogConfig && handleDelete(deleteDialogConfig)}
              loading={deleting !== null}
            >
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </DialogRoot>
    </Box>
  )
}

export default LLMConfigList

