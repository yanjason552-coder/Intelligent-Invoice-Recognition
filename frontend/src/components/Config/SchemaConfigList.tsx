import { Box, Text, Flex, VStack, Input, Badge } from "@chakra-ui/react"
import { FiEdit2, FiTrash2, FiPlus, FiRefreshCw, FiSearch } from "react-icons/fi"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
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

interface SchemaData {
  id: string
  name: string
  version: string
  schema_definition: any
  is_active: boolean
  is_default: boolean
  description?: string
  create_time?: string
  update_time?: string
}

const SchemaConfigList = () => {
  const [schemas, setSchemas] = useState<SchemaData[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [deleteDialogSchema, setDeleteDialogSchema] = useState<SchemaData | null>(null)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // 添加调试日志
  console.log('SchemaConfigList 组件已渲染')

  useEffect(() => {
    loadSchemas()
  }, [])

  const loadSchemas = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const response = await axios.get('/api/v1/config/schemas', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        params: {
          name: searchTerm || undefined
        }
      })
      if (response.data && response.data.data) {
        setSchemas(response.data.data)
      }
    } catch (error: any) {
      console.error('加载Schema列表失败:', error)
      showErrorToast('加载Schema列表失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    loadSchemas()
  }

  const handleDelete = async (schema: SchemaData) => {
    if (!schema.id) {
      showErrorToast('Schema ID不存在，无法删除')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      await axios.delete(`/api/v1/config/schemas/${schema.id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
      showSuccessToast(`Schema "${schema.name}" 删除成功`)
      setDeleteDialogSchema(null)
      await loadSchemas() // 重新加载列表
    } catch (error: any) {
      showErrorToast(error.response?.data?.detail || '删除失败')
    }
  }

  const handleEdit = (schema: SchemaData) => {
    // 触发自定义事件，通知父组件打开编辑页面
    const event = new CustomEvent('openTab', {
      detail: {
        id: `schema-edit-${schema.id}`,
        title: `编辑Schema: ${schema.name}`,
        type: 'schema-edit',
        data: schema
      }
    })
    window.dispatchEvent(event)
  }

  const handleCreate = () => {
    // 触发自定义事件，通知父组件打开创建页面
    const event = new CustomEvent('openTab', {
      detail: {
        id: 'schema-create',
        title: '创建Schema',
        type: 'schema-create',
        data: null
      }
    })
    window.dispatchEvent(event)
  }

  const formatSchemaPreview = (schemaDefinition: any) => {
    try {
      const properties = schemaDefinition.properties || {}
      const required = schemaDefinition.required || []
      const propertyCount = Object.keys(properties).length
      const requiredCount = required.length

      return `属性: ${propertyCount}个, 必填: ${requiredCount}个`
    } catch (error) {
      return "无法解析Schema"
    }
  }

  if (loading && schemas.length === 0) {
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
          Schema 配置列表
        </Text>
        <Flex gap={2}>
          <Button onClick={handleCreate} variant="outline">
            <FiPlus style={{ marginRight: '8px' }} />
            创建Schema
          </Button>
          <Button onClick={loadSchemas} variant="outline">
            <FiRefreshCw style={{ marginRight: '8px' }} />
            刷新
          </Button>
        </Flex>
      </Flex>

      {/* 搜索栏 */}
      <Flex gap={2} mb={6}>
        <Input
          placeholder="搜索Schema名称..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button onClick={handleSearch} variant="outline">
          <FiSearch style={{ marginRight: '8px' }} />
          搜索
        </Button>
      </Flex>

      {schemas.length === 0 ? (
        <Box p={8} textAlign="center" bg="gray.50" borderRadius="md">
          <Text color="gray.500">暂无Schema配置数据</Text>
          <Button onClick={handleCreate} mt={4} variant="outline">
            <FiPlus style={{ marginRight: '8px' }} />
            创建第一个Schema
          </Button>
        </Box>
      ) : (
        <Box
          maxH="calc(100vh - 300px)"
          overflowY="auto"
          overflowX="hidden"
          pr={2}
          className="custom-scrollbar"
        >
          <VStack gap={4} align="stretch" maxW="1200px">
            {schemas.map((schema) => (
              <Box
                key={schema.id}
                p={6}
                border="1px"
                borderColor="gray.200"
                borderRadius="md"
                bg="white"
                boxShadow="sm"
              >
                <VStack gap={4} align="stretch">
                  <Flex justify="space-between" align="center">
                    <Flex align="center" gap={3}>
                      <Text fontSize="lg" fontWeight="semibold" color="gray.800">
                        {schema.name}
                      </Text>
                      <Badge colorPalette="blue" variant="subtle">
                        v{schema.version}
                      </Badge>
                      {schema.is_default && (
                        <Badge colorPalette="green" variant="subtle">
                          默认
                        </Badge>
                      )}
                      {schema.is_active ? (
                        <Badge colorPalette="green" variant="subtle">
                          启用
                        </Badge>
                      ) : (
                        <Badge colorPalette="gray" variant="subtle">
                          停用
                        </Badge>
                      )}
                    </Flex>
                    <Flex gap={2}>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(schema)}
                      >
                        <FiEdit2 style={{ marginRight: '6px' }} />
                        编辑
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        colorPalette="red"
                        onClick={() => setDeleteDialogSchema(schema)}
                      >
                        <FiTrash2 style={{ marginRight: '6px' }} />
                        删除
                      </Button>
                    </Flex>
                  </Flex>

                  {schema.description && (
                    <Box pb={2} borderBottom="1px" borderColor="gray.100">
                      <Text fontSize="sm" color="gray.600">
                        {schema.description}
                      </Text>
                    </Box>
                  )}

                  <VStack gap={2} align="stretch" pt={2}>
                    <Flex gap={6} wrap="wrap">
                      <Box>
                        <Text fontSize="xs" color="gray.500" mb={1}>
                          Schema预览
                        </Text>
                        <Text fontSize="sm" color="gray.800" fontWeight="medium">
                          {formatSchemaPreview(schema.schema_definition)}
                        </Text>
                      </Box>
                    </Flex>

                    <Flex gap={6} wrap="wrap">
                      {schema.create_time && (
                        <Box>
                          <Text fontSize="xs" color="gray.500" mb={1}>
                            创建时间
                          </Text>
                          <Text fontSize="sm" color="gray.800" fontWeight="medium">
                            {new Date(schema.create_time).toLocaleString('zh-CN')}
                          </Text>
                        </Box>
                      )}
                      {schema.update_time && (
                        <Box>
                          <Text fontSize="xs" color="gray.500" mb={1}>
                            更新时间
                          </Text>
                          <Text fontSize="sm" color="gray.800" fontWeight="medium">
                            {new Date(schema.update_time).toLocaleString('zh-CN')}
                          </Text>
                        </Box>
                      )}
                    </Flex>
                  </VStack>
                </VStack>
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
        open={deleteDialogSchema !== null}
        onOpenChange={({ open }) => !open && setDeleteDialogSchema(null)}
      >
        <DialogContent>
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>确认删除Schema</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              您确定要删除Schema <strong>"{deleteDialogSchema?.name}"</strong> 吗？此操作将直接从数据库中删除该Schema，且无法恢复。
            </Text>
            {deleteDialogSchema?.is_default && (
              <Text color="red.600" fontSize="sm">
                注意：这是一个默认Schema，删除后可能影响相关功能的正常运行。
              </Text>
            )}
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
              >
                取消
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="red"
              onClick={() => deleteDialogSchema && handleDelete(deleteDialogSchema)}
            >
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </DialogRoot>
    </Box>
  )
}

export default SchemaConfigList
