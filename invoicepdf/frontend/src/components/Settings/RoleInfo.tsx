import React, { useState, useEffect } from "react"
import { Box, Text, Flex, Button, Input, IconButton, Table, Textarea } from "@chakra-ui/react"
import { FiSearch, FiEdit, FiTrash2, FiPlus, FiRefreshCw, FiUsers, FiShield } from "react-icons/fi"
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

interface Role {
  id: string
  name: string
  code: string
  description: string | null
  is_active: boolean
}

interface Permission {
  id: string
  name: string
  code: string
  resource: string
  action: string
}

interface User {
  id: string
  email: string
  full_name: string | null
}

const RoleInfo = () => {
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [isOpen, setIsOpen] = useState(false)
  const [isPermissionOpen, setIsPermissionOpen] = useState(false)
  const [isUserOpen, setIsUserOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [selectedRoleId, setSelectedRoleId] = useState<string>("")
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([])
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    description: "",
    is_active: true
  })

  const { showSuccessToast, showErrorToast } = useCustomToast()

  // 加载角色列表
  const loadRoles = async () => {
    setIsLoading(true)
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
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadRoles()
  }, [])

  // 搜索过滤
  const filteredRoles = roles.filter(role =>
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (role.description && role.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // 打开新增/编辑对话框
  const handleOpenModal = (role?: Role) => {
    if (role) {
      setEditingRole(role)
      setFormData({
        name: role.name,
        code: role.code,
        description: role.description || "",
        is_active: role.is_active
      })
    } else {
      setEditingRole(null)
      setFormData({
        name: "",
        code: "",
        description: "",
        is_active: true
      })
    }
    setIsOpen(true)
  }

  // 保存角色
  const handleSave = async () => {
    try {
      const url = editingRole 
        ? getApiUrl(`/roles/${editingRole.id}`)
        : getApiUrl('/roles/')
      
      const method = editingRole ? 'PATCH' : 'POST'
      
      const body = {
        name: formData.name,
        code: formData.code,
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

      showSuccessToast(editingRole ? '角色更新成功' : '角色创建成功')
      setIsOpen(false)
      loadRoles()
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  // 删除角色
  const handleDelete = async (roleId: string) => {
    if (!confirm('确定要删除该角色吗？')) {
      return
    }

    try {
      const response = await fetch(getApiUrl(`/roles/${roleId}`), {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('删除失败')
      }

      showSuccessToast('角色删除成功')
      loadRoles()
    } catch (error: any) {
      showErrorToast(error.message || '删除失败')
    }
  }

  // 打开权限管理对话框
  const handleOpenPermissionModal = async (roleId: string) => {
    try {
      // 加载角色的权限
      const response = await fetch(getApiUrl(`/permissions/roles/${roleId}/permissions`), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const permissionList = await response.json()
        setSelectedPermissions(permissionList.map((p: Permission) => p.id))
      }

      setSelectedRoleId(roleId)
      setIsPermissionOpen(true)
    } catch (error: any) {
      showErrorToast('加载权限失败')
    }
  }

  // 保存权限
  const handleSavePermissions = async () => {
    if (!selectedRoleId) return

    try {
      // 先获取当前角色的所有权限
      const currentResponse = await fetch(getApiUrl(`/permissions/roles/${selectedRoleId}/permissions`), {
        method: 'GET',
        headers: getAuthHeaders()
      })
      
      let currentPermissionIds: string[] = []
      if (currentResponse.ok) {
        const currentPermissions = await currentResponse.json()
        currentPermissionIds = currentPermissions.map((p: Permission) => p.id)
      }

      // 找出需要添加和删除的权限
      const toAdd = selectedPermissions.filter(id => !currentPermissionIds.includes(id))
      const toRemove = currentPermissionIds.filter(id => !selectedPermissions.includes(id))

      // 添加新权限
      for (const permissionId of toAdd) {
        await fetch(getApiUrl(`/permissions/roles/${selectedRoleId}/permissions/${permissionId}`), {
          method: 'POST',
          headers: getAuthHeaders()
        })
      }

      // 删除旧权限
      for (const permissionId of toRemove) {
        await fetch(getApiUrl(`/permissions/roles/${selectedRoleId}/permissions/${permissionId}`), {
          method: 'DELETE',
          headers: getAuthHeaders()
        })
      }

      showSuccessToast('权限保存成功')
      setIsPermissionOpen(false)
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  // 打开用户管理对话框
  const handleOpenUserModal = async (roleId: string) => {
    try {
      // 加载角色的用户
      const response = await fetch(getApiUrl(`/roles/${roleId}/users`), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const userRoleList = await response.json()
        setSelectedUsers(userRoleList.map((ur: any) => ur.user_id))
      }

      setSelectedRoleId(roleId)
      setIsUserOpen(true)
    } catch (error: any) {
      showErrorToast('加载用户失败')
    }
  }

  // 保存用户
  const handleSaveUsers = async () => {
    if (!selectedRoleId) return

    try {
      // 先获取当前角色的所有用户
      const currentResponse = await fetch(getApiUrl(`/roles/${selectedRoleId}/users`), {
        method: 'GET',
        headers: getAuthHeaders()
      })
      
      let currentUserIds: string[] = []
      if (currentResponse.ok) {
        const currentUserRoles = await currentResponse.json()
        currentUserIds = currentUserRoles.map((ur: any) => ur.user_id)
      }

      // 找出需要添加和删除的用户
      const toAdd = selectedUsers.filter(id => !currentUserIds.includes(id))
      const toRemove = currentUserIds.filter(id => !selectedUsers.includes(id))

      // 添加新用户
      for (const userId of toAdd) {
        await fetch(getApiUrl(`/roles/${selectedRoleId}/users/${userId}`), {
          method: 'POST',
          headers: getAuthHeaders()
        })
      }

      // 删除旧用户
      for (const userId of toRemove) {
        await fetch(getApiUrl(`/roles/${selectedRoleId}/users/${userId}`), {
          method: 'DELETE',
          headers: getAuthHeaders()
        })
      }

      showSuccessToast('用户保存成功')
      setIsUserOpen(false)
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  return (
    <Box p={4} h="100%" overflow="auto">
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">角色信息管理</Text>
        <Flex gap={2}>
          <Button
            leftIcon={<FiPlus />}
            colorScheme="blue"
            onClick={() => handleOpenModal()}
          >
            新增角色
          </Button>
          <IconButton
            aria-label="刷新"
            icon={<FiRefreshCw />}
            onClick={loadRoles}
            isLoading={isLoading}
          />
        </Flex>
      </Flex>

      {/* 搜索框 */}
      <Box mb={4}>
        <Flex>
          <Input
            placeholder="搜索角色名称或代码..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            mr={2}
          />
          <IconButton
            aria-label="搜索"
            icon={<FiSearch />}
            onClick={loadRoles}
          />
        </Flex>
      </Box>

      {/* 角色列表 */}
      <Box overflowX="auto">
        <Table.Root size={{ base: "sm", md: "md" }}>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>角色名称</Table.ColumnHeader>
              <Table.ColumnHeader>角色代码</Table.ColumnHeader>
              <Table.ColumnHeader>描述</Table.ColumnHeader>
              <Table.ColumnHeader>是否启用</Table.ColumnHeader>
              <Table.ColumnHeader>操作</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredRoles.map((role) => (
              <Table.Row key={role.id}>
                <Table.Cell>{role.name}</Table.Cell>
                <Table.Cell>{role.code}</Table.Cell>
                <Table.Cell>{role.description || '-'}</Table.Cell>
                <Table.Cell>{role.is_active ? '是' : '否'}</Table.Cell>
                <Table.Cell>
                  <Flex gap={2}>
                    <Button
                      leftIcon={<FiEdit />}
                      size="sm"
                      onClick={() => handleOpenModal(role)}
                    >
                      编辑
                    </Button>
                    <Button
                      leftIcon={<FiShield />}
                      size="sm"
                      colorScheme="green"
                      onClick={() => handleOpenPermissionModal(role.id)}
                    >
                      管理权限
                    </Button>
                    <Button
                      leftIcon={<FiUsers />}
                      size="sm"
                      colorScheme="blue"
                      onClick={() => handleOpenUserModal(role.id)}
                    >
                      管理用户
                    </Button>
                    <Button
                      leftIcon={<FiTrash2 />}
                      size="sm"
                      colorScheme="red"
                      onClick={() => handleDelete(role.id)}
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
            <DialogTitle>{editingRole ? '编辑角色' : '新增角色'}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Box>
              <Field mb={4} label="角色名称" required>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </Field>

              <Field mb={4} label="角色代码" required>
                <Input
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  disabled={!!editingRole}
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

      {/* 权限管理对话框 */}
      <DialogRoot open={isPermissionOpen} onOpenChange={({ open }) => setIsPermissionOpen(open)}>
        <DialogContent maxW="600px">
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>管理角色权限</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Box maxH="400px" overflowY="auto">
              {permissions.map(permission => (
                <Box key={permission.id} mb={2}>
                  <Checkbox
                    checked={selectedPermissions.includes(permission.id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedPermissions([...selectedPermissions, permission.id])
                      } else {
                        setSelectedPermissions(selectedPermissions.filter(id => id !== permission.id))
                      }
                    }}
                  >
                    {permission.name} ({permission.code}) - {permission.resource}.{permission.action}
                  </Checkbox>
                </Box>
              ))}
            </Box>
            <Flex justify="flex-end" gap={2} mt={4}>
              <Button onClick={() => setIsPermissionOpen(false)}>取消</Button>
              <Button colorScheme="blue" onClick={handleSavePermissions}>
                保存
              </Button>
            </Flex>
          </DialogBody>
        </DialogContent>
      </DialogRoot>

      {/* 用户管理对话框 */}
      <DialogRoot open={isUserOpen} onOpenChange={({ open }) => setIsUserOpen(open)}>
        <DialogContent maxW="500px">
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>管理角色用户</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Box maxH="400px" overflowY="auto">
              {users.map(user => (
                <Box key={user.id} mb={2}>
                  <Checkbox
                    checked={selectedUsers.includes(user.id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedUsers([...selectedUsers, user.id])
                      } else {
                        setSelectedUsers(selectedUsers.filter(id => id !== user.id))
                      }
                    }}
                  >
                    {user.full_name || user.email}
                  </Checkbox>
                </Box>
              ))}
            </Box>
            <Flex justify="flex-end" gap={2} mt={4}>
              <Button onClick={() => setIsUserOpen(false)}>取消</Button>
              <Button colorScheme="blue" onClick={handleSaveUsers}>
                保存
              </Button>
            </Flex>
          </DialogBody>
        </DialogContent>
      </DialogRoot>
    </Box>
  )
}

export default RoleInfo

