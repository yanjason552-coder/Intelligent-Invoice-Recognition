import { Box, Container, Text, Tabs, Flex } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import React, { useState, useEffect } from "react"
import { FiX } from "react-icons/fi"

import useAuth from "@/hooks/useAuth"
import SalesOrderEdit from "@/components/Items/SalesOrderEdit"
import SalesOrderList from "@/components/Items/SalesOrderList"
import FeatureList from "@/components/Items/FeatureList"
import FeatureEdit from "@/components/Items/FeatureEdit"
import MaterialClassEdit from "@/components/Items/MaterialClassEdit"
import MaterialList from "@/components/Items/MaterialList"
import MaterialEdit from "@/components/Items/MaterialEdit"
import SurfaceTechnologyList from "@/components/Items/SurfaceTechnologyList"
import SurfaceTechnologyEdit from "@/components/Items/SurfaceTechnologyEdit"
import InventoryList from "@/components/Items/InventoryList"
import InventoryEdit from "@/components/Items/InventoryEdit"
import DensityList from "@/components/Items/densityList"
import DensityEdit from "@/components/Items/densityEdit"
import OperationList from "@/components/Items/OperationList"
import OperationEdit from "@/components/Items/OperationEdit"
import NestingList from "@/components/Items/NestingList"
import NestingEdit from "@/components/Items/NestingEdit"
import NestingExe from "@/components/Items/NestingExe"
import ProductionOrderList from "@/components/Items/ProductionOrderList"
import ProductionOrderEdit from "@/components/Items/ProductionOrderEdit"
// 票据管理组件
import InvoiceUpload from "@/components/Invoice/InvoiceUpload"
import InvoiceRecognitionList from "@/components/Invoice/InvoiceRecognitionList"
import InvoiceQueryList from "@/components/Invoice/InvoiceQueryList"
import InvoiceReviewPending from "@/components/Invoice/InvoiceReviewPending"
// 数据管理组件
import RecognitionResultList from "@/components/Data/RecognitionResultList"
// 系统配置组件
import LLMConfig from "@/components/Config/LLMConfig"
import LLMConfigList from "@/components/Config/LLMConfigList"
import TemplateConfig from "@/components/Config/TemplateConfig"
import TemplateImport from "@/components/Config/TemplateImport"
import TemplateEdit from "@/components/Config/TemplateEdit"
// 系统设置组件
import UserInfo from "@/components/Settings/UserInfo"
import RoleInfo from "@/components/Settings/RoleInfo"
import Permission from "@/components/Settings/Permission"
import CompanyInfo from "@/components/Settings/CompanyInfo"
// 统计组件
import Statistics from "@/components/Dashboard/Statistics"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

// TAB页类型定义
interface TabItem {
  id: string
  title: string
  content: React.ReactNode
  closable?: boolean
}

