"use client"

import { useToast } from '@/components/ui/toast'

const useCustomToast = () => {
  const { addToast } = useToast()

  const showSuccessToast = (description: string) => {
    console.log("✅ 成功Toast:", description)
    addToast({
      title: "成功",
      description,
      type: "success"
    })
  }

  const showErrorToast = (description: string) => {
    console.log("❌ 错误Toast:", description)
    addToast({
      title: "错误",
      description,
      type: "error"
    })
  }

  const showInfoToast = (description: string) => {
    console.log("ℹ️ 信息Toast:", description)
    addToast({
      title: "提示",
      description,
      type: "info"
    })
  }

  return { showSuccessToast, showErrorToast, showInfoToast }
}

export default useCustomToast
