import { Box, Text, Flex, VStack, Input } from "@chakra-ui/react"
import { FiSave } from "react-icons/fi"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from '@/hooks/useCustomToast'

const OCRConfig = () => {
  const [config, setConfig] = useState({
    provider: 'tesseract',
    language: 'chi_sim+eng',
    enablePreprocessing: true,
    enablePostprocessing: true,
    confidenceThreshold: 80,
    maxFileSize: 10,
    supportedFormats: ['pdf', 'jpg', 'png']
  })
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleSave = async () => {
    try {
      showSuccessToast('配置保存成功')
    } catch (error) {
      showErrorToast('保存失败')
    }
  }

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={6}>
        <Text fontSize="xl" fontWeight="bold">
          OCR配置
        </Text>
        <Button onClick={handleSave}>
          <FiSave style={{ marginRight: '8px' }} />
          保存配置
        </Button>
      </Flex>

      <VStack gap={6} align="stretch" maxW="800px">
        <Field label="OCR引擎">
          <Input
            value={config.provider}
            onChange={(e) => setConfig({ ...config, provider: e.target.value })}
            placeholder="例如: tesseract, paddleocr"
          />
        </Field>

        <Field label="识别语言">
          <Input
            value={config.language}
            onChange={(e) => setConfig({ ...config, language: e.target.value })}
            placeholder="例如: chi_sim+eng"
          />
        </Field>

        <Field label="置信度阈值 (%)">
          <Input
            type="number"
            value={config.confidenceThreshold}
            onChange={(e) => setConfig({ ...config, confidenceThreshold: parseInt(e.target.value) })}
            min={0}
            max={100}
          />
        </Field>

        <Field label="最大文件大小 (MB)">
          <Input
            type="number"
            value={config.maxFileSize}
            onChange={(e) => setConfig({ ...config, maxFileSize: parseInt(e.target.value) })}
            min={1}
            max={100}
          />
        </Field>
      </VStack>
    </Box>
  )
}

export default OCRConfig
