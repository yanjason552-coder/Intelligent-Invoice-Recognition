import { Box, Text, Flex, Badge, HStack } from "@chakra-ui/react"
import { FiRefreshCw, FiEye, FiDownload } from "react-icons/fi"
import { useState } from "react"
import { AgGridReact } from 'ag-grid-react'
import { ColDef, ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { Button } from "@/components/ui/button"
import useCustomToast from '@/hooks/useCustomToast'

ModuleRegistry.registerModules([AllCommunityModule])

interface RecognitionResult {
  id: string
  invoiceNo: string
  fileName: string
  templateName: string
  recognitionTime: string
  accuracy: number
  status: 'success' | 'failed' | 'partial'
  fieldsCount: number
  recognizedFields: number
}

const RecognitionResultList = () => {
  const [tableData, setTableData] = useState<RecognitionResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { showErrorToast } = useCustomToast()

  const fetchData = async () => {
    setIsLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      setTableData([])
    } catch (error) {
      showErrorToast('加载数据失败')
    } finally {
      setIsLoading(false)
    }
  }

  const columnDefs: ColDef[] = [
    { headerName: '票据编号', field: 'invoiceNo', width: 150 },
    { headerName: '文件名', field: 'fileName', width: 200 },
    { headerName: '模板名称', field: 'templateName', width: 150 },
    { headerName: '识别时间', field: 'recognitionTime', width: 180 },
    {
      headerName: '准确率',
      field: 'accuracy',
      width: 100,
      cellRenderer: (params: any) => `${params.value || 0}%`
    },
    {
      headerName: '状态',
      field: 'status',
      width: 100,
      cellRenderer: (params: any) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          success: { color: 'green', text: '成功' },
          failed: { color: 'red', text: '失败' },
          partial: { color: 'yellow', text: '部分' }
        }
        const info = statusMap[params.value] || { color: 'gray', text: '未知' }
        return <Badge colorScheme={info.color}>{info.text}</Badge>
      }
    },
    {
      headerName: '识别字段',
      field: 'recognizedFields',
      width: 120,
      cellRenderer: (params: any) => `${params.data?.recognizedFields || 0}/${params.data?.fieldsCount || 0}`
    },
    {
      headerName: '操作',
      width: 150,
      cellRenderer: (params: any) => (
        <HStack gap={2}>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => console.log('查看详情:', params.data.id)}
          >
            <FiEye />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => console.log('导出:', params.data.id)}
          >
            <FiDownload />
          </Button>
        </HStack>
      )
    }
  ]

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={4}>
        <Text fontSize="xl" fontWeight="bold">
          识别结果
        </Text>
        <Button onClick={fetchData} loading={isLoading}>
          <FiRefreshCw style={{ marginRight: '8px' }} />
          刷新
        </Button>
      </Flex>

      <Box className="ag-theme-alpine" style={{ height: '600px', width: '100%', overflow: 'hidden' }}>
        <AgGridReact
          theme="legacy"
          rowData={tableData}
          columnDefs={columnDefs}
          defaultColDef={{
            resizable: true,
            sortable: true,
            filter: true
          }}
          onGridReady={() => fetchData()}
        />
      </Box>
    </Box>
  )
}

export default RecognitionResultList
