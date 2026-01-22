import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import {
  type Body_login_login_access_token as AccessToken,
  type ApiError,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from "@/client"
import { handleError } from "@/utils"
import { unifiedApiClient } from "@/client/unifiedTypes"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),

    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  // 原有的登录方法（保持兼容性）
  const login = async (data: AccessToken) => {
    try {
      const response = await LoginService.loginAccessToken({
        formData: data,
      })

      localStorage.setItem("access_token", response.access_token)
    } catch (error) {
      throw error;
    }
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  // 新的统一对象登录方法
  const loginUnified = async (email: string, password: string) => {
    try {
      const response = await unifiedApiClient.login(email, password)
      
      if (response.success && response.data?.access_token) {
        // 登录成功，token已经在unifiedApiClient中设置
        console.log("统一对象登录成功:", response.message)
        return response.data
      } else {
        // 登录失败
        const errorMessage = response.message || "登录失败"
        console.error("统一对象登录失败:", errorMessage)
        throw new Error(errorMessage)
      }
    } catch (error) {
      console.error("统一对象登录异常:", error)
      throw error
    }
  }

  const loginUnifiedMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      loginUnified(email, password),
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    unifiedApiClient.clearAccessToken() // 清除统一API客户端的token
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    loginUnifiedMutation, // 新增的统一对象登录方法
    logout,
    user,
    error,
    resetError: () => setError(null),
  }
}

export { isLoggedIn }
export default useAuth
