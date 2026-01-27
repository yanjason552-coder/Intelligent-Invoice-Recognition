import { Box, Text, Flex, VStack, HStack, Icon } from "@chakra-ui/react"
import { FiUpload, FiFile, FiX, FiCheck } from "react-icons/fi"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from '@/hooks/useCustomToast'
import useAuth from '@/hooks/useAuth'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"

// 调试日志（Debug Mode）
const DEBUG_ENDPOINT = 'http://127.0.0.1:7249/ingest/660b52e9-b46e-482a-a664-d0e8da08b78a'
const DEBUG_SESSION = 'debug-session'
const postDebugLog = (payload: {
  runId: string
  hypothesisId: string
  location: string
  message: string
  data?: Record<string, any>
}) => {
  // #region agent log
  fetch(DEBUG_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId: DEBUG_SESSION,
      timestamp: Date.now(),
      ...payload,
    }),
  }).catch(() => {})
  // #endregion
}

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
  const [allowDuplicate, setAllowDuplicate] = useState(false)
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
    postDebugLog({
      runId: 'pre-run',
      hypothesisId: 'H1',
      location: 'InvoiceUpload.tsx:uploadFiles',
      message: 'uploadFiles invoked',
      data: { uploadMode, fileCount: uploadedFiles.length, hasModelConfig: !!selectedModelConfig, allowDuplicate }
    })
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

    let hasError = false
    for (const fileItem of uploadedFiles) {
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: uploadMode === 'model' ? 'H2' : 'H1',
        location: 'InvoiceUpload.tsx:uploadFiles',
        message: 'start single file upload',
        data: { fileId: fileItem.id, name: fileItem.name, mode: uploadMode }
      })
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
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: uploadMode === 'model' ? 'H2' : 'H1',
          location: 'InvoiceUpload.tsx:uploadFiles',
          message: 'single file upload success',
          data: { fileId: fileItem.id, name: fileItem.name, mode: uploadMode }
        })
      } catch (error: any) {
        hasError = true
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === fileItem.id ? { ...f, status: 'error' } : f
          )
        )

        // 优先使用 error.message（这是我们抛出的自定义错误消息）
        const errorMessage = error?.message || error?.response?.data?.detail || error?.response?.data?.message || '上传失败'
        showErrorToast(`上传失败: ${fileItem.name} - ${errorMessage}`)
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: uploadMode === 'model' ? 'H2' : 'H1',
          location: 'InvoiceUpload.tsx:uploadFiles',
          message: 'single file upload error',
          data: { fileId: fileItem.id, name: fileItem.name, mode: uploadMode, error: errorMessage }
        })
      }
    }

    // 只有在没有错误时才显示"文件上传完成"
    if (!hasError) {
      showSuccessToast('文件上传完成')
    }
    postDebugLog({
      runId: 'pre-run',
      hypothesisId: 'H1',
      location: 'InvoiceUpload.tsx:uploadFiles',
      message: 'all uploads completed',
      data: { fileCount: uploadedFiles.length, mode: uploadMode }
    })
  }

  const uploadToLocalAPI = async (fileItem: UploadedFile) => {
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H1',
          location: 'InvoiceUpload.tsx:uploadToLocalAPI',
          message: 'enter uploadToLocalAPI',
          data: { fileId: fileItem.id, name: fileItem.name, size: fileItem.size, allowDuplicate }
        })
        // 获取访问令牌
        const token = localStorage.getItem('access_token')
        if (!token) {
          const msg = '未登录，请先登录'
          postDebugLog({
            runId: 'pre-run',
            hypothesisId: 'H1',
            location: 'InvoiceUpload.tsx:uploadToLocalAPI',
            message: 'token missing',
            data: { fileId: fileItem.id, name: fileItem.name }
          })
          throw new Error(msg)
        }

        // 创建 FormData
        const formData = new FormData()
        formData.append('file', fileItem.file)

        // 构建API URL
        const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const uploadUrl = `${apiBaseUrl}/api/v1/invoices/upload${allowDuplicate ? '?allow_duplicate=true' : ''}`

        try {
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
                  postDebugLog({
                    runId: 'pre-run',
                    hypothesisId: 'H3',
                    location: 'InvoiceUpload.tsx:uploadToLocalAPI',
                    message: 'progress',
                    data: { fileId: fileItem.id, progress }
                  })
                }
              },
            }
          )
          return response
        } catch (error: any) {
          // 处理 401 未授权错误
          if (error?.response?.status === 401) {
            postDebugLog({
              runId: 'pre-run',
              hypothesisId: 'H1',
              location: 'InvoiceUpload.tsx:uploadToLocalAPI',
              message: '401 unauthorized, clearing token',
              data: { fileId: fileItem.id, name: fileItem.name }
            })
            // 清除过期的 token
            localStorage.removeItem('access_token')
            // 重定向到登录页
            window.location.href = '/login'
            throw new Error('登录已过期，请重新登录')
          }
          // 重新抛出其他错误
          throw error
        }
  }

  const uploadToModelAPI = async (fileItem: UploadedFile, config: LLMConfig) => {
    if (!config.endpoint || !config.api_key) {
      const msg = '模型配置不完整：缺少 endpoint 或 api_key'
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H2',
        location: 'InvoiceUpload.tsx:uploadToModelAPI',
        message: 'missing endpoint or api_key',
        data: { fileId: fileItem.id, name: fileItem.name, configId: config.id }
      })
      throw new Error(msg)
    }
    postDebugLog({
      runId: 'pre-run',
      hypothesisId: 'H2',
      location: 'InvoiceUpload.tsx:uploadToModelAPI',
      message: 'enter uploadToModelAPI',
      data: { fileId: fileItem.id, name: fileItem.name, configId: config.id, endpoint: config.endpoint }
    })

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
    let externalResponse
    try {
      externalResponse = await axios.post(
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
              postDebugLog({
                runId: 'pre-run',
                hypothesisId: 'H3',
                location: 'InvoiceUpload.tsx:uploadToModelAPI',
                message: 'external upload progress',
                data: { fileId: fileItem.id, progress }
              })
            }
          },
        }
      )
    } catch (error: any) {
      // 处理外部 API 的错误
      if (error?.response?.status === 401) {
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H2',
          location: 'InvoiceUpload.tsx:uploadToModelAPI',
          message: 'external API 401 unauthorized',
          data: { fileId: fileItem.id, name: fileItem.name, endpoint: config.endpoint }
        })
        throw new Error(`外部 API 认证失败：模型配置 "${config.name}" 的 API 密钥无效或已过期，请检查模型配置`)
      }
      // 重新抛出其他错误
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '外部 API 请求失败'
      throw new Error(`外部 API 错误：${errorMessage}`)
    }

    // 解析外部 API 返回的 JSON，获取 id
    const externalFileId = externalResponse.data?.id
    if (!externalFileId) {
      const msg = '外部 API 返回数据中缺少 id 字段'
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H2',
        location: 'InvoiceUpload.tsx:uploadToModelAPI',
        message: 'external response missing id',
        data: { fileId: fileItem.id, name: fileItem.name }
      })
      throw new Error(msg)
    }
    postDebugLog({
      runId: 'pre-run',
      hypothesisId: 'H2',
      location: 'InvoiceUpload.tsx:uploadToModelAPI',
      message: 'external upload success',
      data: { fileId: fileItem.id, name: fileItem.name, externalFileId }
    })

    // 调用后端接口保存文件信息（包含 external_file_id）
    const token = localStorage.getItem('access_token')
    if (!token) {
      const msg = '未登录，请先登录'
      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H2',
        location: 'InvoiceUpload.tsx:uploadToModelAPI',
        message: 'token missing before backend save',
        data: { fileId: fileItem.id, externalFileId }
      })
      throw new Error(msg)
    }

    const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const saveUrl = `${apiBaseUrl}/api/v1/invoices/upload-external${allowDuplicate ? '?allow_duplicate=true' : ''}`

    // 创建 FormData 用于后端保存
    const backendFormData = new FormData()
    backendFormData.append('file', fileItem.file)
    backendFormData.append('external_file_id', externalFileId)

    try {
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

      postDebugLog({
        runId: 'pre-run',
        hypothesisId: 'H2',
        location: 'InvoiceUpload.tsx:uploadToModelAPI',
        message: 'backend save success',
        data: { fileId: fileItem.id, externalFileId }
      })
      return backendResponse
    } catch (error: any) {
      // 处理 401 未授权错误
      if (error?.response?.status === 401) {
        postDebugLog({
          runId: 'pre-run',
          hypothesisId: 'H2',
          location: 'InvoiceUpload.tsx:uploadToModelAPI',
          message: '401 unauthorized, clearing token',
          data: { fileId: fileItem.id, name: fileItem.name, externalFileId }
        })
        // 清除过期的 token
        localStorage.removeItem('access_token')
        // 重定向到登录页
        window.location.href = '/login'
        throw new Error('登录已过期，请重新登录')
      }
      // 重新抛出其他错误
      throw error
    }
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

          {/* 调试：允许重复上传（仅超级用户显示，需后端开启开关） */}
          {user?.is_superuser && (
            <Box mt={3}>
              <Field>
                <input
                  type="checkbox"
                  id="allow-duplicate-upload"
                  checked={allowDuplicate}
                  onChange={(e) => setAllowDuplicate(e.target.checked)}
                  style={{ marginRight: '8px' }}
                />
                <label htmlFor="allow-duplicate-upload" style={{ cursor: 'pointer' }}>
                  调试：允许重复上传（跳过去重）
                </label>
              </Field>
              <Text fontSize="xs" color="gray.500" mt={1}>
                需要后端开启环境变量 INVOICE_DEBUG_ALLOW_DUPLICATE_UPLOADS=true
              </Text>
            </Box>
          )}

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