import { Box, Text, Flex, Button, Grid, GridItem, Input, IconButton } from "@chakra-ui/react"
import { FiSearch, FiPlus, FiTrash2, FiDownload, FiUpload, FiChevronUp, FiChevronDown } from "react-icons/fi"
import { useState, useRef, useEffect, useMemo } from "react"
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'


// 注册AG-Grid模块
ModuleRegistry.registerModules([AllCommunityModule])

// 定义数据类型
interface SalesOrderData {
  salesOrderDocDId: string
  customerFullName: string
  docNo: string
  sequence: string
  docDate: string
  deliveryDate: string
  materialCode: string
  materialDescription: string
  qty: number
  nestingedQty: number
  unitId: string
  remark: string
  creator: string
  createDate: string
  modifierLast: string
  modifyDateLast: string
  approveStatus: string
  approver: string
  approveDate: string
  salesOrderDocDFeatureList: any[]
}

// 定义导入数据类型
interface SalesOrderDocDFeature {
  salesOrderDocDFeatureId: string | null
  salesOrderDocDId: string | null
  position: string
  featureId: string | null
  featureValue: string
  remark: string
  creator: string
  createDate: string | null
  modifierLast: string
  modifyDateLast: string | null
  approveStatus: string
  approver: string
  approveDate: string | null
}

interface SalesOrderDocD {
  salesOrderDocDId: string | null
  customerFullName: string
  docId: string | null
  docNo: string
  sequence: string | null
  docDate: string | null
  materialId: string | null
  materialCode: string
  materialDescription: string
  qty: number | null
  unitId: string
  deliveryDate: string | null
  nestingedQty: number | null
  creator: string
  createDate: string | null
  modifierLast: string
  modifyDateLast: string | null
  approveStatus: string
  approver: string
  approveDate: string | null
  remark: string
  salesOrderDocDFeatureList: SalesOrderDocDFeature[]
}
import useCustomToast from '@/hooks/useCustomToast'

