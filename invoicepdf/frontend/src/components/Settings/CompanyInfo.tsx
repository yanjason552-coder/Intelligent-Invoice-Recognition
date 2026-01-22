import React, { useState, useEffect } from "react"
import { Box, Text, Flex, Button, Input, IconButton, Table, Textarea } from "@chakra-ui/react"
import { FiSearch, FiEdit, FiTrash2, FiPlus, FiRefreshCw } from "react-icons/fi"
import { getApiUrl, getAuthHeaders } from '../../client/unifiedTypes'
import useCustomToast from '../../hooks/useCustomToast'
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogBody,
  DialogCloseTrigger,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import { Switch } from "@/components/ui/switch"

interface Company {
  id: string
  name: string
  code: string
  address: string | null
  contact_person: string | null
  contact_phone: string | null
  contact_email: string | null
  description: string | null
  is_active: boolean
  user_count: number
}

const CompanyInfo = () => {
  const [companies, setCompanies] = useState<Company[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [isOpen, setIsOpen] = useState(false)
  const [editingCompany, setEditingCompany] = useState<Company | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    address: "",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    description: "",
    is_active: true
  })

  const { showSuccessToast, showErrorToast } = useCustomToast()

  // 加载公司列表
  const loadCompanies = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(getApiUrl('/companies/'), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('加载公司列表失败')
      }

      const result = await response.json()
      if (result.data) {
        setCompanies(result.data)
      }
    } catch (error: any) {
      showErrorToast(error.message || '加载公司列表失败')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadCompanies()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 搜索过滤
  const filteredCompanies = companies.filter(company =>
    company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    company.code.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // 打开新增/编辑对话框
  const handleOpenModal = (company?: Company) => {
    if (company) {
      setEditingCompany(company)
      setFormData({
        name: company.name,
        code: company.code,
        address: company.address || "",
        contact_person: company.contact_person || "",
        contact_phone: company.contact_phone || "",
        contact_email: company.contact_email || "",
        description: company.description || "",
        is_active: company.is_active
      })
    } else {
      setEditingCompany(null)
      setFormData({
        name: "",
        code: "",
        address: "",
        contact_person: "",
        contact_phone: "",
        contact_email: "",
        description: "",
        is_active: true
      })
    }
    setIsOpen(true)
  }

  // 保存公司
  const handleSave = async () => {
    try {
      const url = editingCompany 
        ? getApiUrl(`/companies/${editingCompany.id}`)
        : getApiUrl('/companies/')
      
      const method = editingCompany ? 'PATCH' : 'POST'
      
      const body = {
        name: formData.name,
        code: formData.code,
        address: formData.address || null,
        contact_person: formData.contact_person || null,
        contact_phone: formData.contact_phone || null,
        contact_email: formData.contact_email || null,
        description: formData.description || null,
        is_active: formData.is_active
      }

      const response = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify(body)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '保存失败')
      }

      showSuccessToast(editingCompany ? '公司更新成功' : '公司创建成功')
      setIsOpen(false)
      loadCompanies()
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  // 删除公司
  const handleDelete = async (companyId: string) => {
    if (!confirm('确定要删除该公司吗？')) {
      return
    }

    try {
      const response = await fetch(getApiUrl(`/companies/${companyId}`), {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '删除失败')
      }

      showSuccessToast('公司删除成功')
      loadCompanies()
    } catch (error: any) {
      showErrorToast(error.message || '删除失败')
    }
  }

  return (
    <Box p={4} h="100%" overflow="auto">
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">公司信息管理</Text>
        <Flex gap={2}>
          <Button
            leftIcon={<FiPlus />}
            colorScheme="blue"
            onClick={() => handleOpenModal()}
          >
            新增公司
          </Button>
          <IconButton
            aria-label="刷新"
            icon={<FiRefreshCw />}
            onClick={loadCompanies}
            isLoading={isLoading}
          />
        </Flex>
      </Flex>

      {/* 搜索框 */}
      <Box mb={4}>
        <Flex>
          <Input
            placeholder="搜索公司名称或代码..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            mr={2}
          />
          <IconButton
            aria-label="搜索"
            icon={<FiSearch />}
            onClick={loadCompanies}
          />
        </Flex>
      </Box>

      {/* 公司列表 */}
      <Box overflowX="auto">
        <Table.Root size={{ base: "sm", md: "md" }}>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>公司名称</Table.ColumnHeader>
              <Table.ColumnHeader>公司代码</Table.ColumnHeader>
              <Table.ColumnHeader>联系人</Table.ColumnHeader>
              <Table.ColumnHeader>联系电话</Table.ColumnHeader>
              <Table.ColumnHeader>关联用户数</Table.ColumnHeader>
              <Table.ColumnHeader>是否启用</Table.ColumnHeader>
              <Table.ColumnHeader>操作</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredCompanies.map((company) => (
              <Table.Row key={company.id}>
                <Table.Cell>{company.name}</Table.Cell>
                <Table.Cell>{company.code}</Table.Cell>
                <Table.Cell>{company.contact_person || '-'}</Table.Cell>
                <Table.Cell>{company.contact_phone || '-'}</Table.Cell>
                <Table.Cell>{company.user_count || 0}</Table.Cell>
                <Table.Cell>{company.is_active ? '是' : '否'}</Table.Cell>
                <Table.Cell>
                  <Flex gap={2}>
                    <Button
                      leftIcon={<FiEdit />}
                      size="sm"
                      onClick={() => handleOpenModal(company)}
                    >
                      编辑
                    </Button>
                    <Button
                      leftIcon={<FiTrash2 />}
                      size="sm"
                      colorScheme="red"
                      onClick={() => handleDelete(company.id)}
                    >
                      删除
                    </Button>
                  </Flex>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>

      {/* 新增/编辑对话框 */}
      <DialogRoot open={isOpen} onOpenChange={({ open }) => setIsOpen(open)}>
        <DialogContent>
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>{editingCompany ? '编辑公司' : '新增公司'}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Box>
              <Field mb={4} label="公司名称" required>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </Field>

              <Field mb={4} label="公司代码" required>
                <Input
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  disabled={!!editingCompany}
                />
              </Field>

              <Field mb={4} label="公司地址">
                <Input
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                />
              </Field>

              <Field mb={4} label="联系人">
                <Input
                  value={formData.contact_person}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                />
              </Field>

              <Field mb={4} label="联系电话">
                <Input
                  value={formData.contact_phone}
                  onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                />
              </Field>

              <Field mb={4} label="联系邮箱">
                <Input
                  value={formData.contact_email}
                  onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                  type="email"
                />
              </Field>

              <Field mb={4} label="描述">
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </Field>

              <Field mb={4} label="是否启用">
                <Switch
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                />
              </Field>

              <Flex justify="flex-end" gap={2} mt={4}>
                <Button onClick={() => setIsOpen(false)}>取消</Button>
                <Button colorScheme="blue" onClick={handleSave}>
                  保存
                </Button>
              </Flex>
            </Box>
          </DialogBody>
        </DialogContent>
      </DialogRoot>
    </Box>
  )
}

export default CompanyInfo

