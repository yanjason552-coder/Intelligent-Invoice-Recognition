import React, { useState, useEffect } from "react"
import { Box, Text, Flex, Button, Input, IconButton, Table, Textarea, VStack, HStack } from "@chakra-ui/react"
import { FiSearch, FiEdit, FiTrash2, FiPlus, FiRefreshCw, FiShield } from "react-icons/fi"
import { getApiUrl, getAuthHeaders } from '../../client/unifiedTypes'
import useCustomToast from '../../hooks/useCustomToast'
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogBody,
  DialogFooter,
  DialogCloseTrigger,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"

interface Permission {
  id: string
  name: string
  code: string
  resource: string
  action: string
  description: string | null
  is_active: boolean
}

interface Role {
  id: string
  name: string
  code: string
}

const Permission = () => {
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedResource, setSelectedResource] = useState<string>("")
  const [isOpen, setIsOpen] = useState(false)
  const [isRolePermissionOpen, setIsRolePermissionOpen] = useState(false)
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null)
  const [selectedRole, setSelectedRole] = useState<string>("")
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    resource: "",
    action: "",
    description: "",
    is_active: true
  })

  const { showSuccessToast, showErrorToast } = useCustomToast()

  // 从菜单结构提取资源列表
  const getMenuResources = () => {
    const menuResources = new Set<string>()
    // 系统设置
    menuResources.add("company")
    menuResources.add("user")
    menuResources.add("role")
    menuResources.add("permission")
    // 票据管理
    menuResources.add("invoice")
    // 数据管理
    menuResources.add("recognition-result")
    menuResources.add("data-export")
    menuResources.add("data-statistics")
    // 系统配置
    menuResources.add("llm-config")
    menuResources.add("template")
    menuResources.add("recognition-rule")
    menuResources.add("review-workflow")
    return Array.from(menuResources)
  }

  const resources = getMenuResources()
  const actions = ["create", "read", "update", "delete", "list", "execute"]

  // 加载权限列表
  const loadPermissions = async () => {
    setIsLoading(true)
    try {
      const url = selectedResource 
        ? getApiUrl(`/permissions/?resource=${selectedResource}`)
        : getApiUrl('/permissions/')
      
      const response = await fetch(url, {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('加载权限列表失败')
      }

      const result = await response.json()
      if (result.data) {
        setPermissions(result.data)
      }
    } catch (error: any) {
      showErrorToast(error.message || '加载权限列表失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 加载角色列表
  const loadRoles = async () => {
    try {
      const response = await fetch(getApiUrl('/roles/'), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('加载角色列表失败')
      }

      const result = await response.json()
      if (result.data) {
        setRoles(result.data)
      }
    } catch (error: any) {
      showErrorToast(error.message || '加载角色列表失败')
    }
  }

  useEffect(() => {
    loadPermissions()
    loadRoles()
  }, [selectedResource])

  // 搜索过滤
  const filteredPermissions = permissions.filter(permission =>
    permission.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    permission.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    permission.resource.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // 打开新增/编辑对话框
  const handleOpenModal = (permission?: Permission) => {
    if (permission) {
      setEditingPermission(permission)
      setFormData({
        name: permission.name,
        code: permission.code,
        resource: permission.resource,
        action: permission.action,
        description: permission.description || "",
        is_active: permission.is_active
      })
    } else {
      setEditingPermission(null)
      setFormData({
        name: "",
        code: "",
        resource: "",
        action: "",
        description: "",
        is_active: true
      })
    }
    setIsOpen(true)
  }

  // 保存权限
  const handleSave = async () => {
    try {
      const url = editingPermission 
        ? getApiUrl(`/permissions/${editingPermission.id}`)
        : getApiUrl('/permissions/')
      
      const method = editingPermission ? 'PATCH' : 'POST'
      
      const body = {
        name: formData.name,
        code: formData.code,
        resource: formData.resource,
        action: formData.action,
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

      showSuccessToast(editingPermission ? '权限更新成功' : '权限创建成功')
      setIsOpen(false)
      loadPermissions()
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  // 删除权限
  const handleDelete = async (permissionId: string) => {
    if (!confirm('确定要删除该权限吗？')) {
      return
    }

    try {
      const response = await fetch(getApiUrl(`/permissions/${permissionId}`), {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('删除失败')
      }

      showSuccessToast('权限删除成功')
      loadPermissions()
    } catch (error: any) {
      showErrorToast(error.message || '删除失败')
    }
  }

  // 打开角色权限分配对话框
  const handleOpenRolePermissionModal = async (permissionId: string) => {
    try {
      // 加载拥有该权限的角色
      const response = await fetch(getApiUrl(`/permissions/${permissionId}/roles`), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const roleList = await response.json()
        setSelectedPermissions(roleList.map((r: Role) => r.id))
      }

      setSelectedRole(permissionId)
      setIsRolePermissionOpen(true)
    } catch (error: any) {
      showErrorToast('加载角色权限失败')
    }
  }

  // 保存角色权限分配
  const handleSaveRolePermission = async () => {
    if (!selectedRole) return

    try {
      // 先获取当前权限的所有角色
      const currentResponse = await fetch(getApiUrl(`/permissions/${selectedRole}/roles`), {
        method: 'GET',
        headers: getAuthHeaders()
      })
      
      let currentRoleIds: string[] = []
      if (currentResponse.ok) {
        const currentRoles = await currentResponse.json()
        currentRoleIds = currentRoles.map((r: Role) => r.id)
      }

      // 找出需要添加和删除的角色
      const toAdd = selectedPermissions.filter(id => !currentRoleIds.includes(id))
      const toRemove = currentRoleIds.filter(id => !selectedPermissions.includes(id))

      // 添加新角色（为角色分配权限）
      for (const roleId of toAdd) {
        await fetch(getApiUrl(`/permissions/roles/${roleId}/permissions/${selectedRole}`), {
          method: 'POST',
          headers: getAuthHeaders()
        })
      }

      // 删除旧角色（移除角色的权限）
      for (const roleId of toRemove) {
        await fetch(getApiUrl(`/permissions/roles/${roleId}/permissions/${selectedRole}`), {
          method: 'DELETE',
          headers: getAuthHeaders()
        })
      }

      showSuccessToast('角色权限分配成功')
      setIsRolePermissionOpen(false)
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  return (
    <Box p={4} h="100%" overflow="auto">
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">权限维护</Text>
        <Flex gap={2}>
          <Button
            leftIcon={<FiPlus />}
            colorScheme="blue"
            onClick={() => handleOpenModal()}
          >
            新增权限
          </Button>
          <IconButton
            aria-label="刷新"
            icon={<FiRefreshCw />}
            onClick={loadPermissions}
            isLoading={isLoading}
          />
        </Flex>
      </Flex>

      {/* 搜索和过滤 */}
      <Flex gap={2} mb={4}>
        <Box as="select"
          placeholder="选择资源"
          value={selectedResource}
          onChange={(e) => setSelectedResource(e.target.value)}
          maxW="200px"
          p={2}
          border="1px"
          borderColor="gray.300"
          borderRadius="md"
        >
          <option value="">全部资源</option>
          {resources.map(resource => (
            <option key={resource} value={resource}>{resource}</option>
          ))}
        </Box>
        <Input
          placeholder="搜索权限名称或代码..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          flex={1}
        />
        <IconButton
          aria-label="搜索"
          icon={<FiSearch />}
          onClick={loadPermissions}
        />
      </Flex>

      {/* 权限列表 */}
      <Box overflowX="auto">
        <Table.Root size={{ base: "sm", md: "md" }}>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>权限名称</Table.ColumnHeader>
              <Table.ColumnHeader>权限代码</Table.ColumnHeader>
              <Table.ColumnHeader>资源</Table.ColumnHeader>
              <Table.ColumnHeader>操作</Table.ColumnHeader>
              <Table.ColumnHeader>描述</Table.ColumnHeader>
              <Table.ColumnHeader>是否启用</Table.ColumnHeader>
              <Table.ColumnHeader>操作</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredPermissions.map((permission) => (
              <Table.Row key={permission.id}>
                <Table.Cell>{permission.name}</Table.Cell>
                <Table.Cell>{permission.code}</Table.Cell>
                <Table.Cell>{permission.resource}</Table.Cell>
                <Table.Cell>{permission.action}</Table.Cell>
                <Table.Cell>{permission.description || '-'}</Table.Cell>
                <Table.Cell>{permission.is_active ? '是' : '否'}</Table.Cell>
                <Table.Cell>
                  <Flex gap={2} wrap="wrap">
                    <Button
                      leftIcon={<FiEdit />}
                      size="sm"
                      onClick={() => handleOpenModal(permission)}
                    >
                      编辑
                    </Button>
                    <Button
                      leftIcon={<FiShield />}
                      size="sm"
                      colorScheme="green"
                      onClick={() => handleOpenRolePermissionModal(permission.id)}
                    >
                      分配角色
                    </Button>
                    <Button
                      leftIcon={<FiTrash2 />}
                      size="sm"
                      colorScheme="red"
                      onClick={() => handleDelete(permission.id)}
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
            <DialogTitle>{editingPermission ? '编辑权限' : '新增权限'}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Box>
              <Field mb={4} label="权限名称" required>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </Field>

              <Field mb={4} label="权限代码" required>
                <Input
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  disabled={!!editingPermission}
                />
              </Field>

              <Field mb={4} label="资源" required>
                <Box as="select"
                  value={formData.resource}
                  onChange={(e) => setFormData({ ...formData, resource: e.target.value })}
                  w="100%"
                  p={2}
                  border="1px"
                  borderColor="gray.300"
                  borderRadius="md"
                >
                  <option value="">请选择</option>
                  {resources.map(resource => (
                    <option key={resource} value={resource}>{resource}</option>
                  ))}
                </Box>
              </Field>

              <Field mb={4} label="操作" required>
                <Box as="select"
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  w="100%"
                  p={2}
                  border="1px"
                  borderColor="gray.300"
                  borderRadius="md"
                >
                  <option value="">请选择</option>
                  {actions.map(action => (
                    <option key={action} value={action}>{action}</option>
                  ))}
                </Box>
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

      {/* 角色权限分配对话框 */}
      <DialogRoot open={isRolePermissionOpen} onOpenChange={({ open }) => setIsRolePermissionOpen(open)}>
        <DialogContent>
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>分配角色</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <VStack align="stretch" spacing={4}>
              {roles.map(role => (
                <Checkbox
                  key={role.id}
                  checked={selectedPermissions.includes(role.id)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setSelectedPermissions([...selectedPermissions, role.id])
                    } else {
                      setSelectedPermissions(selectedPermissions.filter(id => id !== role.id))
                    }
                  }}
                >
                  {role.name} ({role.code})
                </Checkbox>
              ))}
              <Flex justify="flex-end" gap={2} mt={4}>
                <Button onClick={() => setIsRolePermissionOpen(false)}>取消</Button>
                <Button colorScheme="blue" onClick={handleSaveRolePermission}>
                  保存
                </Button>
              </Flex>
            </VStack>
          </DialogBody>
        </DialogContent>
      </DialogRoot>
    </Box>
  )
}

export default Permission

