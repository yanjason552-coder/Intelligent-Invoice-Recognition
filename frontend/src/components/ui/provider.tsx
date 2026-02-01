import { ChakraProvider } from "@chakra-ui/react"
import React, { type PropsWithChildren } from "react"
import { system } from "../../theme"
import { ColorModeProvider } from "./color-mode"
import { ToastProvider } from "./toast"

// 开发环境下的类型检查
if (process.env.NODE_ENV === 'development') {
  console.log('ToastProvider type check:', typeof ToastProvider, ToastProvider)
  if (typeof ToastProvider !== 'function') {
    console.error('ToastProvider is not a function:', typeof ToastProvider, ToastProvider)
  }
}

export function CustomProvider(props: PropsWithChildren) {
  return (
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="light">
        <ToastProvider>
          {props.children}
        </ToastProvider>
      </ColorModeProvider>
    </ChakraProvider>
  )
}
