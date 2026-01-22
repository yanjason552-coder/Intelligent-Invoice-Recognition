import { Flex, Image, useBreakpointValue, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"

import Logo from "/assets/images/syntax-logo.svg"
import UserMenu from "./UserMenu"

function Navbar() {
  const display = useBreakpointValue({ base: "none", md: "flex" })

  return (
    <Flex
      display={display}
      justify="space-between"
      position="sticky"
      color="white"
      align="center"
      bg="bg.muted"
      w="100%"
      top={0}
      p={2}
      minH="22px"  // 将高度设为现在的2倍 (11px * 2 = 22px)
      maxH="22px"  // 限制最大高度
    >
      <Link to="/">
        <Flex alignItems="center" gap={2}>
          <Image 
            src={Logo} 
            alt="Logo" 
            h="22px"     // 设置高度与导航栏同高
            w="auto"     // 宽度自适应，保持比例
            objectFit="contain"  // 保持图片比例，完整显示
          />
          <Text 
            fontSize="sm"  // 调整字体大小以适应22px高度
            fontWeight="bold"
            color="black"  // 保持黑色字体
          >
            票据识别系统
          </Text>
        </Flex>
      </Link>
      <Flex gap={1} alignItems="center">  {/* 减少间距 */}
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar
