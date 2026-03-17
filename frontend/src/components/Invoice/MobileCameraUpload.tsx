import { Box, Text, Flex, VStack, HStack, Button, IconButton, Image, Progress } from "@chakra-ui/react"
import { FiCamera, FiX, FiCheck, FiRotateCw, FiUpload, FiImage } from "react-icons/fi"
import { useState, useRef, useEffect } from "react"
import useCustomToast from '@/hooks/useCustomToast'
import useAuth from '@/hooks/useAuth'
import { OpenAPI } from "@/client/core/OpenAPI"
import axios from "axios"

interface UploadResult {
  success: boolean
  file_id?: string
  invoice_id?: string
  message?: string
}

const MobileCameraUpload = () => {
  const [isCapturing, setIsCapturing] = useState(false)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { user } = useAuth()

  // 检测是否为移动端
  useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent || navigator.vendor
      const isMobileDevice = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase())
      const isSmallScreen = window.innerWidth < 768
      setIsMobile(isMobileDevice || isSmallScreen)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 启动摄像头
  const startCamera = async () => {
    try {
      setIsCapturing(true)
      
      // 优先使用后置摄像头（移动端）
      const constraints = {
        video: {
          facingMode: isMobile ? 'environment' : 'user', // environment = 后置摄像头
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
      }
    } catch (error: any) {
      console.error('启动摄像头失败:', error)
      setIsCapturing(false)
      
      if (error.name === 'NotAllowedError') {
        showErrorToast('需要授权访问摄像头，请在浏览器设置中允许摄像头权限')
      } else if (error.name === 'NotFoundError') {
        showErrorToast('未找到摄像头设备')
      } else {
        showErrorToast(`启动摄像头失败: ${error.message}`)
      }
    }
  }

  // 停止摄像头
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    setIsCapturing(false)
  }

  // 拍照
  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    if (!ctx) return

    // 设置画布尺寸
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // 绘制当前视频帧到画布
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    // 转换为图片数据
    const imageData = canvas.toDataURL('image/jpeg', 0.9)
    setCapturedImage(imageData)
    stopCamera()
  }

  // 压缩图片
  const compressImage = (file: File, maxWidth: number = 1920, quality: number = 0.8): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const img = new Image()
        img.onload = () => {
          const canvas = document.createElement('canvas')
          const ctx = canvas.getContext('2d')
          if (!ctx) {
            reject(new Error('无法创建画布上下文'))
            return
          }

          // 计算压缩后的尺寸
          let width = img.width
          let height = img.height
          if (width > maxWidth) {
            height = (height * maxWidth) / width
            width = maxWidth
          }

          canvas.width = width
          canvas.height = height
          ctx.drawImage(img, 0, 0, width, height)

          canvas.toBlob(
            (blob) => {
              if (blob) {
                resolve(blob)
              } else {
                reject(new Error('图片压缩失败'))
              }
            },
            'image/jpeg',
            quality
          )
        }
        img.onerror = () => reject(new Error('图片加载失败'))
        img.src = e.target?.result as string
      }
      reader.onerror = () => reject(new Error('文件读取失败'))
      reader.readAsDataURL(file)
    })
  }

  // 上传图片
  const uploadImage = async (imageData: string) => {
    try {
      setIsUploading(true)
      setUploadProgress(0)
      setUploadResult(null)

      // 将 base64 转换为 Blob
      const response = await fetch(imageData)
      const blob = await response.blob()
      const file = new File([blob], `invoice_${Date.now()}.jpg`, { type: 'image/jpeg' })

      // 压缩图片（移动端拍照通常较大）
      const compressedBlob = await compressImage(file, 1920, 0.8)
      const compressedFile = new File([compressedBlob], file.name, { type: 'image/jpeg' })

      console.log(`原始大小: ${(file.size / 1024 / 1024).toFixed(2)}MB`)
      console.log(`压缩后: ${(compressedFile.size / 1024 / 1024).toFixed(2)}MB`)

      // 创建 FormData
      const formData = new FormData()
      formData.append('file', compressedFile)

      // 获取 token
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未登录，请先登录')
      }

      // 上传到后端
      // 使用相对路径，让Vite proxy处理，避免跨域问题
      const apiBaseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || ''
      const uploadResponse = await axios.post(
        `${apiBaseUrl}/api/v1/invoices/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${token}`
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              )
              setUploadProgress(percentCompleted)
            }
          }
        }
      )

      const result: UploadResult = {
        success: true,
        file_id: uploadResponse.data.data?.file_id,
        invoice_id: uploadResponse.data.data?.invoice_id,
        message: uploadResponse.data.message || '上传成功'
      }

      setUploadResult(result)
      showSuccessToast('图片上传成功！')
      
      // 3秒后清空结果，允许继续上传
      setTimeout(() => {
        setCapturedImage(null)
        setUploadResult(null)
      }, 3000)

    } catch (error: any) {
      console.error('上传失败:', error)
      const errorMessage = error.response?.data?.detail || error.message || '上传失败'
      showErrorToast(errorMessage)
      setUploadResult({
        success: false,
        message: errorMessage
      })
    } finally {
      setIsUploading(false)
    }
  }

  // 从相册选择
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      showErrorToast('请选择图片文件')
      return
    }

    // 验证文件大小（10MB）
    if (file.size > 10 * 1024 * 1024) {
      showErrorToast('文件大小不能超过10MB')
      return
    }

    // 读取文件并显示预览
    const reader = new FileReader()
    reader.onload = (e) => {
      setCapturedImage(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  // 重新拍照
  const retakePhoto = () => {
    setCapturedImage(null)
    setUploadResult(null)
    startCamera()
  }

  // 清理资源
  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return (
    <Box p={4} maxW="600px" mx="auto">
      <VStack spacing={4} align="stretch">
        {/* 标题 */}
        <Text fontSize="xl" fontWeight="bold" textAlign="center">
          移动端拍照上传
        </Text>

        {/* 摄像头预览区域 */}
        {isCapturing && !capturedImage && (
          <Box position="relative" w="100%" bg="black" borderRadius="md" overflow="hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ width: '100%', display: 'block' }}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            
            {/* 拍照按钮 */}
            <Flex
              position="absolute"
              bottom={4}
              left="50%"
              transform="translateX(-50%)"
              gap={4}
            >
              <IconButton
                aria-label="拍照"
                icon={<FiCamera />}
                colorScheme="blue"
                size="lg"
                borderRadius="full"
                onClick={capturePhoto}
              />
              <IconButton
                aria-label="取消"
                icon={<FiX />}
                colorScheme="gray"
                size="lg"
                borderRadius="full"
                onClick={stopCamera}
              />
            </Flex>
          </Box>
        )}

        {/* 图片预览区域 */}
        {capturedImage && !isUploading && (
          <Box position="relative" w="100%">
            <Image
              src={capturedImage}
              alt="拍摄的发票"
              w="100%"
              borderRadius="md"
              objectFit="contain"
              bg="gray.100"
            />
            
            {/* 操作按钮 */}
            <Flex mt={4} gap={2} justify="center">
              <Button
                leftIcon={<FiRotateCw />}
                onClick={retakePhoto}
                variant="outline"
              >
                重新拍照
              </Button>
              <Button
                leftIcon={<FiUpload />}
                onClick={() => uploadImage(capturedImage)}
                colorScheme="blue"
              >
                上传
              </Button>
            </Flex>
          </Box>
        )}

        {/* 上传进度 */}
        {isUploading && (
          <VStack spacing={2}>
            <Text fontSize="sm" color="gray.600">
              上传中... {uploadProgress}%
            </Text>
            <Progress value={uploadProgress} w="100%" colorScheme="blue" />
          </VStack>
        )}

        {/* 上传结果 */}
        {uploadResult && (
          <Box
            p={4}
            borderRadius="md"
            bg={uploadResult.success ? 'green.50' : 'red.50'}
            borderColor={uploadResult.success ? 'green.200' : 'red.200'}
            borderWidth={1}
          >
            <Flex align="center" gap={2}>
              {uploadResult.success ? (
                <FiCheck color="green" />
              ) : (
                <FiX color="red" />
              )}
              <Text color={uploadResult.success ? 'green.700' : 'red.700'}>
                {uploadResult.message}
              </Text>
            </Flex>
            {uploadResult.invoice_id && (
              <Text fontSize="sm" color="gray.600" mt={2}>
                票据ID: {uploadResult.invoice_id}
              </Text>
            )}
          </Box>
        )}

        {/* 操作按钮区域 */}
        {!isCapturing && !capturedImage && (
          <VStack spacing={3}>
            <Button
              leftIcon={<FiCamera />}
              onClick={startCamera}
              colorScheme="blue"
              size="lg"
              w="100%"
            >
              打开摄像头拍照
            </Button>
            
            <Button
              leftIcon={<FiImage />}
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              size="lg"
              w="100%"
            >
              从相册选择
            </Button>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              style={{ display: 'none' }}
              onChange={handleFileSelect}
            />
          </VStack>
        )}

        {/* 使用说明 */}
        <Box p={4} bg="blue.50" borderRadius="md">
          <Text fontSize="sm" fontWeight="medium" mb={2}>
            使用说明：
          </Text>
          <VStack align="start" spacing={1} fontSize="xs" color="gray.600">
            <Text>1. 点击"打开摄像头拍照"按钮，授权摄像头权限</Text>
            <Text>2. 将发票放在摄像头前，点击拍照按钮</Text>
            <Text>3. 预览拍摄的照片，确认无误后点击上传</Text>
            <Text>4. 也可以从相册选择已拍摄的发票照片</Text>
            <Text>5. 支持 JPG、PNG 格式，文件大小不超过 10MB</Text>
          </VStack>
        </Box>
      </VStack>
    </Box>
  )
}

export default MobileCameraUpload