const SalesOrderList = () => {
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [isImporting, setIsImporting] = useState(false)
  const [tableData, setTableData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)


  const [selectedRowData, setSelectedRowData] = useState<any>(null)
  const [showFeatureDetails, setShowFeatureDetails] = useState(false)

  // 查询条件相关状态
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  const [queryConditions, setQueryConditions] = useState({
    customerFullName: '',
    docNo: '',
    materialCode: '',
    materialDescription: '',
    deliveryDate: '',
    approveStatus: '',
    title: '',
    description: '',
    remark: '',
    materialRatio: '',
    wasteRatio: ''
  })

  const fileInputRef = useRef<HTMLInputElement>(null)

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()

  // 切换查询面板显示状态
  const toggleQueryPanel = () => {
    setIsQueryPanelOpen(!isQueryPanelOpen)
  }

  // 处理查询条件变化
  const handleQueryConditionChange = (field: string, value: string) => {
    setQueryConditions(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // 清空查询条件
  const clearQueryConditions = () => {
    setQueryConditions({
      customerFullName: '',
      docNo: '',
      materialCode: '',
      materialDescription: '',
      deliveryDate: '',
      approveStatus: '',
      title: '',
      description: '',
      remark: '',
      materialRatio: '',
      wasteRatio: ''
    })
  }

  // 搜索处理函数
  const handleSearch = () => {
    executeQuery()
  }

  // 执行查询
  const executeQuery = async () => {
    console.log("执行查询，条件:", queryConditions)
    setIsLoading(true)
    
    try {
      // 构建请求体
      const requestBody: any = {
        action: 'list',
        module: 'sales_order_doc_d',
        page: currentPage,
        limit: 500,
        timestamp: new Date().toISOString()
      }
      
      // 添加查询条件
      const filters: any = {}
      if (queryConditions.customerFullName) filters.customer_full_name = queryConditions.customerFullName
      if (queryConditions.docNo) filters.doc_no = queryConditions.docNo
      if (queryConditions.materialCode) filters.material_code = queryConditions.materialCode
      if (queryConditions.materialDescription) filters.material_description = queryConditions.materialDescription
      if (queryConditions.deliveryDate) filters.delivery_date = queryConditions.deliveryDate
      if (queryConditions.approveStatus) filters.approve_status = queryConditions.approveStatus
      
      if (Object.keys(filters).length > 0) {
        requestBody.filters = filters
      }
      
      console.log("查询请求体:", requestBody)
      
      const response = await fetch('/api/v1/salesOrderDocD/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          console.log("查询成功:", result.data)
          const transformedData = transformData(result.data || [])
          console.log("转换后的数据:", transformedData)
          setTableData(transformedData)
          const totalCount = result.pagination?.total || 0
          const queryType = Object.keys(filters).length > 0 ? '条件查询' : '全部数据'
          const message = `${queryType}成功，找到 ${totalCount} 条记录`
          showSuccessToast(message)
        } else {
          showErrorToast(`查询失败: ${result.message}`)
        }
      } else {
        showErrorToast(`查询失败: ${response.status}`)
      }
    } catch (error) {
      console.error('查询失败:', error)
      showErrorToast(`查询失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 格式化日期函数 - 只显示日期部分
  const formatDate = (dateString: string | null) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      return date.toISOString().split('T')[0] // 只返回 YYYY-MM-DD 格式
    } catch (error) {
      return dateString
    }
  }

  // 格式化数值函数 - 自定义小数点位数
  const formatNumber = (value: number | null, decimals: number = 2) => {
    if (value === null || value === undefined) return ''
    return Number(value).toFixed(decimals)
  }

  // 数据转换函数 - 将后端返回的数据转换为前端格式，子对象数据横置转换
  const transformData = (data: any[]): any[] => {
    const result: any[] = []
    
    // 收集所有唯一的 featureDesc 作为动态列
    const allFeatureDescs = new Set<string>()
    data.forEach(item => {
      if (item.salesOrderDocDFeatureList && item.salesOrderDocDFeatureList.length > 0) {
        item.salesOrderDocDFeatureList.forEach((feature: any) => {
          if (feature.featureDesc) {
            allFeatureDescs.add(feature.featureDesc)
          }
        })
      }
    })
    
    // 将 Set 转换为数组并排序
    const featureDescs = Array.from(allFeatureDescs).sort()
    console.log('动态属性列:', featureDescs)
    
    data.forEach(item => {
      // 主记录
      const mainRecord: any = {
        salesOrderDocDId: item.salesOrderDocDId,
        customerFullName: item.customerFullName,
        docNo: item.docNo,
        sequence: item.sequence,
        docDate: item.docDate,
        materialCode: item.materialCode,
        materialDescription: item.materialDescription,
        qty: item.qty,
        unitId: item.unitId,
        deliveryDate: item.deliveryDate,
        nestingedQty: item.nestingedQty,
        remark: item.remark,
        creator: item.creator,
        createDate: item.createDate,
        modifierLast: item.modifierLast,
        modifyDateLast: item.modifyDateLast,
        approveStatus: item.approveStatus,
        approver: item.approver,
        approveDate: item.approveDate,
        salesOrderDocDFeatureList: item.salesOrderDocDFeatureList || [],
      }
      
      // 添加动态属性列
      featureDescs.forEach(featureDesc => {
        // 查找对应的 featureValue
        const feature = item.salesOrderDocDFeatureList?.find((f: any) => f.featureDesc === featureDesc)
        mainRecord[featureDesc] = feature ? feature.featureValue : ''
      })
      
      result.push(mainRecord)
    })
    
    return result
  }

  // 高级格式化数值函数 - 支持千分位分隔符和小数点位数
  const formatNumberAdvanced = (value: number | null, decimals: number = 2, useThousandsSeparator: boolean = true) => {
    if (value === null || value === undefined) return ''
    
    const num = Number(value)
    const formatted = num.toFixed(decimals)
    
    if (useThousandsSeparator && decimals === 0) {
      // 整数时添加千分位分隔符
      return num.toLocaleString()
    } else if (useThousandsSeparator) {
      // 小数时添加千分位分隔符
      const parts = formatted.split('.')
      parts[0] = Number(parts[0]).toLocaleString()
      return parts.join('.')
    }
    
    return formatted
  }

  

  // 处理行点击，显示属性详情
  const handleRowClick = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.salesOrderDocDFeatureList && rowData.salesOrderDocDFeatureList.length > 0) {
      setSelectedRowData(rowData)
      setShowFeatureDetails(true)
      showInfoToast(`显示 ${rowData.customerFullName} - ${rowData.docNo} 的属性详情`)
    } else {
      showInfoToast('该订单没有属性数据')
    }
  }






  const handleAdd = () => {
    console.log("新增销售订单")
  }

  const handleDelete = () => {
    console.log("删除销售订单", selectedRows)
  }

  const handleExport = () => {
    console.log('导出按钮被点击')
    try {
      // 确定要导出的数据
      const dataToExport = selectedRows.length > 0 
        ? tableData.filter(item => selectedRows.includes(item.salesOrderDocDId))
        : tableData

      console.log('要导出的数据:', dataToExport)
      console.log('选中的行:', selectedRows)

      if (dataToExport.length === 0) {
        showErrorToast('没有数据可导出')
        return
      }

      // 创建工作簿
      console.log('开始生成Excel数据...')
      const workbook = XLSX.utils.book_new()
      
      // ===== 第一个Sheet: sales_order_doc_d =====
      const mainData = []
      
      // 第一行：字段名
      const mainFieldNames = [
        'sales_order_doc_d_id',
        'customer_full_name', 
        'doc_id',
        'doc_no',
        'sequence',
        'doc_date',
        'material_id',
        'material_code',
        'material_description',
        'qty',
        'unit_id',
        'delivery_date',
        'nestinged_qty',
        'creator',
        'create_date',
        'modifier_last',
        'modify_date_last',
        'approve_status',
        'approver',
        'approve_date',
        'remark'
      ]
      mainData.push(mainFieldNames)
      
      // 第二行：字段注释
      const mainFieldLabels = [
        '物理主键',
        '客户全名',
        '订单类型',
        '订单单号',
        '订单行号',
        '订单日期',
        '物料主键',
        '物料编码',
        '物料描述',
        '订单数量',
        '订单单位',
        '交期',
        '已套料数量',
        '创建人',
        '创建日期',
        '最后修改人',
        '最后修改日期',
        '审批状态',
        '审批人',
        '审批日期',
        '备注'
      ]
      mainData.push(mainFieldLabels)
      
      // 第三行开始：主表数据
      dataToExport.forEach(item => {
        const row = [
          item.salesOrderDocDId,
          item.customerFullName,
          item.docId,
          item.docNo,
          item.sequence,
          item.docDate,
          item.materialId,
          item.materialCode,
          item.materialDescription,
          item.qty,
          item.unitId,
          item.deliveryDate,
          item.nestingedQty,
          item.creator,
          item.createDate,
          item.modifierLast,
          item.modifyDateLast,
          item.approveStatus,
          item.approver,
          item.approveDate,
          item.remark
        ]
        mainData.push(row)
      })
      
      // 创建主表工作表
      const mainWorksheet = XLSX.utils.aoa_to_sheet(mainData)
      const mainColWidths = mainFieldNames.map(() => ({ width: 15 }))
      mainWorksheet['!cols'] = mainColWidths
      
      // 添加主表工作表到工作簿
      XLSX.utils.book_append_sheet(workbook, mainWorksheet, 'sales_order_doc_d')
      
      // ===== 第二个Sheet: sales_order_doc_d_feature =====
      const featureData = []
      
      // 第一行：字段名
      const featureFieldNames = [
        'sales_order_doc_d_feature_id',
        'sales_order_doc_d_id',
        'position',
        'feature_id',
        'feature_value',
        'remark',
        'creator',
        'create_date',
        'modifier_last',
        'modify_date_last',
        'approve_status',
        'approver',
        'approve_date'
      ]
      featureData.push(featureFieldNames)
      
      // 第二行：字段注释
      const featureFieldLabels = [
        '属性记录ID',
        '行项目ID',
        '位置',
        '属性ID',
        '属性值',
        '备注',
        '创建人',
        '创建日期',
        '最后修改人',
        '最后修改日期',
        '审批状态',
        '审批人',
        '审批日期'
      ]
      featureData.push(featureFieldLabels)
      
      // 第三行开始：属性表数据
      dataToExport.forEach(item => {
        // 获取该行的属性列表
        const features = item.salesOrderDocDFeatureList || []
        
        if (features.length === 0) {
          // 如果没有属性，添加一行空记录
          const emptyRow = [
            '', // sales_order_doc_d_feature_id
            item.salesOrderDocDId, // sales_order_doc_d_id
            '', // position
            '', // feature_id
            '', // feature_value
            '', // remark
            '', // creator
            '', // create_date
            '', // modifier_last
            '', // modify_date_last
            '', // approve_status
            '', // approver
            ''  // approve_date
          ]
          featureData.push(emptyRow)
        } else {
          // 如果有属性，为每个属性添加一行记录
          features.forEach((feature: any) => {
            const row = [
              feature.salesOrderDocDFeatureId || '',
              item.salesOrderDocDId, // 关联到主表ID
              feature.position || '',
              feature.featureId || '',
              feature.featureValue || '',
              feature.remark || '',
              feature.creator || '',
              feature.createDate || '',
              feature.modifierLast || '',
              feature.modifyDateLast || '',
              feature.approveStatus || '',
              feature.approver || '',
              feature.approveDate || ''
            ]
            featureData.push(row)
          })
        }
      })
      
      // 创建属性表工作表
      const featureWorksheet = XLSX.utils.aoa_to_sheet(featureData)
      const featureColWidths = featureFieldNames.map(() => ({ width: 15 }))
      featureWorksheet['!cols'] = featureColWidths
      
      // 添加属性表工作表到工作簿
      XLSX.utils.book_append_sheet(workbook, featureWorksheet, 'sales_order_doc_d_feature')
      
      // 生成文件名
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
      const fileName = `销售订单数据_${timestamp}.xlsx`
      
      // 导出文件
      const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
      const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      saveAs(blob, fileName)
      
      console.log(`成功导出 ${dataToExport.length} 条主表记录到 ${fileName}`)
      const message = `成功导出 ${dataToExport.length} 条主表记录`
      console.log("显示成功Toast:", message)
      showSuccessToast(message)
    } catch (error) {
      console.error('导出失败:', error)
      const message = '导出失败，请重试'
      console.log("显示错误Toast:", message)
      showErrorToast(message)
    }
  }

  const handleImport = () => {
    console.log("导入销售订单")
    // 触发文件选择对话框
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    console.log('开始导入文件:', file.name)
    showSuccessToast('开始导入文件...')

    try {
      // 读取Excel文件
      const arrayBuffer = await file.arrayBuffer()
      const workbook = XLSX.read(arrayBuffer, { type: 'array' })
      
      console.log('Excel工作表:', workbook.SheetNames)
      
      // 检查是否包含两个工作表
      if (!workbook.SheetNames.includes('sales_order_doc_d') || !workbook.SheetNames.includes('sales_order_doc_d_feature')) {
        throw new Error('Excel文件必须包含 sales_order_doc_d 和 sales_order_doc_d_feature 两个工作表')
      }

      // 读取主表数据
      const mainSheet = workbook.Sheets['sales_order_doc_d']
      const mainData = XLSX.utils.sheet_to_json(mainSheet, { header: 1 })
      console.log('主表数据行数:', mainData.length)

      // 读取属性表数据
      const featureSheet = workbook.Sheets['sales_order_doc_d_feature']
      const featureData = XLSX.utils.sheet_to_json(featureSheet, { header: 1 })
      console.log('属性表数据行数:', featureData.length)

      // 处理主表数据（跳过前两行：字段名和注释）
      const mainRecords: SalesOrderDocD[] = []
      for (let i = 2; i < mainData.length; i++) {
        const row = mainData[i] as any[]
        if (row.length === 0 || !row[0]) continue // 跳过空行

        const record: SalesOrderDocD = {
          salesOrderDocDId: row[0] || null,
          customerFullName: row[1] || '',
          docId: row[2] || null,
          docNo: row[3] || '',
          sequence: row[4] || null,
          docDate: row[5] || null,
          materialId: row[6] || null,
          materialCode: row[7] || '',
          materialDescription: row[8] || '',
          qty: row[9] || null,
          unitId: row[10] || '',
          deliveryDate: row[11] || null,
          nestingedQty: row[12] || null,
          creator: row[13] || '',
          createDate: row[14] || null,
          modifierLast: row[15] || '',
          modifyDateLast: row[16] || null,
          approveStatus: row[17] || '',
          approver: row[18] || '',
          approveDate: row[19] || null,
          remark: row[20] || '',
          salesOrderDocDFeatureList: [] // 初始化空的子对象列表
        }
        mainRecords.push(record)
      }

      // 处理属性表数据（跳过前两行：字段名和注释）
      const featureRecords: SalesOrderDocDFeature[] = []
      for (let i = 2; i < featureData.length; i++) {
        const row = featureData[i] as any[]
        if (row.length === 0 || !row[1]) continue // 跳过空行（必须有关联ID）

        const record: SalesOrderDocDFeature = {
          salesOrderDocDFeatureId: row[0] || null,
          salesOrderDocDId: row[1] || null,
          position: row[2] || '',
          featureId: row[3] || null,
          featureValue: row[4] || '',
          remark: row[5] || '',
          creator: row[6] || '',
          createDate: row[7] || null,
          modifierLast: row[8] || '',
          modifyDateLast: row[9] || null,
          approveStatus: row[10] || '',
          approver: row[11] || '',
          approveDate: row[12] || null
        }
        featureRecords.push(record)
      }

      console.log('处理后的主表记录数:', mainRecords.length)
      console.log('处理后的属性表记录数:', featureRecords.length)

      // 装配数据：将属性表数据关联到主表数据
      const assembledSalesOrderDocDList = mainRecords.map(mainRecord => {
        // 找到属于当前主记录的所有属性记录
        const relatedFeatures = featureRecords.filter(featureRecord => 
          featureRecord.salesOrderDocDId === mainRecord.salesOrderDocDId
        )
        
        // 将属性记录添加到主记录的子对象列表中
        return {
          ...mainRecord,
          salesOrderDocDFeatureList: relatedFeatures
        }
      })

      console.log('装配后的SalesOrderDocD列表:', assembledSalesOrderDocDList)

      // 调用API导入数据
      await importDataToDatabase(assembledSalesOrderDocDList)

      // 清空文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // 刷新数据
      loadInitialData()

    } catch (error) {
      console.error('导入失败:', error)
      showErrorToast(`导入失败: ${error instanceof Error ? error.message : '未知错误'}`)
      
      // 清空文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const importDataToDatabase = async (assembledSalesOrderDocDList: SalesOrderDocD[]) => {
    try {
      console.log('开始调用API导入数据...')
      
      // 检查访问令牌
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到访问令牌，请重新登录')
      }

      // 调用统一API进行批量导入
      const apiUrl = '/api/v1/salesOrderDocD/unified'
      console.log('API URL:', apiUrl)

      const requestBody = {
        action: 'batch_save',
        module: 'sales_order_doc_d',
        data: assembledSalesOrderDocDList,
        timestamp: new Date().toISOString()
      }

      console.log('请求体:', requestBody)

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      })

      console.log('响应状态:', response.status)

      // 检查响应状态
      if (!response.ok) {
        let errorMessage = `HTTP错误: ${response.status} ${response.statusText}`
        
        try {
          const errorText = await response.text()
          console.log('错误响应文本:', errorText)
          
          if (errorText) {
            try {
              const errorData = JSON.parse(errorText)
              errorMessage = errorData.message || errorData.detail || errorMessage
            } catch (parseError) {
              errorMessage = errorText || errorMessage
            }
          }
        } catch (textError) {
          console.error('读取错误响应失败:', textError)
        }
        
        throw new Error(errorMessage)
      }

      // 尝试解析响应
      const responseText = await response.text()
      console.log('响应文本:', responseText)
      
      if (!responseText) {
        throw new Error('服务器返回空响应')
      }
      
      let result
      try {
        result = JSON.parse(responseText)
      } catch (parseError) {
        console.error('JSON解析失败:', parseError)
        throw new Error(`响应格式错误: ${responseText}`)
      }
      
      console.log('解析后的响应:', result)
      
      if (!result.success) {
        throw new Error(result.message || '导入失败')
      }

      const totalFeatures = assembledSalesOrderDocDList.reduce((sum, item) => sum + item.salesOrderDocDFeatureList.length, 0)
      const message = `成功导入 ${assembledSalesOrderDocDList.length} 条主表记录和 ${totalFeatures} 条属性记录`
      console.log("显示成功Toast:", message)
      showSuccessToast(message)

      return result
    } catch (error) {
      console.error('API调用失败:', error)
      throw error
    }
  }

  // 动态生成列定义
  const generateColumnDefs = (data: any[]): ColDef[] => {
    // 收集所有唯一的 featureDesc 作为动态列
    const allFeatureDescs = new Set<string>()
    data.forEach(item => {
      if (item.salesOrderDocDFeatureList && item.salesOrderDocDFeatureList.length > 0) {
        item.salesOrderDocDFeatureList.forEach((feature: any) => {
          if (feature.featureDesc) {
            allFeatureDescs.add(feature.featureDesc)
          }
        })
      }
    })
    
    // 将 Set 转换为数组并排序
    const featureDescs = Array.from(allFeatureDescs).sort()
    
    // 基础列定义
    const baseColumns: ColDef[] = [
      // 复选框列
      {
        headerName: '',
        field: 'select',
        width: 30,
        pinned: 'left',
        checkboxSelection: true,
        headerCheckboxSelection: true
      },
      
      // 序号列
      {
        headerName: '序号',
        field: 'sequence',
        pinned: 'left',
        width: 60,
        valueGetter: (params) => {
          return String((params.node?.rowIndex || 0) + 1).padStart(4, '0')
        }
      },
      
      // 客户列
      {
        headerName: '客户',
        field: 'customerFullName',
        width: 80,
        pinned: 'left',
        filter: 'text'
      },
      
      // 订单单号列
      {
        headerName: '订单单号',
        field: 'docNo',
        width: 120,
        pinned: 'left',
        filter: 'text'
      },
      
      // 行号列
      {
        headerName: '行号',
        field: 'sequence',
        width: 60,
        pinned: 'left',
        filter: 'text'
      },
      
      // 订单日期列
      {
        headerName: '订单日期',
        field: 'docDate',
        pinned: 'left',
        filter: 'text',
        width: 110,
        valueFormatter: (params) => formatDate(params.value)
      },
      
      // 物料编码列
      {
        headerName: '物料编码',
        field: 'materialCode',
        width: 110,
        
      },
      
      // 物料描述列
      {
        headerName: '物料描述',
        field: 'materialDescription',
        width: 250,
        filter: 'text'
      },
      
      // 数量列
      {
        headerName: '数量',
        field: 'qty',
        filter: 'number',
        width: 100,
        valueFormatter: (params) => formatNumberAdvanced(params.value, 0, true)
      },
      
      // 交期列
      {
        headerName: '交期',
        field: 'deliveryDate',
        filter: 'text',
        width: 120,
        valueFormatter: (params) => formatDate(params.value)
      },
      
      // 套料数量列
      {
        headerName: '套料数量',
        field: 'nestingedQty',
        filter: 'number',
        width: 120,
        valueFormatter: (params) => formatNumber(params.value || 0, 1)
      }
    ]
    
    // 动态生成属性列
    const featureColumns: ColDef[] = featureDescs.map(featureDesc => ({
      headerName: featureDesc,
      field: featureDesc,
      width: 120,
      sortable: true,
      filter: true,
      resizable: true
    }))
    
    // 合并基础列和动态属性列
    return [...baseColumns, ...featureColumns]
  }

  // AG-Grid 列定义
  const columnDefs: ColDef[] = useMemo(() => {
    return generateColumnDefs(tableData)
  }, [tableData])

  // AG-Grid 事件处理
  const onGridReady = (params: GridReadyEvent) => {
    console.log("AG-Grid准备就绪")
  }

  const onSelectionChanged = () => {
    // 处理选择变更
    console.log("选择变更")
  }

  const onRowClicked = (params: any) => {
    handleRowClick(params.data)
  }

  // 加载初始数据函数
  const loadInitialData = async () => {
    setIsLoading(true)
    try {
      // 构建请求体
      const requestBody: any = {
        action: 'list',
        module: 'sales_order_doc_d',
        page: currentPage,
        limit: 500,
        timestamp: new Date().toISOString()
      }

      const response = await fetch('/api/v1/salesOrderDocD/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const result = await response.json()
        console.log('API response:', result)
        if (result.success) {
          console.log('Setting table data:', result.data)
          
          // 转换数据格式并更新表格数据
          const transformedData = transformData(result.data || [])
          console.log('转换后的数据:', transformedData)
          
          setTableData(transformedData)
          showSuccessToast('数据加载成功')
        } else {
          console.error('API returned error:', result.message)
          showErrorToast(`数据加载失败: ${result.message}`)
        }
      } else {
        console.error('HTTP error:', response.status, response.statusText)
        showErrorToast(`数据加载失败: ${response.status}`)
      }
    } catch (error) {
      console.error('加载初始数据失败:', error)
      showErrorToast(`数据加载失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 初始化加载数据
  useEffect(() => {
    loadInitialData()
  }, [currentPage])

  return (
    <Box p={0} h="100%" display="flex" flexDirection="column">
      
      {/* 隐藏的文件输入元素 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls"
        
        style={{ display: 'none' }}
        onChange={handleFileChange} // 添加 onChange 事件
      />
      
      {/* 工具栏 */}
      <Flex 
        bg="white" 
        p={2} 
        borderRadius="lg" 
        mt={0}
        mb={1}
        border="1px"
        borderColor="e2e8f0"
        justify="flex-start"
        align="center"
        gap={3}
        boxShadow="0 1px 3px rgba(0,0,0,0.1)"
        flexShrink={0}  // 防止工具栏被压缩
      >
        <Box position="relative">
          
          {/* 横线和箭头指示器 */}
          <Box
            position="absolute"
            bottom="-8px"
            left="50%"
            transform="translateX(-50%)"
            width="100%"
            display="flex"
            flexDirection="column"
            alignItems="center"
          >
            <Box
              width="100%"
              height="2px"
              bg="blue.400"
              borderRadius="1px"
            />
            <Box
              mt="-1px"
              width="0"
              height="0"
              borderLeft="6px solid transparent"
              borderRight="6px solid transparent"
              borderTop={isQueryPanelOpen ? "8px solid blue.400" : "none"}
              borderBottom={isQueryPanelOpen ? "none" : "8px solid blue.400"}
            />
          </Box>
        </Box>
        <Button
          colorScheme="green"
          variant="outline"
          size="sm"
          onClick={handleAdd}
          title="新增"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiPlus />
        </Button>
        <Button
          colorScheme="red"
          variant="outline"
          size="sm"
          onClick={handleDelete}
          title="删除"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiTrash2 />
        </Button>
        <Button
          colorScheme="purple"
          variant="outline"
          size="sm"
          onClick={handleExport}
          title="导出"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
        >
          <FiDownload />
        </Button>
        <Button
          colorScheme="orange"
          variant="outline"
          size="sm"
          onClick={handleImport}
          title="导入"
          minW="44px"
          height="32px"
          fontSize="13px"
          px={3}
          borderRadius="md"
          disabled={isImporting}
        >
          {isImporting ? "导入中..." : <FiUpload />}
        </Button>
      </Flex>

      {/* 2. 查询区域 */}
      <Box 
        bg="white" 
        p={1} 
        borderRadius="md" 
        mb={0}
        border="1px" 
        borderColor="gray.200"
        flexShrink={0}
      >
        {isQueryPanelOpen && (
          <Box p={1}>
          <Flex align="top" justify="space-between" gap={2}>
            <Grid templateColumns="repeat(3, 1fr)" gap={1}>
            <GridItem>
                  <Flex align="center" gap={2}>
                    <Text fontSize="sm" fontWeight="medium">客户全称</Text>
                    <Input
                      size="sm"
                      value={queryConditions.title}
                      onChange={(e) => handleQueryConditionChange('title', e.target.value)}
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                  <Flex align="center" gap={2}>
                    <Text fontSize="sm" fontWeight="medium">订单单号</Text>
                    <Input
                      size="sm"
                      value={queryConditions.title}
                      onChange={(e) => handleQueryConditionChange('title', e.target.value)}
                      flex="1"
                    />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">订单日期</Text>
                  <Input
                    size="sm"
                    value={queryConditions.description}
                    onChange={(e) => handleQueryConditionChange('description', e.target.value)}
                    placeholder="请输入描述"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              <GridItem>
                <Flex align="center" gap={2}>
                  <Text fontSize="sm" fontWeight="medium">交货日期</Text>
                  <Input
                    size="sm"
                    value={queryConditions.remark}
                    onChange={(e) => handleQueryConditionChange('remark', e.target.value)}
                    placeholder="请输入备注"
                    flex="1"
                  />
                </Flex>
              </GridItem>
              
            </Grid>
            <Button
              colorScheme="blue"
              variant="outline"
              size="sm"
              onClick={handleSearch}
              title="查询"
            
            >
              <FiSearch />
              
            </Button>
          </Flex>
          
        </Box>
        )}
        
        
        {/* 查询区域折叠按钮 */}
        <Flex 
          justify="center" 
          p={0} 
          borderTop="0px" 
          borderColor="gray"
          bg="gray.50"
        >
          
          <IconButton
            aria-label="切换"
            size="xs"
            variant="ghost"
            colorScheme="blue"
            onClick={toggleQueryPanel}
            ml={2}
          >
            {isQueryPanelOpen ? <FiChevronUp /> : <FiChevronDown />}
          </IconButton>
        </Flex>
      </Box>
      
      {/* 数据表格 */}
      <Box
        className="ag-theme-alpine"
        width="100%"
        flex="0.9"
        minH="0"
        overflow="hidden"
      >
        {isLoading && (
          <Box
            position="absolute"
            top="50%"
            left="50%"
            transform="translate(-50%, -50%)"
            zIndex={10}
            bg="white"
            p={4}
            borderRadius="md"
            boxShadow="lg"
          >
            <Flex align="center" gap={2}>
              <Box
                width="4"
                height="4"
                borderRadius="full"
                bg="blue.500"
                animation="pulse 1.5s infinite"
              />
              <Text fontSize="sm" color="gray.600">加载数据中...</Text>
            </Flex>
          </Box>
        )}
        <AgGridReact
          theme="legacy"
          columnDefs={columnDefs}
          rowData={tableData}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          onRowClicked={onRowClicked}
          rowSelection={{ mode: 'multiRow' }}
          pagination={true}
          paginationPageSize={10}
          paginationPageSizeSelector={[10, 50, 2000]}
          animateRows={true}
          
        />
      </Box>

     

    </Box>
  )
}

export default SalesOrderList 