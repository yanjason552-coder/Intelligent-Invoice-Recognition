import { Box, Flex, Icon, Text } from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { 
  FiChevronDown, 
  FiFile, 
  FiFolder, 
  FiSettings, 
  FiDatabase, 
  FiPackage, 
  FiBarChart2,
  FiUsers,
  FiShield,
  FiLink,
  FiTag,
  FiTrendingUp,
  FiPlus,
  FiUpload,
  FiEye,
  FiCheckCircle,
  FiFileText,
  FiSearch,
  FiDownload,
  FiCpu,
  FiSliders,
  FiZap,
  FiX
} from "react-icons/fi"
import { useState } from "react"

// 定义菜单项接口
interface MenuItem {
  title: string
  path: string
  action?: string
  children?: MenuItem[]
}

interface MenuGroup {
  title: string
  children: MenuItem[]
}

// 菜单数据结构 - 票据识别系统
const menu: MenuGroup[] = [
  {
    title: "系统设置",
    children: [
      { title: "公司信息", path: "/company-info", action: "open-tab" },
      { title: "用户信息", path: "/user-info", action: "open-tab" },
      { title: "角色信息", path: "/role-info", action: "open-tab" },
      { title: "维护权限", path: "/permission", action: "open-tab" },
    ],
  },
  {
    title: "票据管理",
    children: [
      { 
        title: "票据上传", 
        path: "/invoice-upload",
        children: [
          { title: "上传", path: "/invoice-upload-page", action: "open-tab" }
        ]
      },
      { 
        title: "票据识别", 
        path: "/invoice-recognition",
        children: [
          { title: "识别任务", path: "/invoice-recognition-list", action: "open-tab" }
        ]
      },
      { 
        title: "票据查询", 
        path: "/invoice-query",
        children: [
          { title: "查询", path: "/invoice-query-list", action: "open-tab" }
        ]
      },
      { 
        title: "票据审核", 
        path: "/invoice-review",
        children: [
          { title: "待审核", path: "/invoice-review-pending", action: "open-tab" },
          { title: "已审核", path: "/invoice-review-completed", action: "open-tab" },
          { title: "已拒绝", path: "/invoice-review-rejected", action: "open-tab" }
        ]
      },
    ],
  },
  {
    title: "系统配置",
    children: [
      { 
        title: "大模型配置", 
        path: "/llm-config",
        children: [
          { title: "配置管理", path: "/llm-config-page", action: "open-tab" },
          { title: "配置列表", path: "/llm-config-list-page", action: "open-tab" }
        ]
      },
      { 
        title: "单据模板配置", 
        path: "/template-config",
        children: [
          { title: "模板管理", path: "/template-config-list", action: "open-tab" }
        ]
      },
      { 
        title: "识别规则", 
        path: "/recognition-rules",
        children: [
          { title: "查询", path: "/recognition-rules-list", action: "open-tab" },
          { title: "编辑", path: "/recognition-rules-edit", action: "open-tab" }
        ]
      },
      { 
        title: "审核流程", 
        path: "/review-workflow",
        children: [
          { title: "配置", path: "/review-workflow-config", action: "open-tab" }
        ]
      },
    ],
  },
]

// 根据菜单项返回合适的图标
const getMenuIcon = (title: string) => {
  switch (title) {
    // 系统设置相关
    case "系统设置":
      return FiSettings
    case "用户信息":
      return FiUsers
    case "角色信息":
      return FiShield
    case "维护权限":
      return FiShield
    case "集成设置":
      return FiLink
    
    // 票据管理相关
    case "票据管理":
      return FiFileText
    case "票据上传":
      return FiUpload
    case "上传":
      return FiUpload
    case "票据识别":
      return FiEye
    case "识别任务":
      return FiFile
    case "批量识别":
      return FiPackage
    case "票据查询":
      return FiSearch
    case "查询":
      return FiSearch
    case "票据审核":
      return FiCheckCircle
    case "待审核":
      return FiFile
    case "已审核":
      return FiCheckCircle
    case "已拒绝":
      return FiX
    
    // 模板管理相关
    case "模板管理":
      return FiFile
    case "模板配置":
      return FiSliders
    case "编辑":
      return FiFile
    case "模板训练":
      return FiCpu
    case "训练任务":
      return FiFile
    case "新建训练":
      return FiPlus
    case "模板测试":
      return FiZap
    case "测试":
      return FiZap
    
    // 数据管理相关
    case "数据管理":
      return FiDatabase
    case "识别结果":
      return FiFileText
    case "详情":
      return FiEye
    case "数据导出":
      return FiDownload
    case "导出":
      return FiDownload
    case "数据统计":
      return FiBarChart2
    case "统计报表":
      return FiTrendingUp
    
    // 系统配置相关
    case "系统配置":
      return FiSettings
    case "大模型配置":
      return FiCpu
    case "单据模板配置":
      return FiFileText
    case "模板管理":
      return FiSliders
    case "配置":
      return FiSliders
    case "配置管理":
      return FiSliders
    case "配置列表":
      return FiFile
    case "识别规则":
      return FiTag
    case "审核流程":
      return FiLink
    
    // 默认
    default:
      return FiFolder
  }
}

