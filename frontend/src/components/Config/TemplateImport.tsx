import { Box, Text, Flex, VStack, HStack, Input, Badge, IconButton } from "@chakra-ui/react"
import { FiUpload, FiFile, FiX, FiCheckCircle, FiAlertCircle } from "react-icons/fi"
import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from '@/hooks/useCustomToast'
import axios from 'axios'

interface ImportResult {
  success: boolean
  template_id?: string
  template_name?: string
  fields_count?: number
  message?: string
  errors?: string[]
}

const TemplateImport = () => {
  const [file, setFile] = useState<File | null>(null)
  const [templateName, setTemplateName] = useState('')
  const [templateType, setTemplateType] = useState('其他')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // 模板类型选项
  const templateTypeOptions = [
    { value: '增值税发票', label: '增值税发票' },
    { value: '普通发票', label: '普通发票' },
    { value: '采购订单', label: '采购订单' },
    { value: '收据', label: '收据' },
    { value: '出库单', label: '出库单' },
    { value: '入库单', label: '入库单' },
    { value: '其他', label: '其他' }
  ]

  // 处理文件选择
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (!selectedFile) return

    // 验证文件类型
    const fileName = selectedFile.name.toLowerCase()
    const isExcel = fileName.endsWith('.xlsx') || fileName.endsWith('.xls')
    const isJson = fileName.endsWith('.json')

    if (!isExcel && !isJson) {
      showErrorToast('请选择 Excel 文件 (.xlsx, .xls) 或 JSON 文件 (.json)')
      return
    }

    // 如果文件是 Excel，自动提取文件名作为模板名称
    if (isExcel && !templateName) {
      const nameWithoutExt = selectedFile.name.replace(/\.(xlsx|xls)$/i, '')
      setTemplateName(nameWithoutExt)
    }

    setFile(selectedFile)
    setImportResult(null)
  }

  // 处理文件删除
  const handleRemoveFile = () => {
    setFile(null)
    setImportResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // 处理导入
  const handleImport = async () => {
    if (!file) {
      showErrorToast('请选择要导入的文件')
      return
    }

    if (!templateName.trim()) {
      showErrorToast('请输入模板名称')
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setImportResult(null)

    try {
      const token = localStorage.getItem('access_token')
      const formData = new FormData()
      formData.append('file', file)
      formData.append('name', templateName)
      formData.append('template_type', templateType)
      if (description) {
        formData.append('description', description)
      }

      const response = await axios.post('/api/v1/templates/import', formData, {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000, // 5分钟超时（300秒），与后端保持一致
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(percentCompleted)
            // 上传完成后，进度条保持在95%，等待服务器处理
            if (percentCompleted >= 100) {
              setUploadProgress(95)
            }
          }
        }
      })
      
      // 服务器响应后，进度条到100%
      setUploadProgress(100)

      if (response.data) {
        const result: ImportResult = {
          success: true,
          template_id: response.data.data?.template_id,
          template_name: response.data.data?.template_name,
          fields_count: response.data.data?.fields_count,
          message: response.data.message || '导入成功'
        }
        setImportResult(result)
        showSuccessToast(`模板导入成功！共识别 ${result.fields_count || 0} 个字段`)

        // 通知模板列表刷新
        const refreshEvent = new CustomEvent('refreshTemplateList')
        window.dispatchEvent(refreshEvent)

        // 3秒后跳转到编辑页面
        setTimeout(() => {
          if (result.template_id) {
            const event = new CustomEvent('openTab', {
              detail: {
                type: 'template-edit',
                data: {
                  templateId: result.template_id
                }
              }
            })
            window.dispatchEvent(event)
          }
        }, 3000)
      }
    } catch (error: any) {
      console.error('导入失败:', error)
      
      // 处理超时错误
      let errorMessage = '导入失败'
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = '请求超时，请检查网络连接或稍后重试。如果问题持续，请检查后端服务是否正常运行。'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      const result: ImportResult = {
        success: false,
        message: errorMessage,
        errors: error.response?.data?.errors || []
      }
      setImportResult(result)
      showErrorToast(errorMessage)
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  // 处理继续导入
  const handleContinueImport = () => {
    setFile(null)
    setTemplateName('')
    setDescription('')
    setImportResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <Box p={6} maxW="800px" mx="auto">
      <VStack spacing={6} align="stretch">
        {/* 标题 */}
        <Box>
          <Text fontSize="2xl" fontWeight="bold" mb={2}>
            导入模板
          </Text>
          <Text fontSize="sm" color="gray.600">
            支持 Excel (.xlsx, .xls) 和 JSON (.json) 格式。上传后将自动解析字段并创建模板草稿。
          </Text>
        </Box>

        {/* 文件上传区域 */}
        <Box
          border="2px dashed"
          borderColor={file ? "green.300" : "gray.300"}
          borderRadius="md"
          p={8}
          textAlign="center"
          bg={file ? "green.50" : "gray.50"}
          transition="all 0.3s"
        >
          {!file ? (
            <VStack spacing={4}>
              <FiUpload size={48} color="#718096" />
              <Box>
                <Text fontSize="lg" fontWeight="medium" mb={2}>
                  选择文件
                </Text>
                <Text fontSize="sm" color="gray.600" mb={4}>
                  支持 Excel 或 JSON 格式
                </Text>
                <Input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.json"
                  onChange={handleFileSelect}
                  display="none"
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  leftIcon={<FiUpload />}
                  colorScheme="blue"
                >
                  选择文件
                </Button>
              </Box>
            </VStack>
          ) : (
            <VStack spacing={4}>
              <FiFile size={48} color="#48BB78" />
              <Box>
                <Text fontSize="lg" fontWeight="medium" mb={2}>
                  {file.name}
                </Text>
                <Text fontSize="sm" color="gray.600">
                  {(file.size / 1024).toFixed(2)} KB
                </Text>
              </Box>
              <IconButton
                aria-label="删除文件"
                icon={<FiX />}
                onClick={handleRemoveFile}
                colorScheme="red"
                variant="ghost"
                size="sm"
              />
            </VStack>
          )}
        </Box>

        {/* 上传进度 */}
        {uploading && (
          <Box>
            <Flex justify="space-between" mb={2}>
              <Text fontSize="sm" color="gray.600">
                上传中...
              </Text>
              <Text fontSize="sm" color="gray.600">
                {uploadProgress}%
              </Text>
            </Flex>
            <Box
              w="100%"
              h="8px"
              bg="gray.200"
              borderRadius="full"
              overflow="hidden"
            >
              <Box
                h="100%"
                bg="blue.500"
                width={`${uploadProgress}%`}
                transition="width 0.3s"
                borderRadius="full"
              />
            </Box>
          </Box>
        )}

        {/* 模板信息表单 */}
        {file && !uploading && (
          <Box bg="white" p={6} borderRadius="md" border="1px" borderColor="gray.200">
            <VStack spacing={4} align="stretch">
              <Field label="模板名称" required>
                <Input
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="请输入模板名称"
                />
              </Field>

              <Field label="模板类型" required>
                <select
                  value={templateType}
                  onChange={(e) => setTemplateType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '4px'
                  }}
                >
                  {templateTypeOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="模板描述">
                <Input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="请输入模板描述（可选）"
                />
              </Field>
            </VStack>
          </Box>
        )}

        {/* 导入结果 */}
        {importResult && (
          <Box
            bg={importResult.success ? "green.50" : "red.50"}
            p={6}
            borderRadius="md"
            border="1px"
            borderColor={importResult.success ? "green.200" : "red.200"}
          >
            <VStack spacing={4} align="stretch">
              <Flex align="center" gap={2}>
                {importResult.success ? (
                  <FiCheckCircle size={24} color="#48BB78" />
                ) : (
                  <FiAlertCircle size={24} color="#F56565" />
                )}
                <Text
                  fontSize="lg"
                  fontWeight="medium"
                  color={importResult.success ? "green.700" : "red.700"}
                >
                  {importResult.success ? '导入成功' : '导入失败'}
                </Text>
              </Flex>

              {importResult.success ? (
                <VStack spacing={2} align="stretch">
                  <Text fontSize="sm" color="gray.700">
                    <strong>模板名称：</strong>{importResult.template_name}
                  </Text>
                  <Text fontSize="sm" color="gray.700">
                    <strong>识别字段数：</strong>{importResult.fields_count || 0}
                  </Text>
                  <Text fontSize="sm" color="gray.600" mt={2}>
                    3秒后将自动跳转到模板编辑页面...
                  </Text>
                </VStack>
              ) : (
                <VStack spacing={2} align="stretch">
                  <Text fontSize="sm" color="red.700">
                    {importResult.message}
                  </Text>
                  {importResult.errors && importResult.errors.length > 0 && (
                    <Box>
                      <Text fontSize="sm" fontWeight="medium" color="red.700" mb={2}>
                        错误详情：
                      </Text>
                      <VStack spacing={1} align="stretch">
                        {importResult.errors.map((error, index) => (
                          <Text key={index} fontSize="xs" color="red.600">
                            • {error}
                          </Text>
                        ))}
                      </VStack>
                    </Box>
                  )}
                </VStack>
              )}
            </VStack>
          </Box>
        )}

        {/* 操作按钮 */}
        <Flex justify="flex-end" gap={3}>
          {importResult?.success ? (
            <>
              <Button
                onClick={handleContinueImport}
                variant="outline"
              >
                继续导入
              </Button>
              <Button
                onClick={() => {
                  if (importResult.template_id) {
                    const event = new CustomEvent('openTemplateEditTab', {
                      detail: {
                        templateId: importResult.template_id,
                        templateData: {
                          id: importResult.template_id,
                          name: importResult.template_name
                        }
                      }
                    })
                    window.dispatchEvent(event)
                  }
                }}
                colorScheme="blue"
              >
                立即编辑
              </Button>
            </>
          ) : (
            <>
              <Button
                onClick={() => {
                  const event = new CustomEvent('closeTab', { detail: { tabId: 'template-import' } })
                  window.dispatchEvent(event)
                }}
                variant="outline"
              >
                取消
              </Button>
              <Button
                onClick={handleImport}
                leftIcon={<FiUpload />}
                colorScheme="blue"
                isLoading={uploading}
                isDisabled={!file || !templateName.trim()}
              >
                开始导入
              </Button>
            </>
          )}
        </Flex>

        {/* 使用说明 */}
        <Box bg="blue.50" p={4} borderRadius="md" border="1px" borderColor="blue.200">
          <Text fontSize="sm" fontWeight="medium" color="blue.700" mb={2}>
            使用说明：
          </Text>
          <VStack spacing={1} align="stretch" fontSize="xs" color="blue.600">
            <Text>• Excel 格式：第一行为字段名称（中文），每一列代表一个字段</Text>
            <Text>• JSON 格式：包含 name, template_type, fields 等字段的 JSON 对象</Text>
            <Text>• 系统会自动识别字段类型，并区分头字段和明细字段</Text>
            <Text>• 导入后将创建模板草稿，可在编辑页面中进一步调整</Text>
          </VStack>
        </Box>
      </VStack>
    </Box>
  )
}

export default TemplateImport

