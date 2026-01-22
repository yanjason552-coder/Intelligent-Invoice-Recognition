import { Box, Text, Flex, VStack, HStack, Icon } from "@chakra-ui/react"
import { FiUpload, FiFile, FiX, FiCheck } from "react-icons/fi"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from '@/hooks/useCustomToast'
import useAuth from '@/hooks/useAuth'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress?: number
}

interface LLMConfig {
  id: string
  name: string
  endpoint: string
  api_key: string
  description?: string
}

const InvoiceUpload = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [uploadMode, setUploadMode] = useState<'local' | 'model'>('local')
  const [selectedModelConfig, setSelectedModelConfig] = useState<LLMConfig | null>(null)
  const [modelConfigs, setModelConfigs] = useState<LLMConfig[]>([])
  const [loadingConfigs, setLoadingConfigs] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { user } = useAuth()

  // 加载模型配置列表
  useEffect(() => {
    loadModelConfigs()
  }, [])

  const loadModelConfigs = async () => {
    try {
      setLoadingConfigs(true)
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await axios.get(`${apiBaseUrl}/api/v1/config/llm/list`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      if (response.data && response.data.data) {
        const configs = response.data.data.map((config: any) => ({
          id: config.id,
          name: config.name,
          endpoint: config.endpoint,
          api_key: config.api_key || '', // 列表接口现在返回 api_key
          description: config.description
        }))
        setModelConfigs(configs)
      }
    } catch (error: any) {
      console.error('加载模型配置失败:', error)
      // 不显示错误提示，因为这是可选功能
    } finally {
      setLoadingConfigs(false)
    }
  }

  // 获取指定配置的完整信息（包含 api_key）
  const getModelConfigWithKey = async (configId: string): Promise<LLMConfig | null> => {
    try {
      // 先从已加载的配置列表中查找
      const config = modelConfigs.find(c => c.id === configId)
      if (config && config.api_key) {
        return config
      }
      // 如果列表中没有或没有 api_key，尝试获取默认配置（包含 api_key）
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const defaultResponse = await axios.get(`${apiBaseUrl}/api/v1/config/llm`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      if (defaultResponse.data && defaultResponse.data.id === configId) {
        return {
          id: defaultResponse.data.id,
          name: defaultResponse.data.name,
          endpoint: defaultResponse.data.endpoint,
          api_key: defaultResponse.data.api_key,
          description: defaultResponse.data.description
        }
      }
      return config || null
    } catch (error: any) {
      console.error('获取模型配置详情失败:', error)
      return null
    }
  }

  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return

    const newFiles: UploadedFile[] = Array.from(files).map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
      status: 'pending' as const
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id))
  }

  const uploadFiles = async () => {
    if (uploadedFiles.length === 0) {
      showErrorToast('请先选择要上传的文件')
      return
    }

    // 如果使用模型配置上传，需要验证配置
    if (uploadMode === 'model') {
      if (!selectedModelConfig) {
        showErrorToast('请先选择模型配置')
        return
      }
      // 获取包含 api_key 的完整配置
      const fullConfig = await getModelConfigWithKey(selectedModelConfig.id)
      if (!fullConfig || !fullConfig.api_key) {
        showErrorToast('无法获取模型配置的 API 密钥，请检查配置')
        return
      }
      selectedModelConfig.api_key = fullConfig.api_key
      selectedModelConfig.endpoint = fullConfig.endpoint
    }

    for (const fileItem of uploadedFiles) {
      if (fileItem.status === 'success') continue

      setUploadedFiles(prev =>
        prev.map(f =>
          f.id === fileItem.id ? { ...f, status: 'uploading', progress: 0 } : f
        )
      )

      try {
        if (uploadMode === 'model' && selectedModelConfig) {
          // 使用模型配置上传到外部 API
          await uploadToModelAPI(fileItem, selectedModelConfig)
        } else {
          // 使用本地 API 上传
          await uploadToLocalAPI(fileItem)
        }

        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === fileItem.id ? { ...f, status: 'success', progress: 100 } : f
          )
        )

        showSuccessToast(`文件 ${fileItem.name} 上传成功`)
      } catch (error: any) {
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === fileItem.id ? { ...f, status: 'error' } : f
          )
        )

        const errorMessage = error?.response?.data?.detail || error?.message || '上传失败'
        showErrorToast(`上传失败: ${fileItem.name} - ${errorMessage}`)
      }
    }

    showSuccessToast('文件上传完成')
  }

  const uploadToLocalAPI = async (fileItem: UploadedFile) => {
        // 获取访问令牌
        const token = localStorage.getItem('access_token')
        if (!token) {
          throw new Error('未登录，请先登录')
        }

        // 创建 FormData
        const formData = new FormData()
        formData.append('file', fileItem.file)

        // 构建API URL
        const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const uploadUrl = `${apiBaseUrl}/api/v1/invoices/upload`

        // 调用上传API
        const response = await axios.post(
          uploadUrl,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                setUploadedFiles(prev =>
                  prev.map(f =>
                    f.id === fileItem.id ? { ...f, progress } : f
                  )
                )
              }
            },
          }
        )

    return response
  }

  const uploadToModelAPI = async (fileItem: UploadedFile, config: LLMConfig) => {
    if (!config.endpoint || !config.api_key) {
      throw new Error('模型配置不完整：缺少 endpoint 或 api_key')
    }

    // 获取当前用户名
    const userName = user?.email || user?.full_name || 'unknown'

    // 构建外部 API URL
    const externalEndpoint = config.endpoint.endsWith('/') 
      ? config.endpoint.slice(0, -1) 
      : config.endpoint
    const uploadUrl = `${externalEndpoint}/files/upload`

    // 创建 FormData
    const formData = new FormData()
    formData.append('file', fileItem.file)
    formData.append('user', userName)

    // 调用外部 API
    const externalResponse = await axios.post(
      uploadUrl,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${config.api_key}`,
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        setUploadedFiles(prev =>
          prev.map(f =>
                f.id === fileItem.id ? { ...f, progress } : f
          )
        )
          }
        },
      }
    )

    // 解析外部 API 返回的 JSON，获取 id
    const externalFileId = externalResponse.data?.id
    if (!externalFileId) {
      throw new Error('外部 API 返回数据中缺少 id 字段')
    }

    // 调用后端接口保存文件信息（包含 external_file_id）
    const token = localStorage.getItem('access_token')
    if (!token) {
      throw new Error('未登录，请先登录')
    }

    const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const saveUrl = `${apiBaseUrl}/api/v1/invoices/upload-external`

    // 创建 FormData 用于后端保存
    const backendFormData = new FormData()
    backendFormData.append('file', fileItem.file)
    backendFormData.append('external_file_id', externalFileId)

    // 调用后端接口保存
    const backendResponse = await axios.post(
      saveUrl,
      backendFormData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return backendResponse
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <Box p={4}>
      <Text fontSize="xl" fontWeight="bold" mb={4}>
        票据上传
      </Text>

      <VStack gap={4} align="stretch">
        {/* 上传方式选择 */}
        <Box border="1px" borderColor="gray.200" borderRadius="md" p={4}>
          <Text fontSize="md" fontWeight="medium" mb={3}>
            上传方式
          </Text>
          <Flex gap={4} align="center">
            <Field>
              <input
                type="radio"
                id="upload-model"
                name="upload-mode"
                value="model"
                checked={uploadMode === 'model'}
                onChange={(e) => setUploadMode(e.target.value as 'local' | 'model')}
                style={{ marginRight: '8px' }}
              />
              <label htmlFor="upload-model" style={{ cursor: 'pointer' }}>
                模型配置上传（外部 API）
              </label>
            </Field>
            <Field>
              <input
                type="radio"
                id="upload-local"
                name="upload-mode"
                value="local"
                checked={uploadMode === 'local'}
                onChange={(e) => setUploadMode(e.target.value as 'local' | 'model')}
                style={{ marginRight: '8px' }}
              />
              <label htmlFor="upload-local" style={{ cursor: 'pointer' }}>
                本地上传（系统服务器）
              </label>
            </Field>
          </Flex>

          {/* 模型配置选择 */}
          {uploadMode === 'model' && (
            <Box mt={4}>
              <Field label="选择模型配置" required>
                {loadingConfigs ? (
                  <Text fontSize="sm" color="gray.500">加载配置中...</Text>
                ) : (
                  <select
                    value={selectedModelConfig?.id || ''}
                    onChange={async (e) => {
                      const configId = e.target.value
                      if (configId) {
                        const config = modelConfigs.find(c => c.id === configId)
                        if (config) {
                          // 获取包含 api_key 的完整配置
                          const fullConfig = await getModelConfigWithKey(configId)
                          if (fullConfig) {
                            setSelectedModelConfig(fullConfig)
                          } else {
                            setSelectedModelConfig(config)
                          }
                        }
                      } else {
                        setSelectedModelConfig(null)
                      }
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
                    <option value="">请选择模型配置</option>
                    {modelConfigs.map((config) => (
                      <option key={config.id} value={config.id}>
                        {config.name} {config.description ? `- ${config.description}` : ''}
                      </option>
                    ))}
                  </select>
                )}
                {selectedModelConfig && (
                  <Text fontSize="xs" color="gray.500" mt={1}>
                    API 地址: {selectedModelConfig.endpoint}
                  </Text>
                )}
              </Field>
            </Box>
          )}
        </Box>

        {/* 上传区域 */}
        <Box
          border="2px dashed"
          borderColor={isDragging ? "blue.400" : "gray.300"}
          borderRadius="md"
          p={8}
          textAlign="center"
          bg={isDragging ? "blue.50" : "gray.50"}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          cursor="pointer"
          _hover={{ borderColor: "blue.400", bg: "blue.50" }}
          onClick={() => fileInputRef.current?.click()}
        >
          <Icon as={FiUpload} boxSize={12} color="gray.400" mb={4} />
          <Text fontSize="lg" fontWeight="medium" mb={2}>
            拖拽文件到此处或点击上传
          </Text>
          <Text fontSize="sm" color="gray.500" mb={4}>
            支持 PDF、JPG、PNG 格式，单文件最大 10MB
          </Text>
          <Button colorScheme="blue" size="sm">
            选择文件
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            style={{ display: 'none' }}
            onChange={(e) => handleFileSelect(e.target.files)}
          />
        </Box>

        {/* 文件列表 */}
        {uploadedFiles.length > 0 && (
          <Box border="1px" borderColor="gray.200" borderRadius="md" p={4}>
            <Text fontSize="md" fontWeight="medium" mb={3}>
              已选择文件 ({uploadedFiles.length})
            </Text>
            <VStack gap={2} align="stretch">
              {uploadedFiles.map((file) => (
                <Flex
                  key={file.id}
                  align="center"
                  justify="space-between"
                  p={3}
                  bg="gray.50"
                  borderRadius="md"
                  border="1px"
                  borderColor="gray.200"
                >
                  <HStack gap={3} flex={1}>
                    <Icon as={FiFile} color="blue.500" />
                    <Box flex={1}>
                      <Text fontSize="sm" fontWeight="medium" truncate>
                        {file.name}
                      </Text>
                      <Text fontSize="xs" color="gray.500">
                        {formatFileSize(file.size)}
                        {file.status === 'uploading' && file.progress !== undefined && (
                          <Text as="span" ml={2}>
                            - 上传中 {file.progress}%
                          </Text>
                        )}
                        {file.status === 'success' && (
                          <Text as="span" ml={2} color="green.500">
                            - 上传成功
                          </Text>
                        )}
                        {file.status === 'error' && (
                          <Text as="span" ml={2} color="red.500">
                            - 上传失败
                          </Text>
                        )}
                      </Text>
                    </Box>
                    {file.status === 'success' && (
                      <Icon as={FiCheck} color="green.500" />
                    )}
                  </HStack>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation()
                      removeFile(file.id)
                    }}
                  >
                    <FiX />
                  </Button>
                </Flex>
              ))}
            </VStack>
          </Box>
        )}

        {/* 操作按钮 */}
        <HStack justify="flex-end" gap={3}>
          <Button
            variant="outline"
            onClick={() => setUploadedFiles([])}
            disabled={uploadedFiles.length === 0}
          >
            清空列表
          </Button>
          <Button
            colorScheme="blue"
            onClick={uploadFiles}
            disabled={uploadedFiles.length === 0 || uploadedFiles.every(f => f.status === 'success')}
            loading={uploadedFiles.some(f => f.status === 'uploading')}
          >
            开始上传
          </Button>
        </HStack>
      </VStack>
    </Box>
  )
}

export default InvoiceUpload