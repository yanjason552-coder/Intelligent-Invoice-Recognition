import React, { useState, useEffect, useRef } from "react"
import { Box, Text, Flex, Button, Input, IconButton, Table, Badge, HStack } from "@chakra-ui/react"
import { FiSearch, FiEdit, FiTrash2, FiPlus, FiRefreshCw, FiShield, FiChevronDown, FiX } from "react-icons/fi"
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
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"

interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  company_id: string | null  // 保留向后兼容
  company_ids: string[] | null  // 新增：关联的公司ID列表
  primary_company_id: string | null  // 新增：主公司ID
  companies: Array<{
    id: string
    code: string
    name: string
    is_primary: boolean
  }> | null  // 新增：关联的公司详细信息列表
}

interface Company {
  id: string
  name: string
  code: string
}

interface Role {
  id: string
  name: string
  code: string
  description: string | null
  is_active: boolean
}

const UserInfo = () => {
  const [users, setUsers] = useState<User[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [userRoles, setUserRoles] = useState<Record<string, Role[]>>({}) // 用户ID -> 角色列表
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [isOpen, setIsOpen] = useState(false)
  const [isResetPasswordOpen, setIsResetPasswordOpen] = useState(false)
  const [isRoleOpen, setIsRoleOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [resetPasswordUserId, setResetPasswordUserId] = useState<string>("")
  const [newPassword, setNewPassword] = useState("")
  const [selectedUserId, setSelectedUserId] = useState<string>("")
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([])
  const [isCompanyDropdownOpen, setIsCompanyDropdownOpen] = useState(false)
  const companyDropdownRef = useRef<HTMLDivElement>(null)
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    is_active: true,
    is_superuser: false,
    password: "",
    company_ids: [] as string[],  // 改为数组，支持多个公司
    primary_company_id: ""  // 主公司ID
  })

  const { showSuccessToast, showErrorToast } = useCustomToast()

  // 加载用户列表
  const loadUsers = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(getApiUrl('/users/'), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('加载用户列表失败')
      }

      const result = await response.json()
      if (result.data) {
        setUsers(result.data)
      }
    } catch (error: any) {
      showErrorToast(error.message || '加载用户列表失败')
    } finally {
      setIsLoading(false)
    }
  }

  // 加载公司列表
  const loadCompanies = async () => {
    try {
      const response = await fetch(getApiUrl('/companies/'), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const result = await response.json()
        if (result.data) {
          setCompanies(result.data)
        } else {
          console.warn('公司列表数据为空')
          setCompanies([])
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: '加载公司列表失败' }))
        console.error('加载公司列表失败:', errorData)
        showErrorToast(errorData.detail || '加载公司列表失败')
        setCompanies([])
      }
    } catch (error: any) {
      console.error('加载公司列表失败:', error)
      showErrorToast(error.message || '加载公司列表失败')
      setCompanies([])
    }
  }

  // 加载角色列表
  const loadRoles = async () => {
    try {
      const response = await fetch(getApiUrl('/roles/'), {
        method: 'GET',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const result = await response.json()
        if (result.data) {
          setRoles(result.data)
        }
      }
    } catch (error: any) {
      console.error('加载角色列表失败:', error)
    }
  }

  // 加载用户的所有角色
  const loadUserRoles = async (userId: string) => {
    try {
      // 获取所有角色，然后检查每个角色是否属于该用户
      const userRolesList: Role[] = []
      for (const role of roles) {
        const response = await fetch(getApiUrl(`/roles/${role.id}/users`), {
          method: 'GET',
          headers: getAuthHeaders()
        })
        if (response.ok) {
          const userRoles = await response.json()
          const hasRole = userRoles.some((ur: any) => ur.user_id === userId)
          if (hasRole) {
            userRolesList.push(role)
          }
        }
      }
      setUserRoles(prev => ({ ...prev, [userId]: userRolesList }))
      return userRolesList
    } catch (error: any) {
      console.error('加载用户角色失败:', error)
      return []
    }
  }

  // 加载单个用户的所有角色（用于打开对话框时）
  const loadUserRolesForModal = async (userId: string) => {
    try {
      const userRolesList: Role[] = []
      for (const role of roles) {
        const response = await fetch(getApiUrl(`/roles/${role.id}/users`), {
          method: 'GET',
          headers: getAuthHeaders()
        })
        if (response.ok) {
          const userRoles = await response.json()
          const hasRole = userRoles.some((ur: any) => ur.user_id === userId)
          if (hasRole) {
            userRolesList.push(role)
          }
        }
      }
      return userRolesList
    } catch (error: any) {
      console.error('加载用户角色失败:', error)
      return []
    }
  }

  useEffect(() => {
    loadUsers()
    loadCompanies()
    loadRoles()
  }, [])

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (companyDropdownRef.current && !companyDropdownRef.current.contains(event.target as Node)) {
        setIsCompanyDropdownOpen(false)
      }
    }

    if (isCompanyDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isCompanyDropdownOpen])

  // 当用户列表或角色列表变化时，加载所有用户的角色
  useEffect(() => {
    if (users.length > 0 && roles.length > 0) {
      users.forEach(user => {
        loadUserRoles(user.id)
      })
    }
  }, [users, roles])

  // 搜索过滤
  const filteredUsers = users.filter(user =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (user.full_name && user.full_name.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // 打开新增/编辑对话框
  const handleOpenModal = async (user?: User) => {
    // 确保公司列表已加载
    if (companies.length === 0) {
      await loadCompanies()
    }
    
    if (user) {
      setEditingUser(user)
      // 优先使用新的多公司字段，如果没有则使用旧的company_id
      const companyIds = user.company_ids || (user.company_id ? [user.company_id] : [])
      const primaryCompanyId = user.primary_company_id || user.company_id || ""
      
      setFormData({
        email: user.email,
        full_name: user.full_name || "",
        is_active: user.is_active,
        is_superuser: user.is_superuser,
        password: "",
        company_ids: companyIds,
        primary_company_id: primaryCompanyId
      })
    } else {
      setEditingUser(null)
      setFormData({
        email: "",
        full_name: "",
        is_active: true,
        is_superuser: false,
        password: "",
        company_ids: [],
        primary_company_id: ""
      })
    }
    setIsOpen(true)
  }

  // 打开重置密码对话框
  const handleOpenResetPassword = (userId: string) => {
    setResetPasswordUserId(userId)
    setNewPassword("")
    setIsResetPasswordOpen(true)
  }

  // 打开管理角色对话框
  const handleOpenRoleModal = async (userId: string) => {
    setSelectedUserId(userId)
    // 加载用户当前的角色
    const currentRoles = await loadUserRolesForModal(userId)
    setSelectedRoleIds(currentRoles.map(r => r.id))
    setIsRoleOpen(true)
  }

  // 保存用户角色
  const handleSaveRoles = async () => {
    if (!selectedUserId) return

    try {
      // 获取用户当前的角色
      const currentRoles = userRoles[selectedUserId] || []
      const currentRoleIds = currentRoles.map(r => r.id)

      // 找出需要添加和删除的角色
      const toAdd = selectedRoleIds.filter(id => !currentRoleIds.includes(id))
      const toRemove = currentRoleIds.filter(id => !selectedRoleIds.includes(id))

      // 添加新角色
      for (const roleId of toAdd) {
        const response = await fetch(getApiUrl(`/roles/${roleId}/users/${selectedUserId}`), {
          method: 'POST',
          headers: getAuthHeaders()
        })
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || '分配角色失败')
        }
      }

      // 删除旧角色
      for (const roleId of toRemove) {
        const response = await fetch(getApiUrl(`/roles/${roleId}/users/${selectedUserId}`), {
          method: 'DELETE',
          headers: getAuthHeaders()
        })
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || '移除角色失败')
        }
      }

      showSuccessToast('角色保存成功')
      setIsRoleOpen(false)
      // 重新加载用户角色
      await loadUserRoles(selectedUserId)
      // 重新加载用户列表以刷新显示
      await loadUsers()
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  // 重置密码
  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 8) {
      showErrorToast('密码长度至少8个字符')
      return
    }

    try {
      const response = await fetch(getApiUrl(`/users/${resetPasswordUserId}/reset-password`), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ new_password: newPassword })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '重置密码失败')
      }

      showSuccessToast('密码重置成功')
      setIsResetPasswordOpen(false)
      setNewPassword("")
    } catch (error: any) {
      showErrorToast(error.message || '重置密码失败')
    }
  }

  // 保存用户
  const handleSave = async () => {
    try {
      const url = editingUser 
        ? getApiUrl(`/users/${editingUser.id}`)
        : getApiUrl('/users/')
      
      const method = editingUser ? 'PATCH' : 'POST'
      
      // 去重 company_ids，确保没有重复值
      const uniqueCompanyIds = formData.company_ids.length > 0 
        ? [...new Set(formData.company_ids)]  // 使用 Set 去重
        : null
      
      const body: any = {
        email: formData.email,
        full_name: formData.full_name || null,
        is_active: formData.is_active,
        is_superuser: formData.is_superuser,
        company_ids: uniqueCompanyIds,
        primary_company_id: formData.primary_company_id || null
      }

      if (formData.password) {
        body.password = formData.password
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

      showSuccessToast(editingUser ? '用户更新成功' : '用户创建成功')
      setIsOpen(false)
      // 同时刷新用户列表和公司列表
      await Promise.all([loadUsers(), loadCompanies()])
    } catch (error: any) {
      showErrorToast(error.message || '保存失败')
    }
  }

  // 删除用户
  const handleDelete = async (userId: string) => {
    if (!confirm('确定要删除该用户吗？')) {
      return
    }

    try {
      const response = await fetch(getApiUrl(`/users/${userId}`), {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('删除失败')
      }

      showSuccessToast('用户删除成功')
      loadUsers()
    } catch (error: any) {
      showErrorToast(error.message || '删除失败')
    }
  }

  return (
    <Box p={4} h="100%" overflow="auto">
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">用户信息管理</Text>
        <Flex gap={2}>
          <Button
            leftIcon={<FiPlus />}
            colorScheme="blue"
            onClick={() => handleOpenModal()}
          >
            新增用户
          </Button>
          <Button
            leftIcon={<FiRefreshCw />}
            onClick={async () => {
              await Promise.all([loadUsers(), loadCompanies(), loadRoles()])
            }}
            isLoading={isLoading}
          >
            刷新
          </Button>
        </Flex>
      </Flex>

      {/* 搜索框 */}
      <Box mb={4}>
        <Flex>
          <Input
            placeholder="搜索用户邮箱或姓名..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            mr={2}
          />
          <Button
            leftIcon={<FiSearch />}
            colorScheme="green"
            onClick={loadUsers}
          >
            搜索
          </Button>
        </Flex>
      </Box>

      {/* 用户列表 */}
      <Box overflowX="auto">
        <Table.Root size={{ base: "sm", md: "md" }}>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>邮箱</Table.ColumnHeader>
              <Table.ColumnHeader>姓名</Table.ColumnHeader>
              <Table.ColumnHeader>公司</Table.ColumnHeader>
              <Table.ColumnHeader>公司代码</Table.ColumnHeader>
              <Table.ColumnHeader>角色</Table.ColumnHeader>
              <Table.ColumnHeader>是否激活</Table.ColumnHeader>
              <Table.ColumnHeader>是否超级用户</Table.ColumnHeader>
              <Table.ColumnHeader>操作</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredUsers.map((user) => {
              // 优先使用新的多公司字段，如果没有则使用旧的company_id
              const userCompanyIds = user.company_ids || (user.company_id ? [user.company_id] : [])
              const userCompanyList = userCompanyIds
                .map(id => companies.find(c => c.id === id))
                .filter(Boolean) as Company[]
              const primaryCompanyId = user.primary_company_id || user.company_id
              const primaryCompany = companies.find(c => c.id === primaryCompanyId)
              const userRoleList = userRoles[user.id] || []
              return (
                <Table.Row key={user.id}>
                  <Table.Cell>{user.email}</Table.Cell>
                  <Table.Cell>{user.full_name || '-'}</Table.Cell>
                  <Table.Cell>
                    {userCompanyList.length > 0 ? (
                      <HStack gap={1} flexWrap="wrap">
                        {userCompanyList.map(company => (
                          <Badge 
                            key={company.id} 
                            colorScheme={company.id === primaryCompanyId ? "blue" : "gray"}
                          >
                            {company.name}
                            {company.id === primaryCompanyId && " (主)"}
                          </Badge>
                        ))}
                      </HStack>
                    ) : '-'}
                  </Table.Cell>
                  <Table.Cell>
                    {userCompanyList.length > 0 ? (
                      <HStack gap={1} flexWrap="wrap">
                        {userCompanyList.map(company => (
                          <Badge 
                            key={company.id} 
                            colorScheme={company.id === primaryCompanyId ? "blue" : "gray"}
                          >
                            {company.code}
                            {company.id === primaryCompanyId && " (主)"}
                          </Badge>
                        ))}
                      </HStack>
                    ) : '-'}
                  </Table.Cell>
                  <Table.Cell>
                    {userRoleList.length > 0 ? (
                      <HStack gap={1} flexWrap="wrap">
                        {userRoleList.map(role => (
                          <Badge key={role.id} colorScheme="blue">{role.name}</Badge>
                        ))}
                      </HStack>
                    ) : (
                      '-'
                    )}
                  </Table.Cell>
                  <Table.Cell>{user.is_active ? '是' : '否'}</Table.Cell>
                  <Table.Cell>{user.is_superuser ? '是' : '否'}</Table.Cell>
                  <Table.Cell>
                    <Flex gap={2} flexWrap="wrap">
                      <Button
                        leftIcon={<FiEdit />}
                        size="sm"
                        onClick={() => handleOpenModal(user)}
                      >
                        编辑
                      </Button>
                      <Button
                        leftIcon={<FiShield />}
                        size="sm"
                        colorScheme="purple"
                        onClick={() => handleOpenRoleModal(user.id)}
                      >
                        管理角色
                      </Button>
                      <Button
                        leftIcon={<FiRefreshCw />}
                        size="sm"
                        colorScheme="blue"
                        onClick={() => handleOpenResetPassword(user.id)}
                      >
                        重置密码
                      </Button>
                      <Button
                        leftIcon={<FiTrash2 />}
                        size="sm"
                        colorScheme="red"
                        onClick={() => handleDelete(user.id)}
                      >
                        删除
                      </Button>
                    </Flex>
                  </Table.Cell>
                </Table.Row>
              )
            })}
          </Table.Body>
        </Table.Root>
      </Box>

      {/* 新增/编辑对话框 */}
      <DialogRoot open={isOpen} onOpenChange={({ open }) => setIsOpen(open)}>
        <DialogContent>
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>{editingUser ? '编辑用户' : '新增用户'}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Box>
              <Field mb={4} label="邮箱" required>
                <Input
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  type="email"
                />
              </Field>

              <Field mb={4} label="姓名">
                <Input
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                />
              </Field>

              {!editingUser && (
                <Field mb={4} label="密码" required>
                  <Input
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    type="password"
                  />
                </Field>
              )}

              <Field mb={4} label="是否激活">
                <Switch
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                />
              </Field>

              <Field mb={4} label="是否超级用户">
                <Switch
                  checked={formData.is_superuser}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_superuser: checked })}
                />
              </Field>

              <Field mb={4} label="关联公司（可多选）">
                {companies.length === 0 ? (
                  <Text fontSize="sm" color="gray.500">正在加载公司列表...</Text>
                ) : (
                  <Box position="relative" ref={companyDropdownRef}>
                    {/* 多选下拉框按钮 */}
                    <Button
                      w="100%"
                      justifyContent="space-between"
                      onClick={() => setIsCompanyDropdownOpen(!isCompanyDropdownOpen)}
                      rightIcon={<FiChevronDown />}
                      variant="outline"
                    >
                      {formData.company_ids.length === 0 
                        ? "请选择公司" 
                        : `${formData.company_ids.length} 个公司已选择`}
                    </Button>
                    
                    {/* 下拉选项列表 */}
                    {isCompanyDropdownOpen && (
                      <Box
                        position="absolute"
                        top="100%"
                        left={0}
                        right={0}
                        mt={1}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        boxShadow="lg"
                        zIndex={1000}
                        maxH="300px"
                        overflowY="auto"
                      >
                      {companies.map(company => {
                        const isSelected = formData.company_ids.includes(company.id)
                        const isPrimary = formData.primary_company_id === company.id
                        return (
                          <Box
                            key={company.id}
                            p={3}
                            cursor="pointer"
                            bg={isSelected ? "blue.50" : "white"}
                            _hover={{ bg: "gray.50" }}
                            borderBottom="1px solid"
                            borderColor="gray.200"
                            onClick={(e) => {
                              e.stopPropagation()
                              if (isSelected) {
                                // 移除公司
                                const newCompanyIds = formData.company_ids.filter(id => id !== company.id)
                                let newPrimaryId = formData.primary_company_id
                                if (company.id === formData.primary_company_id) {
                                  newPrimaryId = newCompanyIds.length > 0 ? newCompanyIds[0] : ""
                                }
                                setFormData({
                                  ...formData,
                                  company_ids: newCompanyIds,
                                  primary_company_id: newPrimaryId
                                })
                              } else {
                                // 添加公司
                                const newCompanyIds = [...formData.company_ids, company.id]
                                const newPrimaryId = formData.company_ids.length === 0 
                                  ? company.id 
                                  : formData.primary_company_id
                                setFormData({
                                  ...formData,
                                  company_ids: newCompanyIds,
                                  primary_company_id: newPrimaryId
                                })
                              }
                            }}
                          >
                            <Flex align="center" justify="space-between">
                              <Flex align="center" gap={2}>
                                <Box
                                  w={4}
                                  h={4}
                                  border="2px solid"
                                  borderColor={isSelected ? "blue.500" : "gray.300"}
                                  bg={isSelected ? "blue.500" : "white"}
                                  borderRadius="sm"
                                  display="flex"
                                  alignItems="center"
                                  justifyContent="center"
                                >
                                  {isSelected && (
                                    <Text color="white" fontSize="xs">✓</Text>
                                  )}
                                </Box>
                                <Text fontSize="sm">
                                  {company.name} ({company.code})
                                </Text>
                              </Flex>
                              {isSelected && (
                                <Button
                                  size="xs"
                                  colorScheme={isPrimary ? "blue" : "gray"}
                                  variant={isPrimary ? "solid" : "outline"}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setFormData({
                                      ...formData,
                                      primary_company_id: company.id
                                    })
                                  }}
                                >
                                  {isPrimary ? "主公司" : "设为主公司"}
                                </Button>
                              )}
                            </Flex>
                          </Box>
                        )
                      })}
                      </Box>
                    )}
                    
                    {/* 已选择的公司标签 */}
                    {formData.company_ids.length > 0 && (
                      <Flex wrap="wrap" gap={2} mt={2}>
                        {formData.company_ids.map(companyId => {
                          const company = companies.find(c => c.id === companyId)
                          if (!company) return null
                          const isPrimary = formData.primary_company_id === companyId
                          return (
                            <Badge
                              key={companyId}
                              colorScheme={isPrimary ? "blue" : "gray"}
                              p={2}
                              borderRadius="md"
                              display="flex"
                              alignItems="center"
                              gap={1}
                            >
                              <Text>{company.name} ({company.code})</Text>
                              {isPrimary && <Text fontSize="xs">(主)</Text>}
                              <IconButton
                                aria-label="移除"
                                icon={<FiX />}
                                size="xs"
                                variant="ghost"
                                onClick={() => {
                                  const newCompanyIds = formData.company_ids.filter(id => id !== companyId)
                                  let newPrimaryId = formData.primary_company_id
                                  if (companyId === formData.primary_company_id) {
                                    newPrimaryId = newCompanyIds.length > 0 ? newCompanyIds[0] : ""
                                  }
                                  setFormData({
                                    ...formData,
                                    company_ids: newCompanyIds,
                                    primary_company_id: newPrimaryId
                                  })
                                }}
                              />
                            </Badge>
                          )
                        })}
                      </Flex>
                    )}
                    
                    {/* 提示信息 */}
                    {formData.company_ids.length === 0 && (
                      <Text fontSize="sm" color="gray.500" mt={2}>请至少选择一个公司</Text>
                    )}
                    {formData.company_ids.length > 0 && !formData.primary_company_id && (
                      <Text fontSize="sm" color="orange.500" mt={2}>请选择一个主公司</Text>
                    )}
                  </Box>
                )}
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

      {/* 重置密码对话框 */}
      <DialogRoot open={isResetPasswordOpen} onOpenChange={({ open }) => setIsResetPasswordOpen(open)}>
        <DialogContent>
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>重置密码</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Field mb={4} label="新密码" required>
              <Input
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                type="password"
                placeholder="请输入新密码（至少8个字符）"
              />
            </Field>
            <Flex justify="flex-end" gap={2} mt={4}>
              <Button onClick={() => setIsResetPasswordOpen(false)}>取消</Button>
              <Button colorScheme="blue" onClick={handleResetPassword}>
                确认重置
              </Button>
            </Flex>
          </DialogBody>
        </DialogContent>
      </DialogRoot>

      {/* 管理角色对话框 */}
      <DialogRoot open={isRoleOpen} onOpenChange={({ open }) => setIsRoleOpen(open)}>
        <DialogContent>
          <DialogCloseTrigger />
          <DialogHeader>
            <DialogTitle>管理角色</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Box mb={4}>
              <Text fontSize="sm" color="gray.600" mb={2}>
                选择角色：
              </Text>
              <Box maxH="300px" overflowY="auto" border="1px" borderColor="gray.200" borderRadius="md" p={2}>
                {roles.map((role) => (
                  <Box key={role.id} mb={2}>
                    <Checkbox
                      checked={selectedRoleIds.includes(role.id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedRoleIds([...selectedRoleIds, role.id])
                        } else {
                          setSelectedRoleIds(selectedRoleIds.filter(id => id !== role.id))
                        }
                      }}
                    >
                      <Box ml={2}>
                        <Text fontWeight="medium">{role.name}</Text>
                        {role.description && (
                          <Text fontSize="xs" color="gray.500">{role.description}</Text>
                        )}
                      </Box>
                    </Checkbox>
                  </Box>
                ))}
              </Box>
            </Box>
            <Flex justify="flex-end" gap={2} mt={4}>
              <Button onClick={() => setIsRoleOpen(false)}>取消</Button>
              <Button colorScheme="blue" onClick={handleSaveRoles}>
                保存
              </Button>
            </Flex>
          </DialogBody>
        </DialogContent>
      </DialogRoot>
    </Box>
  )
}

export default UserInfo