const SidebarItems = () => {
  const navigate = useNavigate()
  // 控制一级分组展开/收起
  const [openGroups, setOpenGroups] = useState(() => menu.map(() => true))
  // 控制二级菜单展开/收起
  const [openSubMenus, setOpenSubMenus] = useState<{ [key: string]: boolean }>({})

  const toggleGroup = (idx: number) => {
    setOpenGroups((prev) => prev.map((v, i) => (i === idx ? !v : v)))
  }

  const toggleSubMenu = (itemTitle: string) => {
    setOpenSubMenus((prev) => ({
      ...prev,
      [itemTitle]: !prev[itemTitle]
    }))
  }

  // 处理菜单项点击
  const handleMenuItemClick = (item: MenuItem) => {
    if (item.action === "open-tab") {
      // 触发自定义事件，通知父组件打开TAB
      const event = new CustomEvent('openTab', {
        detail: {
          id: item.path.replace('/', ''),
          title: item.title,
          type: item.path.replace('/', ''),  // 移除前导斜杠
          data: undefined  // 列表页面不需要额外数据
        }
      })
      window.dispatchEvent(event)
      // 导航到首页
      navigate({ to: "/" })
    } else {
      // 普通路由导航
      navigate({ to: item.path as any })
    }
  }

  return (
    <>
      <Text fontSize="xs" px={4} py={2} fontWeight="bold">
        我的菜单
      </Text>
      <Box>
        {menu.map((group, idx) => (
          <Box key={group.title} mb={2}>
            <Flex
              align="center"
              px={2}
              py={1}
              cursor="pointer"
              onClick={() => toggleGroup(idx)}
              fontWeight="bold"
            >
              <Icon as={FiChevronDown} mr={1} transform={openGroups[idx] ? "rotate(0deg)" : "rotate(-90deg)"} transition="transform 0.2s" />
              <Icon as={getMenuIcon(group.title)} mr={1} />
              <Text>{group.title}</Text>
            </Flex>
            {openGroups[idx] && (
              <Box pl={6}>
                {group.children.map((item) => (
                  <Box key={item.title}>
                    {item.children && item.children.length > 0 ? (
                      // 有子菜单的项目
                      <Box>
                        <Flex
                          align="center"
                          px={2}
                          py={1}
                          _hover={{ bg: "gray.100" }}
                          cursor="pointer"
                          fontWeight="medium"
                          onClick={() => toggleSubMenu(item.title)}
                        >
                          <Icon 
                            as={FiChevronDown} 
                            mr={1} 
                            transform={openSubMenus[item.title] ? "rotate(0deg)" : "rotate(-90deg)"} 
                            transition="transform 0.2s" 
                          />
                          <Icon as={getMenuIcon(item.title)} mr={2} />
                          <Text>{item.title}</Text>
                        </Flex>
                        {openSubMenus[item.title] && (
                          <Box pl={4}>
                            {item.children.map((subItem: MenuItem) => (
                              <Flex 
                                key={subItem.title} 
                                align="center" 
                                px={2} 
                                py={1} 
                                _hover={{ bg: "gray.100" }}
                                cursor="pointer"
                                onClick={() => handleMenuItemClick(subItem)}
                              >
                                <Icon as={getMenuIcon(subItem.title)} mr={2} />
                                <Text fontSize="sm">{subItem.title}</Text>
                              </Flex>
                            ))}
                          </Box>
                        )}
                      </Box>
                    ) : (
                      // 没有子菜单的项目
                      <Flex 
                        align="center" 
                        px={2} 
                        py={1} 
                        _hover={{ bg: "gray.100" }}
                        cursor="pointer"
                        onClick={() => handleMenuItemClick(item)}
                      >
                        <Icon as={getMenuIcon(item.title)} mr={2} />
                        <Text>{item.title}</Text>
                      </Flex>
                    )}
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        ))}
      </Box>
    </>
  )
}

export default SidebarItems

