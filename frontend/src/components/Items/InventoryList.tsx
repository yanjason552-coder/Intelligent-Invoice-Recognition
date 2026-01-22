import React, { useRef } from "react"
import { Box, Text, Flex, Button, HStack, Input, Grid, GridItem } from "@chakra-ui/react"
import { FiPlus, FiTrash2, FiChevronDown, FiChevronUp, FiFilter, FiRefreshCw, FiDownload, FiUpload } from "react-icons/fi"
import { useState, useEffect, useMemo } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridReadyEvent, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

// 注册AG-Grid模块 - 包含所有社区功能
ModuleRegistry.registerModules([AllCommunityModule])
import useCustomToast from '../../hooks/useCustomToast'
import { getApiUrl, getAuthHeaders } from '../../client/unifiedTypes'

const InventoryList = () => {
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [tableData, setTableData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalItems, setTotalItems] = useState(0)

  // 导入导出相关状态
  const [isImporting, setIsImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 查询条件相关状态
  const [isQueryPanelOpen, setIsQueryPanelOpen] = useState(true)
  const [queryConditions, setQueryConditions] = useState({
    materialCode: '',
    materialDesc: '',
    plantName: '',
    warehouseName: '',
    binName: '',
    lotNo: '',
    approveStatus: ''
  })

  const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()

  // 数据转换函数 - 将后端返回的数据转换为前端格式，子对象数据横置转换
  const transformData = (data: any[]): any[] => {
    const result: any[] = []
    
    // 收集所有唯一的 featureDesc 作为动态列
    const allFeatureDescs = new Set<string>()
    data.forEach(item => {
      if (item.materialLotFeatureList && item.materialLotFeatureList.length > 0) {
        item.materialLotFeatureList.forEach((feature: any) => {
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
        inventoryId: item.inventoryId,
        materialId: item.materialId,
        materialCode: item.materialCode,
        materialDesc: item.materialDesc,
        plantId: item.plantId,
        plantName: item.plantName,
        warehouseId: item.warehouseId,
        warehouseName: item.warehouseName,
        binId: item.binId,
        binName: item.binName,
        materialLotId: item.materialLotId,
        lotNo: item.lotNo,
        lotDesc: item.lotDesc,
        stockQty: item.stockQty,
        unitIdStock: item.unitIdStock,
        stockQtySecond: item.stockQtySecond,
        unitIdStockSec: item.unitIdStockSec,
        stockQtyLocked: item.stockQtyLocked,
        stockQtySecondLocked: item.stockQtySecondLocked,
        approveStatus: item.approveStatus,
        approver: item.approver,
        approveDate: item.approveDate,
        creator: item.creator,
        createDate: item.createDate,
        modifierLast: item.modifierLast,
        modifyDateLast: item.modifyDateLast,
        materialLotFeatureList: item.materialLotFeatureList || [],
      }
      
      // 添加动态属性列
      featureDescs.forEach(featureDesc => {
        // 查找对应的 featureValue
        const feature = item.materialLotFeatureList?.find((f: any) => f.featureDesc === featureDesc)
        mainRecord[featureDesc] = feature ? feature.featureValue : ''
      })
      
      result.push(mainRecord)
    })
    
    return result
  }

  // 动态生成列定义
  const generateColumnDefs = (data: any[]): ColDef[] => {
    // 收集所有唯一的 featureDesc 作为动态列
    const allFeatureDescs = new Set<string>()
    data.forEach(item => {
      if (item.materialLotFeatureList && item.materialLotFeatureList.length > 0) {
        item.materialLotFeatureList.forEach((feature: any) => {
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
      {
        headerName: '选择',
        field: 'select',
        width: 40,
        checkboxSelection: true,
        headerCheckboxSelection: true,
        sortable: false,
        filter: false,
        resizable: false
      },
      { 
        headerName: '行号', 
        field: 'seq', 
        width: 70,   
        valueGetter: (params) => {
          const rowIndex = params.node?.rowIndex || 0
          return String(rowIndex + 1).padStart(4, '0')
        }
      },
      { 
        headerName: '物料编码', 
        field: 'materialCode', 
        width: 120,
        sortable: true,
        filter: true
      },
      { 
        headerName: '物料描述', 
        field: 'materialDesc', 
        width: 150,
        sortable: true,
        filter: true
      },
      { 
        headerName: '仓库', 
        field: 'warehouseName', 
        width: 100,
        sortable: true,
        filter: true
      },
      { 
        headerName: '库位', 
        field: 'binName', 
        width: 100,
        sortable: true,
        filter: true
      },
      { 
        headerName: '批号', 
        field: 'lotNo', 
        width: 120,
        sortable: true,
        filter: true
      },
      { 
        headerName: '库存数量', 
        field: 'stockQty', 
        width: 100,
        sortable: true,
        filter: true
      },
      { 
        headerName: '已套数量', 
        field: 'stockQtyLocked', 
        width: 110,
        sortable: true,
        filter: true
      },
      { 
        headerName: '可用数量', 
        field: 'availableQty', 
        width: 110,
        sortable: true,
        filter: true,
        valueGetter: (params: any) => {
          const stockQty = params.data?.stockQty || 0
          const stockQtyLocked = params.data?.stockQtyLocked || 0
          return stockQty - stockQtyLocked
        },
        valueFormatter: (params: any) => {
          const value = params.value
          if (value === null || value === undefined) return ''
          return Number(value).toLocaleString()
        }
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

  // 执行查询
  const executeQuery = async () => {
    console.log("执行查询，条件:", queryConditions)
    setIsLoading(true)
    
    try {
      const response = await fetch(getApiUrl('/inventory/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'inventory',
          page: currentPage,
          limit: 2000,
          filters: {
            material_code: queryConditions.materialCode || undefined,
            material_desc: queryConditions.materialDesc || undefined,
            plant_name: queryConditions.plantName || undefined,
            warehouse_name: queryConditions.warehouseName || undefined,
            bin_name: queryConditions.binName || undefined,
            lot_no: queryConditions.lotNo || undefined,
            approve_status: queryConditions.approveStatus || undefined
          },
          timestamp: new Date().toISOString()
        })
      })

      // 检查响应状态
      if (!response.ok) {
        const errorText = await response.text()
        console.error('HTTP错误:', response.status, response.statusText, errorText)
        showErrorToast(`查询失败: ${response.status} ${response.statusText}`)
        return
      }

      // 尝试解析JSON
      let result
      try {
        result = await response.json()
      } catch (jsonError) {
        console.error('JSON解析失败:', jsonError)
        const responseText = await response.text()
        console.error('响应内容:', responseText)
        showErrorToast('服务器返回的数据格式错误')
        return
      }
      
      if (result.success) {
        console.log('查询返回的原始数据:', result.data)
        const transformedData = transformData(result.data || [])
        console.log('转换后的数据:', transformedData)
        setTableData(transformedData)
        setTotalItems(result.pagination?.total || 0)
        showSuccessToast(result.message || '查询成功')
      } else {
        showErrorToast(result.message || '查询失败')
      }
    } catch (error) {
      console.error('查询失败:', error)
      showErrorToast('查询失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  // 清空查询条件
  const clearQueryConditions = () => {
    setQueryConditions({
      materialCode: '',
      materialDesc: '',
      plantName: '',
      warehouseName: '',
      binName: '',
      lotNo: '',
      approveStatus: ''
    })
  }

  // 导出Excel
  const handleExport = () => {
    try {
      let exportData: any[] = []
      let fileName = ''
      
      if (tableData.length === 0) {
        // 导出空模板 - 包含3个工作表
        const inventoryTemplate = [{
          'inventoryId': '',
          'materialId': '',
          'materialCode': '',
          'materialDesc': '',
          'plantId': '',
          'plantName': '',
          'warehouseId': '',
          'warehouseName': '',
          'binId': '',
          'binName': '',
          'materialLotId': '',
          'lotNo': '',
          'lotDesc': '',
          'stockQty': '',
          'unitIdStock': '',
          'stockQtySecond': '',
          'unitIdStockSec': '',
          'stockQtyLocked': '',
          'stockQtySecondLocked': '',
          'approveStatus': '',
          'approver': '',
          'approveDate': '',
          'creator': '',
          'createDate': '',
          'modifierLast': '',
          'modifyDateLast': ''
        }]

        const materialLotTemplate = [{
          'materialLotId': '',
          'materialId': '',
          'materialCode': '',
          'materialDesc': '',
          'lotNo': '',
          'lotDesc': '',
          'manufactureDate': '',
          'remark': '',
          'creator': '',
          'createDate': '',
          'modifierLast': '',
          'modifyDateLast': '',
          'approveStatus': '',
          'approver': '',
          'approveDate': ''
        }]

        const materialLotFeatureTemplate = [{
          'materialLotFeatureId': '',
          'materialLotId': '',
          'featureId': '',
          'featureCode': '',
          'featureDesc': '',
          'featureValue': '',
          'remark': '',
          'creator': '',
          'createDate': '',
          'modifierLast': '',
          'modifyDateLast': '',
          'approveStatus': '',
          'approver': '',
          'approveDate': ''
        }]

        // 创建工作簿
        const wb = XLSX.utils.book_new()
        
        // 创建inventory工作表
        const wsInventory = XLSX.utils.json_to_sheet(inventoryTemplate)
        const inventoryColWidths = [
          { wch: 20 }, // inventory_id
          { wch: 15 }, // material_id
          { wch: 15 }, // material_code
          { wch: 20 }, // material_desc
          { wch: 15 }, // plant_id
          { wch: 12 }, // plant_name
          { wch: 15 }, // warehouse_id
          { wch: 12 }, // warehouse_name
          { wch: 15 }, // bin_id
          { wch: 12 }, // bin_name
          { wch: 15 }, // material_lot_id
          { wch: 15 }, // lotNo
          { wch: 20 }, // lotDesc
          { wch: 12 }, // stock_qty
          { wch: 15 }, // unit_id_stock
          { wch: 12 }, // stock_qty_second
          { wch: 15 }, // unit_id_stock_sec
          { wch: 12 }, // stock_qty_locked
          { wch: 12 }, // stock_qty_second_locked
          { wch: 10 }, // approve_status
          { wch: 12 }, // approver
          { wch: 15 }, // approve_date
          { wch: 12 }, // creator
          { wch: 15 }, // create_date
          { wch: 12 }, // modifier_last
          { wch: 15 }  // modify_date_last
        ]
        wsInventory['!cols'] = inventoryColWidths
        XLSX.utils.book_append_sheet(wb, wsInventory, 'inventory')

        // 创建material_lot工作表
        const wsMaterialLot = XLSX.utils.json_to_sheet(materialLotTemplate)
        const materialLotColWidths = [
          { wch: 20 }, // materialLotId
          { wch: 15 }, // materialId
          { wch: 15 }, // materialCode
          { wch: 20 }, // materialDesc
          { wch: 15 }, // lotNo
          { wch: 20 }, // lotDesc
          { wch: 15 }, // manufactureDate
          { wch: 20 }, // remark
          { wch: 12 }, // creator
          { wch: 15 }, // createDate
          { wch: 12 }, // modifierLast
          { wch: 15 }, // modifyDateLast
          { wch: 10 }, // approveStatus
          { wch: 12 }, // approver
          { wch: 15 }  // approveDate
        ]
        wsMaterialLot['!cols'] = materialLotColWidths
        XLSX.utils.book_append_sheet(wb, wsMaterialLot, 'material_lot')

        // 创建material_lot_feature工作表
        const wsMaterialLotFeature = XLSX.utils.json_to_sheet(materialLotFeatureTemplate)
        const materialLotFeatureColWidths = [
          { wch: 20 }, // materialLotFeatureId
          { wch: 15 }, // materialLotId
          { wch: 12 }, // featureId
          { wch: 15 }, // featureCode
          { wch: 20 }, // featureDesc
          { wch: 20 }, // featureValue
          { wch: 20 }, // remark
          { wch: 12 }, // creator
          { wch: 15 }, // createDate
          { wch: 12 }, // modifierLast
          { wch: 15 }, // modifyDateLast
          { wch: 10 }, // approveStatus
          { wch: 12 }, // approver
          { wch: 15 }  // approveDate
        ]
        wsMaterialLotFeature['!cols'] = materialLotFeatureColWidths
        XLSX.utils.book_append_sheet(wb, wsMaterialLotFeature, 'material_lot_feature')

        fileName = `库存明细模板_${new Date().toISOString().slice(0, 10)}.xlsx`
        XLSX.writeFile(wb, fileName)
        showInfoToast('导出空模板成功')
      } else {
        // 导出实际数据
        exportData = tableData.map(item => ({
          '物料ID': item.material_id || '',
          '物料编码': item.material_code || '',
          '物料描述': item.material_desc || '',
          '工厂名称': item.plant_name || '',
          '仓库名称': item.warehouse_name || '',
          '库位名称': item.bin_name || '',
          '批号编码': item.material_lot_code || '',
          '库存数量': item.stock_qty || 0,
          '已锁定数量': item.stock_qty_locked || 0,
          '批准状态': item.approve_status || '',
          '创建日期': item.create_date || ''
        }))
        fileName = `库存明细_${new Date().toISOString().slice(0, 10)}.xlsx`
        
        // 创建工作簿
        const wb = XLSX.utils.book_new()
        const ws = XLSX.utils.json_to_sheet(exportData)

        // 设置列宽
        const colWidths = [
          { wch: 12 }, // 物料ID
          { wch: 15 }, // 物料编码
          { wch: 20 }, // 物料描述
          { wch: 12 }, // 工厂名称
          { wch: 12 }, // 仓库名称
          { wch: 12 }, // 库位名称
          { wch: 15 }, // 批号编码
          { wch: 12 }, // 库存数量
          { wch: 12 }, // 已锁定数量
          { wch: 10 }, // 批准状态
          { wch: 15 }  // 创建日期
        ]
        ws['!cols'] = colWidths

        // 添加工作表到工作簿
        XLSX.utils.book_append_sheet(wb, ws, '库存明细')

        // 导出文件
        XLSX.writeFile(wb, fileName)
        showSuccessToast('导出成功')
      }
    } catch (error) {
      console.error('导出失败:', error)
      showErrorToast('导出失败')
    }
  }

  // 导入Excel
  const handleImport = () => {
    fileInputRef.current?.click()
  }

  // 处理文件上传
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 检查文件类型
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      showErrorToast('请选择Excel文件(.xlsx或.xls)')
      return
    }

    // 防重复提交检查
    if (isImporting) {
      showErrorToast('正在处理中，请勿重复提交')
      return
    }

    setIsImporting(true)
    try {
      const result = await readExcelFile(file)
      console.log('导入的数据:', result)
      
      if (result.success) {
        // 调用API保存数据到对应的数据表
        const saveResult = await saveDataToTables(result)
        
        const totalCount = (result.inventory?.length || 0) + 
                          (result.materialLot?.length || 0) + 
                          (result.materialLotFeature?.length || 0)
        showSuccessToast(`成功导入 ${totalCount} 条数据`)
        
        // 重新加载数据
        await loadInventoryData()
      } else {
        showErrorToast(result.message || '导入失败')
      }
    } catch (error: any) {
      console.error('导入失败:', error)
      showErrorToast(error.message || '导入失败')
    } finally {
      setIsImporting(false)
      // 清空文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // 组装数据，建立关联关系
  const assembleData = (result: {
    success: boolean
    message: string
    inventory: any[]
    materialLot: any[]
    materialLotFeature: any[]
  }) => {
    const assembledInventory: any[] = []
    
    // 处理inventory数据，为每个inventory组装对应的materialLot对象
    if (result.inventory && result.inventory.length > 0) {
      for (const inventoryItem of result.inventory) {
        // 查找对应的materialLot数据
        const materialLotItem = result.materialLot?.find(
          (lot: any) => lot.materialLotId === inventoryItem.materialLotId
        )
        
        // 查找对应的materialLotFeature数据
        const materialLotFeatures = result.materialLotFeature?.filter(
          (feature: any) => feature.materialLotId === inventoryItem.materialLotId
        ) || []
        
        // 组装materialLot对象，包含materialLotFeature子对象列表
        const assembledMaterialLot = materialLotItem ? {
          ...materialLotItem,
          materialLotFeatureList: materialLotFeatures
        } : null
        
        // 组装inventory对象，包含materialLot对象
        const assembledInventoryItem = {
          ...inventoryItem,
          materialLot: assembledMaterialLot
        }
        
        assembledInventory.push(assembledInventoryItem)
      }
    }
    
    return assembledInventory
  }

  // 保存数据到对应的数据表
  const saveDataToTables = async (result: {
    success: boolean
    message: string
    inventory: any[]
    materialLot: any[]
    materialLotFeature: any[]
  }) => {
    try {
      // 先组装数据，建立关联关系
      const assembledInventory = assembleData(result)
      
      // 一次性提交装配的对象列表
      if (assembledInventory && assembledInventory.length > 0) {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 300000) // 5分钟超时
        
        try {
          const response = await fetch(getApiUrl('/inventory/unified'), {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              action: 'batch_save',
              module: 'inventory',
              data: assembledInventory,
              timestamp: new Date().toISOString()
            }),
            signal: controller.signal
          })
          
          clearTimeout(timeoutId)
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
          }
          
          const result = await response.json()
          if (!result.success) {
            throw new Error(result.message || '保存失败')
          }
          
          return result
        } catch (error: any) {
          clearTimeout(timeoutId)
          if (error.name === 'AbortError') {
            throw new Error('请求超时，请稍后重试')
          }
          throw error
        }
      }
    } catch (error) {
      console.error('保存数据失败:', error)
      throw error
    }
  }

  // 读取Excel文件（多工作表版本）
  const readExcelFile = (file: File): Promise<{
    success: boolean
    message: string
    inventory: any[]
    materialLot: any[]
    materialLotFeature: any[]
  }> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer)
          const workbook = XLSX.read(data, { type: 'array' })
          
          const result = {
            success: true,
            message: '',
            inventory: [] as any[],
            materialLot: [] as any[],
            materialLotFeature: [] as any[]
          }
          
          // 处理inventory工作表
          if (workbook.SheetNames.includes('inventory')) {
            const worksheet = workbook.Sheets['inventory']
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
            
            if (jsonData.length > 1) { // 有标题行和数据行
              const headers = jsonData[0] as string[]
              const rows = jsonData.slice(1) as any[][]
              
              result.inventory = rows.map(row => {
                const item: any = {}
                headers.forEach((header, index) => {
                  if (row[index] !== undefined && row[index] !== '') {
                    item[header] = row[index]
                  }
                })
                return item
              }).filter(item => Object.keys(item).length > 0) // 过滤空行
            }
          }
          
          // 处理material_lot工作表
          if (workbook.SheetNames.includes('material_lot')) {
            const worksheet = workbook.Sheets['material_lot']
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
            
            if (jsonData.length > 1) { // 有标题行和数据行
              const headers = jsonData[0] as string[]
              const rows = jsonData.slice(1) as any[][]
              
              result.materialLot = rows.map(row => {
                const item: any = {}
                headers.forEach((header, index) => {
                  if (row[index] !== undefined && row[index] !== '') {
                    item[header] = row[index]
                  }
                })
                return item
              }).filter(item => Object.keys(item).length > 0) // 过滤空行
            }
          }
          
          // 处理material_lot_feature工作表
          if (workbook.SheetNames.includes('material_lot_feature')) {
            const worksheet = workbook.Sheets['material_lot_feature']
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
            
            if (jsonData.length > 1) { // 有标题行和数据行
              const headers = jsonData[0] as string[]
              const rows = jsonData.slice(1) as any[][]
              
              result.materialLotFeature = rows.map(row => {
                const item: any = {}
                headers.forEach((header, index) => {
                  if (row[index] !== undefined && row[index] !== '') {
                    item[header] = row[index]
                  }
                })
                return item
              }).filter(item => Object.keys(item).length > 0) // 过滤空行
            }
          }
          
          // 检查是否至少有一个工作表有数据
          if (result.inventory.length === 0 && result.materialLot.length === 0 && result.materialLotFeature.length === 0) {
            result.success = false
            result.message = 'Excel文件中没有找到有效数据'
          }
          
          resolve(result)
        } catch (error) {
          reject(error)
        }
      }
      reader.onerror = reject
      reader.readAsArrayBuffer(file)
    })
  }

  // 新增处理函数
  const handleAdd = () => {
    console.log("新增库存明细")
    // TODO: 实现新增逻辑
    showInfoToast("新增功能开发中...")
  }

  // 删除处理函数
  const handleDelete = async () => {
    if (selectedRows.length === 0) {
      showErrorToast("请先选择要删除的记录")
      return
    }
    
    if (!confirm(`确定要删除选中的 ${selectedRows.length} 条记录吗？`)) {
      return
    }
    
    setIsLoading(true)
    
    try {
      const deletePromises = selectedRows.map(async (inventoryId) => {
        const response = await fetch(getApiUrl('/inventory/unified'), {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            action: 'delete',
            module: 'inventory',
            data: { inventory_id: inventoryId },
            timestamp: new Date().toISOString()
          })
        })
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error('删除HTTP错误:', response.status, response.statusText, errorText)
          return { success: false, message: `删除失败: ${response.status} ${response.statusText}` }
        }
        
        try {
          return await response.json()
        } catch (jsonError) {
          console.error('删除JSON解析失败:', jsonError)
          return { success: false, message: '服务器返回的数据格式错误' }
        }
      })
      
      const results = await Promise.all(deletePromises)
      const successCount = results.filter(result => result.success).length
      
      if (successCount > 0) {
        showSuccessToast(`成功删除 ${successCount} 条记录`)
        setSelectedRows([])
        // 重新加载数据
        await loadInventoryData()
      } else {
        showErrorToast('删除失败')
      }
    } catch (error) {
      console.error('删除失败:', error)
      showErrorToast('删除失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }





  // AG-Grid列定义 - 使用动态生成的列定义
  const columnDefs: ColDef[] = useMemo(() => {
    return generateColumnDefs(tableData)
  }, [tableData])

  // 初始化数据
  useEffect(() => {
    loadInventoryData()
  }, [])

  // 加载inventory数据
  const loadInventoryData = async () => {
    setIsLoading(true)
    
    try {
      const response = await fetch(getApiUrl('/inventory/unified'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'list',
          module: 'inventory',
          page: currentPage,
          limit: 2000,
          timestamp: new Date().toISOString()
        })
      })

      const result = await response.json()
      
      if (result.success) {
        console.log('加载返回的原始数据:', result.data)
        const transformedData = transformData(result.data || [])
        console.log('转换后的数据:', transformedData)
        setTableData(transformedData)
        setTotalItems(result.pagination?.total || 0)
      } else {
        console.error('加载数据失败:', result.message)
        showErrorToast(result.message || '加载数据失败')
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      showErrorToast('加载数据失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  // AG-Grid事件处理
  const onGridReady = (params: GridReadyEvent) => {
    console.log("AG-Grid准备就绪")
  }

  const onSelectionChanged = (event: any) => {
    const selectedNodes = event.api.getSelectedNodes()
    const selectedIds = selectedNodes.map((node: any) => node.data.inventoryId)
    setSelectedRows(selectedIds)
  }

  // 行双击事件处理
  const onRowDoubleClicked = (event: any) => {
    const rowData = event.data
    if (rowData && rowData.inventoryId) {
      console.log("双击行数据:", rowData)
      
      // 触发自定义事件，通知父组件打开InventoryEdit TAB页
      const customEvent = new CustomEvent('openInventoryEditTab', {
        detail: {
          inventoryId: rowData.inventoryId,
          inventoryData: rowData
        }
      })
      window.dispatchEvent(customEvent)
    }
  }

  return (
    <Box p={0} h="100%" display="flex" flexDirection="column">
       
      {/* 工具栏 */}
      <Flex 
        bg="white" 
        p={2} 
        borderRadius="lg" 
        mt={0}
        mb={2}
        border="1px"
        borderColor="e2e8f0"
        justify="flex-start"
        align="center"
        gap={3}
        boxShadow="0 1px 3px rgba(0,0,0,0.1)"
        flexShrink={0}  // 防止工具栏被压缩
      >
        <Box position="relative">
          <Button
            colorScheme="blue"
            variant="outline"
            size="sm"
            onClick={toggleQueryPanel}
            title="查询条件"
            minW="44px"
            height="32px"
            fontSize="13px"
            px={3}
            borderRadius="md"
          >
            {isQueryPanelOpen ? <FiChevronUp /> : <FiChevronDown />}
          </Button>
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
          disabled={selectedRows.length === 0}
        >
          <FiTrash2 />
        </Button>
        <Button
          colorScheme="blue"
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
          colorScheme="green"
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
          <FiUpload />
        </Button>
        
      </Flex>

      {/* 查询条件区域 */}
      {isQueryPanelOpen && (
        <Box
          bg="gray.50"
          p={2}
          borderRadius="md"
          mb={1}
          border="1px"
          borderColor="gray.200"
        >
          <Flex justify="space-between" align="center" mb={3}>
            <Text fontWeight="bold" fontSize="sm">查询条件</Text>
            <HStack gap={2}>
            <Button
                colorScheme="blue"
                variant="outline"
                size="sm"
                onClick={executeQuery}
                title="查询"
                minW="44px"
                height="32px"
                fontSize="13px"
                px={3}
                borderRadius="md"
              >
                <FiFilter />
              </Button>
              <Button
                colorScheme="gray"
                variant="outline"
                size="sm"
                onClick={clearQueryConditions}
                title="重置"
                minW="44px"
                height="32px"
                fontSize="13px"
                px={3}
                borderRadius="md"
              >
                <FiRefreshCw />
              </Button>
            </HStack>
          </Flex>
          
          <Grid templateColumns="repeat(3, 1fr)" gap={1}>
            <GridItem>
              <Flex align="center" gap={2}>
                <Text fontSize="sm" fontWeight="medium" minW="80px">物料编码</Text>
                <Input
                  size="sm"
                  placeholder="请输入物料编码"
                  value={queryConditions.materialCode}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('materialCode', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>
            
            <GridItem>
              <Flex align="center">
                <Text fontSize="sm" fontWeight="medium" minW="80px">物料描述</Text>
                <Input
                  size="sm"
                  placeholder="请输入物料描述"
                  value={queryConditions.materialDesc}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('materialDesc', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>
                      
            <GridItem>
              <Flex align="center" >
                <Text fontSize="sm" fontWeight="medium" minW="80px">仓库名称</Text>
                <Input
                  size="sm"
                  placeholder="请输入仓库名称"
                  value={queryConditions.warehouseName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('warehouseName', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>
            
            <GridItem>
              <Flex align="center" >
                <Text fontSize="sm" fontWeight="medium" minW="80px">库位名称</Text>
                <Input
                  size="sm"
                  placeholder="请输入库位名称"
                  value={queryConditions.binName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('binName', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>
            
            <GridItem>
              <Flex align="center">
                <Text fontSize="sm" fontWeight="medium" minW="80px">批号编码</Text>
                <Input
                  size="sm"
                  placeholder="请输入批号编码"
                  value={queryConditions.lotNo}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleQueryConditionChange('lotNo', e.target.value)}
                  flex="1"
                />
              </Flex>
            </GridItem>           
            
          </Grid>
        </Box>
      )}



      {/* 数据表格 */}
      <Box
        className="ag-theme-alpine"
        width="100%"
        flex="0.90"
        minH="0"
        overflow="hidden"
      >
        <AgGridReact
          theme="legacy"
          columnDefs={columnDefs}
          rowData={tableData}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          onRowDoubleClicked={onRowDoubleClicked}
          rowSelection={{ mode: 'multiRow' }}
          pagination={true}
          paginationPageSize={pageSize}
          paginationPageSizeSelector={[10, 50, 2000]}
          suppressRowClickSelection={true}
          animateRows={true}
          // 默认列定义
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true
          }}
        />
      </Box>
      
      {/* 隐藏的文件输入元素 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFileUpload}
        style={{ display: 'none' }}
      />
    </Box>
  )
}

export default InventoryList 