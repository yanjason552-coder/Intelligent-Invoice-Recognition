import {
  Box,
  Text,
  Flex,
  VStack,
  HStack,
  Button,
  Textarea,
  Badge,
  IconButton,
  Table,
  Spinner,
  Code,
} from "@chakra-ui/react"
import {
  FiUpload,
  FiImage,
  FiFile,
  FiCheckCircle,
  FiXCircle,
  FiAlertCircle,
  FiCopy,
  FiSave,
  FiRefreshCw,
  FiChevronDown,
  FiChevronUp,
  FiDownload,
  FiInfo,
} from "react-icons/fi"
import { useState, useRef } from "react"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'

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

interface FieldStatus {
  key: string
  status: 'ok' | 'missing' | 'format_error' | 'warning'
  message?: string
  confidence?: number
}

interface ExtractionResult {
  prompt_suggestion: string
  extracted_data: Record<string, any>
  field_status: FieldStatus[]
  warnings?: string[]
  trace_id?: string
}

interface PromptOutputPanelProps {
  templateId?: string
  fields: TemplateField[]
  onPromptUpdate?: (prompt: string) => void
}

const PromptOutputPanel = ({ templateId, fields, onPromptUpdate }: PromptOutputPanelProps) => {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // 文件上传
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [filePreview, setFilePreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  
  // 识别模式
  const [recognitionMode, setRecognitionMode] = useState<'both' | 'extract' | 'prompt_only'>('both')
  
  // 识别结果
  const [extracting, setExtracting] = useState(false)
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null)
  
  // 提示词
  const [promptSuggestion, setPromptSuggestion] = useState<string>('')
  const [editedPrompt, setEditedPrompt] = useState<string>('')
  const [isPromptCollapsed, setIsPromptCollapsed] = useState(false)
  
  // 结果展示
  const [isResultCollapsed, setIsResultCollapsed] = useState(false)

  // 处理文件选择
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'application/pdf']
    if (!allowedTypes.includes(file.type)) {
      showErrorToast('不支持的文件类型，请上传图片（JPG/PNG/WEBP/GIF）或PDF文件')
      return
    }

    // 验证文件大小（最大10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorToast('文件大小不能超过10MB')
      return
    }

    setUploadedFile(file)
    
    // 生成预览
    if (file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setFilePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    } else if (file.type === 'application/pdf') {
      setFilePreview(null) // PDF预览需要特殊处理
    }
  }

  // 执行识别
  const handleExtract = async () => {
    if (!uploadedFile) {
      showErrorToast('请先上传发票文件')
      return
    }

    if (!fields || fields.length === 0) {
      showErrorToast('请先配置字段定义')
      return
    }

    // 新建模板时，如果没有templateId，使用临时ID或提示用户先保存模板
    if (!templateId) {
      showErrorToast('请先保存模板后再进行识别，或先配置字段定义')
      return
    }

    setExtracting(true)
    setExtractionResult(null)

    try {
      const token = localStorage.getItem('access_token')
      const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      // 构建字段定义
      const fieldDefinitions = fields.map(f => ({
        key: f.field_key,
        label: f.field_name,
        dataType: f.data_type,
        required: f.is_required,
        desc: f.description || '',
        example: f.example || '',
        format: f.validation?.format || f.validation?.pattern || '',
        aliases: f.validation?.aliases || [],
      }))

      // 创建FormData
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('template_id', templateId)
      formData.append('mode', recognitionMode)
      formData.append('field_definitions', JSON.stringify(fieldDefinitions))

      const response = await axios.post(
        `${apiBaseUrl}/api/v1/templates/${templateId}/extract`,
        formData,
        {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000, // 2分钟超时
        }
      )

      if (response.data) {
        const result: ExtractionResult = response.data.data || response.data
        setExtractionResult(result)
        setPromptSuggestion(result.prompt_suggestion || '')
        setEditedPrompt(result.prompt_suggestion || '')
        
        if (result.prompt_suggestion) {
          showSuccessToast('识别完成，已生成提示词建议')
        } else {
          showSuccessToast('识别完成')
        }
      }
    } catch (error: any) {
      console.error('识别失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '识别失败'
      showErrorToast(`识别失败: ${errorMessage}`)
    } finally {
      setExtracting(false)
    }
  }

  // 应用提示词
  const handleApplyPrompt = () => {
    if (!editedPrompt.trim()) {
      showErrorToast('提示词不能为空')
      return
    }
    
    if (onPromptUpdate) {
      onPromptUpdate(editedPrompt)
      showSuccessToast('提示词已应用')
    }
  }

  // 复制提示词
  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(editedPrompt)
    showSuccessToast('提示词已复制到剪贴板')
  }

  // 导出结果
  const handleExportResult = () => {
    if (!extractionResult) return

    const exportData = {
      prompt_suggestion: extractionResult.prompt_suggestion,
      extracted_data: extractionResult.extracted_data,
      field_status: extractionResult.field_status,
      warnings: extractionResult.warnings,
      trace_id: extractionResult.trace_id,
      export_time: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `extraction_result_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    showSuccessToast('结果已导出')
  }

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'green'
      case 'missing':
        return 'red'
      case 'format_error':
        return 'orange'
      case 'warning':
        return 'yellow'
      default:
        return 'gray'
    }
  }

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ok':
        return <FiCheckCircle />
      case 'missing':
        return <FiXCircle />
      case 'format_error':
      case 'warning':
        return <FiAlertCircle />
      default:
        return null
    }
  }

  return (
    <Box
      width="400px"
      minWidth="400px"
      height="100vh"
      bg="white"
      borderLeft="1px solid"
      borderColor="gray.200"
      display="flex"
      flexDirection="column"
      overflow="hidden"
      flexShrink={0}
    >
      {/* 标题栏 */}
      <Box p={4} borderBottom="1px" borderColor="gray.200">
        <Flex justify="space-between" align="center">
          <Text fontSize="lg" fontWeight="bold">
            提示词输出
          </Text>
        </Flex>
      </Box>

      {/* 内容区域 */}
      <Box flex="1" overflowY="auto" p={4}>
        <VStack spacing={4} align="stretch">
          {/* 文件上传区 */}
          <Box>
            <Text fontSize="sm" fontWeight="medium" mb={2}>
              发票上传
            </Text>
            <Box
              border="2px dashed"
              borderColor="gray.300"
              borderRadius="md"
              p={4}
              textAlign="center"
              cursor="pointer"
              _hover={{ borderColor: 'blue.400', bg: 'blue.50' }}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
              {uploadedFile ? (
                <VStack spacing={2}>
                  {filePreview ? (
                    <Box maxW="100%" maxH="200px" overflow="hidden" borderRadius="md">
                      <img src={filePreview} alt="预览" style={{ maxWidth: '100%', height: 'auto' }} />
                    </Box>
                  ) : (
                    <FiFile size={48} color="#718096" />
                  )}
                  <Text fontSize="sm" color="gray.600">
                    {uploadedFile.name}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    {(uploadedFile.size / 1024).toFixed(2)} KB
                  </Text>
                  <Button
                    size="xs"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation()
                      setUploadedFile(null)
                      setFilePreview(null)
                      if (fileInputRef.current) {
                        fileInputRef.current.value = ''
                      }
                    }}
                  >
                    重新选择
                  </Button>
                </VStack>
              ) : (
                <VStack spacing={2}>
                  <FiUpload size={48} color="#718096" />
                  <Text fontSize="sm" color="gray.600">
                    点击上传发票
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    支持 JPG/PNG/PDF，最大10MB
                  </Text>
                </VStack>
              )}
            </Box>
          </Box>

          {/* 识别模式选择 */}
          <Box>
            <Text fontSize="sm" fontWeight="medium" mb={2}>
              识别模式
            </Text>
            <select
              value={recognitionMode}
              onChange={(e) => setRecognitionMode(e.target.value as any)}
              style={{
                width: '100%',
                padding: '6px 12px',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontSize: '14px',
                backgroundColor: 'white'
              }}
            >
              <option value="both">抽取字段 + 生成提示词</option>
              <option value="extract">仅抽取字段值</option>
              <option value="prompt_only">仅生成提示词</option>
            </select>
          </Box>

          {/* 识别按钮 */}
          <Button
            colorScheme="blue"
            leftIcon={extracting ? <Spinner size="sm" /> : <FiRefreshCw />}
            onClick={handleExtract}
            isDisabled={!uploadedFile || extracting || (!templateId && fields.length === 0)}
            isLoading={extracting}
            loadingText="识别中..."
          >
            开始识别
          </Button>
          {!templateId && (
            <Box
              mt={2}
              p={2}
              bg="blue.50"
              borderRadius="md"
              border="1px"
              borderColor="blue.200"
              display="flex"
              alignItems="start"
            >
              <FiInfo style={{ marginRight: '8px', flexShrink: 0, marginTop: '2px' }} color="#3182ce" />
              <Text fontSize="xs" color="blue.700">
                新建模板时，请先保存模板后再进行识别，或先配置字段定义
              </Text>
            </Box>
          )}

          {/* 提示词区 */}
          {(promptSuggestion || extractionResult?.prompt_suggestion) && (
            <Box>
              <Flex justify="space-between" align="center" mb={2}>
                <Text fontSize="sm" fontWeight="medium">
                  提示词建议
                </Text>
                <HStack spacing={2}>
                  <IconButton
                    aria-label="折叠/展开"
                    title="折叠/展开"
                    icon={isPromptCollapsed ? <FiChevronDown /> : <FiChevronUp />}
                    size="xs"
                    variant="ghost"
                    onClick={() => setIsPromptCollapsed(!isPromptCollapsed)}
                  />
                  <IconButton
                    aria-label="复制"
                    title="复制"
                    icon={<FiCopy />}
                    size="xs"
                    variant="ghost"
                    onClick={handleCopyPrompt}
                  />
                  <IconButton
                    aria-label="应用"
                    title="应用"
                    icon={<FiSave />}
                    size="xs"
                    variant="ghost"
                    colorScheme="blue"
                    onClick={handleApplyPrompt}
                  />
                </HStack>
              </Flex>
              {!isPromptCollapsed && (
                <>
                  <Textarea
                    value={editedPrompt}
                    onChange={(e) => setEditedPrompt(e.target.value)}
                    placeholder="提示词建议将显示在这里..."
                    size="sm"
                    minH="200px"
                    fontFamily="mono"
                    fontSize="xs"
                  />
                  <Box
                    mt={2}
                    p={2}
                    bg="blue.50"
                    borderRadius="md"
                    border="1px"
                    borderColor="blue.200"
                    display="flex"
                    alignItems="start"
                  >
                    <FiInfo style={{ marginRight: '8px', flexShrink: 0, marginTop: '2px' }} color="#3182ce" />
                    <Text fontSize="xs" color="blue.700">
                      该提示词用于字段抽取，输出应为JSON格式。缺失字段请填写null。
                    </Text>
                  </Box>
                </>
              )}
            </Box>
          )}

          {/* 抽取结果区 */}
          {extractionResult && (
            <Box>
              <Flex justify="space-between" align="center" mb={2}>
                <Text fontSize="sm" fontWeight="medium">
                  抽取结果
                </Text>
                <HStack spacing={2}>
                  <IconButton
                    aria-label="折叠/展开"
                    title="折叠/展开"
                    icon={isResultCollapsed ? <FiChevronDown /> : <FiChevronUp />}
                    size="xs"
                    variant="ghost"
                    onClick={() => setIsResultCollapsed(!isResultCollapsed)}
                  />
                  <IconButton
                    aria-label="导出"
                    title="导出"
                    icon={<FiDownload />}
                    size="xs"
                    variant="ghost"
                    onClick={handleExportResult}
                  />
                </HStack>
              </Flex>
              {!isResultCollapsed && (
                <>
                  {/* 字段状态 */}
                  {extractionResult.field_status && extractionResult.field_status.length > 0 && (
                    <Box mb={4}>
                      <Text fontSize="xs" fontWeight="medium" mb={2}>
                        字段状态
                      </Text>
                      <Box overflowX="auto" maxH="200px">
                        <Table.Root size="sm">
                          <Table.Header>
                            <Table.Row>
                              <Table.ColumnHeader fontSize="xs">字段</Table.ColumnHeader>
                              <Table.ColumnHeader fontSize="xs">状态</Table.ColumnHeader>
                              <Table.ColumnHeader fontSize="xs">说明</Table.ColumnHeader>
                            </Table.Row>
                          </Table.Header>
                          <Table.Body>
                            {extractionResult.field_status.map((status, idx) => (
                              <Table.Row key={idx}>
                                <Table.Cell fontSize="xs">{status.key}</Table.Cell>
                                <Table.Cell>
                                  <Badge colorScheme={getStatusColor(status.status)} size="sm">
                                    {getStatusIcon(status.status)}
                                    {' '}
                                    {status.status === 'ok' ? '正常' : 
                                     status.status === 'missing' ? '缺失' :
                                     status.status === 'format_error' ? '格式错误' : '警告'}
                                  </Badge>
                                </Table.Cell>
                                <Table.Cell fontSize="xs">{status.message || '-'}</Table.Cell>
                              </Table.Row>
                            ))}
                          </Table.Body>
                        </Table.Root>
                      </Box>
                    </Box>
                  )}

                  {/* 抽取数据 */}
                  {extractionResult.extracted_data && (
                    <Box>
                      <Text fontSize="xs" fontWeight="medium" mb={2}>
                        抽取数据
                      </Text>
                      <Code
                        p={2}
                        display="block"
                        whiteSpace="pre-wrap"
                        fontSize="xs"
                        maxH="200px"
                        overflowY="auto"
                      >
                        {JSON.stringify(extractionResult.extracted_data, null, 2)}
                      </Code>
                    </Box>
                  )}

                  {/* 警告信息 */}
                  {extractionResult.warnings && extractionResult.warnings.length > 0 && (
                    <Box
                      mt={4}
                      p={2}
                      bg="yellow.50"
                      borderRadius="md"
                      border="1px"
                      borderColor="yellow.200"
                      display="flex"
                      alignItems="start"
                    >
                      <FiAlertCircle style={{ marginRight: '8px', flexShrink: 0, marginTop: '2px' }} color="#d69e2e" />
                      <VStack align="start" spacing={1}>
                        {extractionResult.warnings.map((warning, idx) => (
                          <Text key={idx} fontSize="xs" color="yellow.700">
                            {warning}
                          </Text>
                        ))}
                      </VStack>
                    </Box>
                  )}
                </>
              )}
            </Box>
          )}
        </VStack>
      </Box>
    </Box>
  )
}

export default PromptOutputPanel