function Dashboard() {
  const { user: currentUser } = useAuth()
  const [activeTab, setActiveTab] = useState("welcome")
  const [tabs, setTabs] = useState<TabItem[]>([
    {
      id: "welcome",
      title: "欢迎页面",
      content: (
        <Box pt={4}>
          <Statistics />
        </Box>
      ),
      closable: false
    }
  ])

  // 添加新TAB页
  const addTab = (newTab: TabItem) => {
    // 检查是否已存在相同的TAB
    const existingIndex = tabs.findIndex(tab => tab.id === newTab.id)
    if (existingIndex !== -1) {
      setActiveTab(newTab.id)
      return
    }
    
    setTabs(prev => [...prev, newTab])
    setActiveTab(newTab.id)
  }

  // 关闭TAB页
  const closeTab = (tabId: string) => {
    if (tabId === "welcome") return // 不允许关闭欢迎页面
    
    const newTabs = tabs.filter(tab => tab.id !== tabId)
    setTabs(newTabs)
    
    // 如果关闭的是当前激活的TAB，切换到前一个TAB
    if (tabId === activeTab) {
      const currentIndex = tabs.findIndex(tab => tab.id === tabId)
      const newActiveTab = tabs[Math.max(0, currentIndex - 1)]?.id || "welcome"
      setActiveTab(newActiveTab)
    }
  }

  // 监听菜单点击事件
  useEffect(() => {
    // 监听openTab事件
    const handleOpenTab = (event: CustomEvent) => {
      const { type, data } = event.detail || {}
      
      // 添加调试日志（data 对于列表页面是可选的）
      console.log('openTab事件触发:', { type, data: data ?? undefined, fullEvent: event.detail })
      
      if (type === "sales-order-list") {
        addTab({
          id: "sales-order-list",
          title: "销售订单-查询",
          content: <SalesOrderList />,
          closable: true
        })
      } else if (type === "sales-order-edit") {
        addTab({
          id: "sales-order-edit",
          title: "销售订单-编辑",
          content: <SalesOrderEdit />,
          closable: true
        })
      } else if (type === "feature-list") {
        addTab({
          id: "feature-list",
          title: "物料属性-查询",
          content: <FeatureList />,
          closable: true
        })
      } else if (type === "feature-edit") {
        addTab({
          id: "feature-edit",
          title: "物料属性-编辑",
          content: <FeatureEdit />,
          closable: true
        })
      } else if (type === "material-list") {
        addTab({
          id: "material-list",
          title: "物料信息-查询",
          content: <MaterialList />,
          closable: true
        })
      } else if (type === "material-edit") {
        addTab({
          id: "material-edit",
          title: "物料信息-编辑",
          content: <MaterialEdit />,
          closable: true
        })
      } else if (type === "material-class-edit") {
        addTab({
          id: "material-class-edit",
          title: "物料类别-编辑",
          content: <MaterialClassEdit />,
          closable: true
        })
      } else if (type === "surface-list") {
        addTab({
          id: "surface-list",
          title: "表面要求-查询",
          content: <SurfaceTechnologyList />,
          closable: true
        })
      } else if (type === "surface-edit") {
        addTab({
          id: "surface-edit",
          title: "表面要求-编辑",
          content: <SurfaceTechnologyEdit />,
          closable: true
        })
      } else if (type === "inventory-list") {
        addTab({
          id: "inventory-list",
          title: "库存明细-查询",
          content: <InventoryList />,
          closable: true
        })
      } else if (type === "inventory-edit") {
        addTab({
          id: "inventory-edit",
          title: "库存明细-编辑",
          content: <InventoryEdit />,
          closable: true
        })
      } else if (type === "density-list") {
        addTab({
          id: "density-list",
          title: "物料密度-查询",
          content: <DensityList />,
          closable: true
        })
      } else if (type === "density-edit") {
        addTab({
          id: "density-edit",
          title: "物料密度-编辑",
          content: <DensityEdit />,
          closable: true
        })
      } else if (type === "operation-list") {
        addTab({
          id: "operation-list",
          title: "制造工艺-查询",
          content: <OperationList />,
          closable: true
        })
      } else if (type === "operation-edit") {
        addTab({
          id: "operation-edit",
          title: "制造工艺-编辑",
          content: <OperationEdit />,
          closable: true
        })
      } else if (type === "nesting-list") {
        addTab({
          id: "nesting-list",
          title: "套料作业-查询",
          content: <NestingList />,
          closable: true
        })
      } else if (type === "nesting-edit") {
        addTab({
          id: "nesting-edit",
          title: "套料作业-编辑",
          content: <NestingEdit />,
          closable: true
        })
      }
      else if (type === "nesting-exe") {
        addTab({
          id: "nesting-exe",
          title: "套料作业-执行",
          content: <NestingExe />,
          closable: true
        })
      }
      else if (type === "production-order-list") {
        addTab({
          id: "production-order-list",
          title: "生产订单-查询",
          content: <ProductionOrderList />,
          closable: true
        })
      }
      else if (type === "production-order-edit") {
        addTab({
          id: "production-order-edit",
          title: "生产订单-维护",
          content: <ProductionOrderEdit />,
          closable: true
        })
      }
      // 票据管理相关Tab
      else if (type === "invoice-upload-page") {
        addTab({
          id: "invoice-upload-page",
          title: "票据上传",
          content: <InvoiceUpload />,
          closable: true
        })
      }
      else if (type === "invoice-recognition-list") {
        addTab({
          id: "invoice-recognition-list",
          title: "票据识别-任务列表",
          content: <InvoiceRecognitionList />,
          closable: true
        })
      }
      else if (type === "invoice-batch-recognition") {
        addTab({
          id: "invoice-batch-recognition",
          title: "票据识别-批量识别",
          content: <InvoiceRecognitionList />,
          closable: true
        })
      }
      else if (type === "invoice-query-list") {
        addTab({
          id: "invoice-query-list",
          title: "票据查询",
          content: <InvoiceQueryList />,
          closable: true
        })
      }
      else if (type === "invoice-review-pending") {
        addTab({
          id: "invoice-review-pending",
          title: "票据审核-待审核",
          content: <InvoiceReviewPending />,
          closable: true
        })
      }
      else if (type === "invoice-review-completed") {
        addTab({
          id: "invoice-review-completed",
          title: "票据审核-已审核",
          content: <InvoiceQueryList reviewStatus="approved" title="已审核票据" />,
          closable: true
        })
      }
      else if (type === "invoice-review-rejected") {
        addTab({
          id: "invoice-review-rejected",
          title: "票据审核-已拒绝",
          content: <InvoiceQueryList reviewStatus="rejected" title="已拒绝票据" />,
          closable: true
        })
      }
      // 数据管理相关Tab
      else if (type === "recognition-result-list") {
        addTab({
          id: "recognition-result-list",
          title: "识别结果-查询",
          content: <RecognitionResultList />,
          closable: true
        })
      }
      else if (type === "recognition-result-detail") {
        addTab({
          id: "recognition-result-detail",
          title: "识别结果-详情",
          content: <RecognitionResultList />,
          closable: true
        })
      }
      else if (type === "data-export-page") {
        addTab({
          id: "data-export-page",
          title: "数据导出",
          content: <RecognitionResultList />,
          closable: true
        })
      }
      else if (type === "data-statistics-report") {
        addTab({
          id: "data-statistics-report",
          title: "数据统计-报表",
          content: <RecognitionResultList />,
          closable: true
        })
      }
      // 系统配置相关Tab
      else if (type === "llm-config-page") {
        addTab({
          id: "llm-config-page",
          title: "大模型配置管理",
          content: <LLMConfig />,
          closable: true
        })
      }
      else if (type === "llm-config-list-page") {
        addTab({
          id: "llm-config-list-page",
          title: "大模型配置列表",
          content: <LLMConfigList />,
          closable: true
        })
      }
      else if (type === "template-config-list") {
        addTab({
          id: "template-config-list",
          title: "单据模板配置",
          content: <TemplateConfig />,
          closable: true
        })
      }
      else if (type === "template-import") {
        addTab({
          id: "template-import",
          title: "导入模板",
          content: <TemplateImport />,
          closable: true
        })
      }
      else if (type === "template-edit") {
        const templateId = event.detail?.data?.templateId || event.detail?.templateId
        addTab({
          id: `template-edit-${templateId || 'new'}`,
          title: templateId ? "编辑模板" : "新建模板",
          content: <TemplateEdit templateId={templateId} />,
          closable: true
        })
      }
      else if (type === "ocr-config-page") {
        addTab({
          id: "ocr-config-page",
          title: "OCR配置",
          content: <LLMConfig />,
          closable: true
        })
      }
      else if (type === "recognition-rules-list") {
        addTab({
          id: "recognition-rules-list",
          title: "识别规则-查询",
          content: <OCRConfig />,
          closable: true
        })
      }
      else if (type === "recognition-rules-edit") {
        addTab({
          id: "recognition-rules-edit",
          title: "识别规则-编辑",
          content: <OCRConfig />,
          closable: true
        })
      }
      else if (type === "review-workflow-config") {
        addTab({
          id: "review-workflow-config",
          title: "审核流程-配置",
          content: <OCRConfig />,
          closable: true
        })
      }
      // 系统设置相关Tab
      else if (type === "company-info") {
        addTab({
          id: "company-info",
          title: "公司信息",
          content: <CompanyInfo />,
          closable: true
        })
      }
      else if (type === "user-info") {
        addTab({
          id: "user-info",
          title: "用户信息",
          content: <UserInfo />,
          closable: true
        })
      }
      else if (type === "role-info") {
        addTab({
          id: "role-info",
          title: "角色信息",
          content: <RoleInfo />,
          closable: true
        })
      }
      else if (type === "permission") {
        addTab({
          id: "permission",
          title: "维护权限",
          content: <Permission />,
          closable: true
        })
      }
    }

    // 监听closeTab事件（允许子页面通过 window.dispatchEvent 关闭当前tab）
    const handleCloseTab = (event: CustomEvent) => {
      const tabId = event.detail?.tabId || event.detail?.id
      if (!tabId || typeof tabId !== "string") return
      closeTab(tabId)
    }

    // 监听NestingEdit TAB页打开事件
    const handleOpenNestingEditTab = (event: CustomEvent) => {
      const { nestingLayoutId, nestingLayoutData } = event.detail
      const tabId = `nesting-edit-${nestingLayoutId || 'new'}`
      
      addTab({
        id: tabId,
        title: `套料作业-编辑(${nestingLayoutData?.nestingLayoutId || '新建'})`,
        content: <NestingEdit nestingLayoutId={nestingLayoutId} initialNestingLayoutData={nestingLayoutData} />,
        closable: true
      })
    }

    // 监听FeatureEdit TAB页打开事件
    const handleOpenFeatureEditTab = (event: CustomEvent) => {
      const { featureId, featureData } = event.detail
      const tabId = `feature-edit-${featureId}`
      
      addTab({
        id: tabId,
        title: `物料属性-编辑(${featureData.featureCode || featureId})`,
        content: <FeatureEdit featureId={featureId} featureData={featureData} />,
        closable: true
      })
    }

    // 监听MaterialEdit TAB页打开事件
    const handleOpenMaterialEditTab = (event: CustomEvent) => {
      const { materialId, materialData } = event.detail
      const tabId = `material-edit-${materialId}`
      
      addTab({
        id: tabId,
        title: `物料信息-编辑(${materialData.materialCode || materialId})`,
        content: <MaterialEdit materialId={materialId} materialData={materialData} />,
        closable: true
      })
    }

    // 监听SurfaceTechnologyEdit TAB页打开事件
    const handleOpenSurfaceTechnologyEditTab = (event: CustomEvent) => {
      const { surfaceTechnologyId, surfaceTechnologyData } = event.detail
      const tabId = `surface-edit-${surfaceTechnologyId}`
      
      addTab({
        id: tabId,
        title: `表面要求-编辑(${surfaceTechnologyData.surfaceCode || surfaceTechnologyId})`,
        content: <SurfaceTechnologyEdit surfaceTechnologyId={surfaceTechnologyId} surfaceTechnologyData={surfaceTechnologyData} />,
        closable: true
      })
    }

    // 监听DensityEdit TAB页打开事件
    const handleOpenDensityEditTab = (event: CustomEvent) => {
      const { materialDensityId, densityData } = event.detail
      const tabId = `density-edit-${materialDensityId}`
      
      addTab({
        id: tabId,
        title: `物料密度-编辑(${densityData.materialCode || materialDensityId})`,
        content: <DensityEdit materialDensityId={materialDensityId} densityData={densityData} />,
        closable: true
      })
    }

    // 监听OperationEdit TAB页打开事件
    const handleOpenOperationEditTab = (event: CustomEvent) => {
      const { operationId, operationData } = event.detail
      const tabId = `operation-edit-${operationId}`
      
      addTab({
        id: tabId,
        title: `制造工艺-编辑(${operationData.operationCode || operationId})`,
        content: <OperationEdit operationId={operationId} operationData={operationData} />,
        closable: true
      })
    }

    // 添加事件监听器
    window.addEventListener('openTab', handleOpenTab as EventListener)
    window.addEventListener('closeTab', handleCloseTab as EventListener)
    window.addEventListener('openFeatureEditTab', handleOpenFeatureEditTab as EventListener)
    window.addEventListener('openMaterialEditTab', handleOpenMaterialEditTab as EventListener)
    window.addEventListener('openSurfaceTechnologyEditTab', handleOpenSurfaceTechnologyEditTab as EventListener)
    window.addEventListener('openDensityEditTab', handleOpenDensityEditTab as EventListener)
    window.addEventListener('openOperationEditTab', handleOpenOperationEditTab as EventListener)
    window.addEventListener('openNestingEditTab', handleOpenNestingEditTab as EventListener)

    // 清理事件监听器
    return () => {
      window.removeEventListener('openTab', handleOpenTab as EventListener)
      window.removeEventListener('closeTab', handleCloseTab as EventListener)
      window.removeEventListener('openFeatureEditTab', handleOpenFeatureEditTab as EventListener)
      window.removeEventListener('openMaterialEditTab', handleOpenMaterialEditTab as EventListener)
      window.removeEventListener('openSurfaceTechnologyEditTab', handleOpenSurfaceTechnologyEditTab as EventListener)
      window.removeEventListener('openDensityEditTab', handleOpenDensityEditTab as EventListener)
      window.removeEventListener('openOperationEditTab', handleOpenOperationEditTab as EventListener)
      window.removeEventListener('openNestingEditTab', handleOpenNestingEditTab as EventListener)
    }
  }, [tabs.length]) // 依赖tabs.length以确保addTab函数是最新的

  return (
    <>
      <Container maxW="full" p={0}>
        <Box position="relative" h="100vh">
          {/* 内容区域 - 包含TAB页和内容 */}
          <Box 
            pt={0}  // 移除顶部间距，因为导航栏已经在父布局中处理
            h="100vh"
            overflowY="hidden"  // 禁用垂直滚动
            bg="white"
            display="flex"
            flexDirection="column"
          >
            {/* TAB页 - 在主内容区域内顶部对齐，左边对齐 */}
            <Box 
              position="relative"
              top={0}
              left={0}
              bg="white"
              borderBottom="1px"
              borderColor="gray.200"
              w="100%"
              flexShrink={0}  // 防止TAB页被压缩
            >
              <Tabs.Root value={activeTab} variant="enclosed">
                <Tabs.List 
                  borderBottom="none"
                  bg="gray.50"
                  minH="18px"
                  justifyContent="flex-start"  // 左边对齐
                  p={0}
                  m={0}
                >
                  {tabs.map((tab) => (
                    <Tabs.Trigger 
                      key={tab.id} 
                      value={tab.id} 
                      position="relative"
                      onClick={() => setActiveTab(tab.id)}
                      style={{
                        border: 'none',
                        background: 'transparent',
                        padding: '4px 8px',
                        marginRight: '0px',
                        borderTopLeftRadius: '2px',
                        borderTopRightRadius: '2px',
                        fontSize: '13px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        borderBottom: activeTab === tab.id ? '2px solid #3182ce' : '2px solid transparent'
                      }}
                    >
                      <Flex align="center">
                        <Text>{tab.title}</Text>
                        {tab.closable && (
                          <Box
                            as="span"
                            aria-label="关闭标签页"
                            ml={1}
                            onClick={(e) => {
                              e.stopPropagation()
                              closeTab(tab.id)
                            }}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              minWidth: '14px',
                              height: '12px',
                              padding: '0',
                              marginLeft: '4px',
                              cursor: 'pointer',
                              borderRadius: '4px',
                              transition: 'background-color 0.2s'
                            }}
                            _hover={{
                              backgroundColor: 'gray.200'
                            }}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault()
                                e.stopPropagation()
                                closeTab(tab.id)
                              }
                            }}
                          >
                            <FiX size={10} />
                          </Box>
                        )}
                      </Flex>
                    </Tabs.Trigger>
                  ))}
                </Tabs.List>
              </Tabs.Root>
            </Box>

            {/* 内容区域 */}
            <Box flex="1" overflow="auto">
              {tabs.map((tab) => (
                <Box 
                  key={tab.id} 
                  display={activeTab === tab.id ? 'block' : 'none'}
                  p={0}
                  h="100%"
                  overflowY="auto"
                  overflowX="hidden"
                >
                  {tab.content}
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Container>
    </>
  )
}
