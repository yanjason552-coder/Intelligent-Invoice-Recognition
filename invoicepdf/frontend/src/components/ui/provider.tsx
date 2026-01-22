"use client"

import { ChakraProvider } from "@chakra-ui/react"
import React, { type PropsWithChildren } from "react"
import { system } from "../../theme"
import { ColorModeProvider } from "./color-mode"
import { ToastProvider } from "./toast"

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
