import { Container, Image, Input, Tabs, Box, VStack } from "@chakra-ui/react"
import {
  createFileRoute,
  redirect,
} from "@tanstack/react-router"
import { type SubmitHandler, useForm } from "react-hook-form"
import { useState } from "react"
import { FiLock, FiUser } from "react-icons/fi"

import type { Body_login_login_access_token as AccessToken, UserRegister } from "@/client"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { InputGroup } from "@/components/ui/input-group"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import Logo from "/assets/images/syntax-logo.svg"
import { emailPattern, passwordRules, confirmPasswordRules } from "../utils"

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
})

interface UserRegisterForm extends UserRegister {
  confirm_password: string
}

function Login() {
  const { loginMutation, signUpMutation, error, resetError } = useAuth()
  const { showSuccessToast } = useCustomToast()
  const [activeTab, setActiveTab] = useState<"login" | "register">("login")
  
  // 登录表单
  const loginForm = useForm<AccessToken & { language: string }>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
      language: "zh",
    },
  })

  // 注册表单
  const registerForm = useForm<UserRegisterForm>({
    mode: "onChange", // 改为 onChange 以便实时验证
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
    },
  })

  const onLoginSubmit: SubmitHandler<AccessToken & { language: string }> = async (data) => {
    console.log('登录表单提交:', data)
    console.log('表单验证状态:', {
      isValid: loginForm.formState.isValid,
      errors: loginForm.formState.errors,
      isSubmitting: loginForm.formState.isSubmitting
    })
    
    resetError()

    try {
      // 只传递登录所需的字段
      const loginData = {
        username: data.username,
        password: data.password,
      }
      console.log('发送登录请求:', loginData)
      await loginMutation.mutateAsync(loginData)
    } catch (err) {
      console.error('登录错误:', err)
      // error is handled by useAuth hook
    }
  }

  const onRegisterSubmit: SubmitHandler<UserRegisterForm> = async (data) => {
    console.log('注册表单提交:', data)
    console.log('注册表单验证状态:', {
      isValid: registerForm.formState.isValid,
      errors: registerForm.formState.errors,
      isSubmitting: registerForm.formState.isSubmitting
    })

    resetError()

    try {
      // 移除 confirm_password 字段，只传递 UserRegister 需要的字段
      const registerData: UserRegister = {
        email: data.email,
        password: data.password,
        full_name: data.full_name || null,
      }
      console.log('发送注册请求:', registerData)
      await signUpMutation.mutateAsync(registerData)
      
      // 注册成功后的处理
      showSuccessToast("注册成功！请使用您的邮箱和密码登录。")
      
      // 重置注册表单
      registerForm.reset()
      
      // 切换到登录标签页
      setActiveTab("login")
    } catch (err) {
      console.error('注册错误:', err)
      // error is handled by useAuth hook
    }
  }



  return (
    <>
      <Container
        h="100vh"
        maxW="sm"
        alignItems="stretch"
        justifyContent="center"
        gap={4}
        centerContent
      >
        <Image
          src={Logo}
          alt="FastAPI logo"
          height="auto"
          maxW="2xs"
          alignSelf="center"
          mb={4}
        />
        
        <Tabs.Root
          value={activeTab}
          onValueChange={(e) => setActiveTab(e.value as "login" | "register")}
          w="100%"
        >
          <Tabs.List>
            <Tabs.Trigger value="login">登录</Tabs.Trigger>
            <Tabs.Trigger value="register">注册</Tabs.Trigger>
          </Tabs.List>

          {/* 登录标签页 */}
          <Tabs.Content value="login">
            <Box 
              as="form" 
              onSubmit={loginForm.handleSubmit(onLoginSubmit)} 
              w="100%"
            >
              <VStack gap={4} align="stretch">
              <Field
                invalid={!!loginForm.formState.errors.username}
                errorText={loginForm.formState.errors.username?.message || (error ? String(error) : undefined)}
        >
          <InputGroup w="100%" startElement={<FiUser />}>
            <Input
              id="username"
                    {...loginForm.register("username", {
                required: "Username is required",
                pattern: emailPattern,
              })}
              placeholder="Email"
              type="email"
            />
          </InputGroup>
        </Field>
        <PasswordInput
          type="password"
          startElement={<FiLock />}
                {...loginForm.register("password", passwordRules())}
          placeholder="Password"
                errors={loginForm.formState.errors}
        />
        
        <Field
                invalid={!!loginForm.formState.errors.language}
                errorText={loginForm.formState.errors.language?.message}
        >
          <select
            id="language"
                  {...loginForm.register("language")}
                  defaultValue="zh"
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              fontSize: '14px',
              backgroundColor: 'white'
            }}
          >
            <option value="zh">中文</option>
            <option value="en">英语</option>
            <option value="de">德语</option>
          </select>
        </Field>
        
              <Button 
                variant="solid" 
                type="submit" 
                loading={loginForm.formState.isSubmitting} 
                size="md"
                w="100%"
                disabled={loginForm.formState.isSubmitting}
              >
                登录
              </Button>
              </VStack>
            </Box>
          </Tabs.Content>

          {/* 注册标签页 */}
          <Tabs.Content value="register">
            <Box 
              as="form" 
              onSubmit={(e) => {
                console.log('注册表单提交事件触发')
                registerForm.handleSubmit(onRegisterSubmit)(e)
              }} 
              w="100%"
            >
              <VStack gap={4} align="stretch">
              <Field
                invalid={!!registerForm.formState.errors.full_name}
                errorText={registerForm.formState.errors.full_name?.message}
              >
                <InputGroup w="100%" startElement={<FiUser />}>
                  <Input
                    id="full_name"
                    {...registerForm.register("full_name", {
                      required: "Full Name is required",
                    })}
                    placeholder="Full Name"
                    type="text"
                  />
                </InputGroup>
              </Field>

              <Field
                invalid={!!registerForm.formState.errors.email}
                errorText={registerForm.formState.errors.email?.message}
              >
                <InputGroup w="100%" startElement={<FiUser />}>
                  <Input
                    id="email"
                    {...registerForm.register("email", {
                      required: "Email is required",
                      pattern: emailPattern,
                    })}
                    placeholder="Email"
                    type="email"
                  />
                </InputGroup>
              </Field>

              <PasswordInput
                type="password"
                startElement={<FiLock />}
                {...registerForm.register("password", passwordRules())}
                placeholder="Password"
                errors={registerForm.formState.errors}
              />

              <PasswordInput
                type="confirm_password"
                startElement={<FiLock />}
                {...registerForm.register("confirm_password", confirmPasswordRules(registerForm.getValues))}
                placeholder="Confirm Password"
                errors={registerForm.formState.errors}
              />
        
        <Button 
          variant="solid" 
          type="submit" 
                loading={registerForm.formState.isSubmitting}
          size="md"
          w="100%"
                disabled={registerForm.formState.isSubmitting}
                onClick={() => {
                  console.log('注册按钮点击')
                  console.log('表单状态:', {
                    isValid: registerForm.formState.isValid,
                    errors: registerForm.formState.errors,
                    isDirty: registerForm.formState.isDirty,
                    isSubmitting: registerForm.formState.isSubmitting
                  })
                }}
              >
                注册
        </Button>
              </VStack>
            </Box>
          </Tabs.Content>
        </Tabs.Root>
      </Container>
    </>
  )
}
