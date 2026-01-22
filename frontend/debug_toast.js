// Toast调试脚本
// 在浏览器控制台中运行

function debugToast() {
  console.log('🔍 开始调试Toast功能...')
  
  // 检查React组件
  console.log('\n📋 检查React组件:')
  const reactElements = document.querySelectorAll('[data-reactroot], [data-reactid]')
  console.log('React元素数量:', reactElements.length)
  
  // 检查Chakra UI元素
  console.log('\n📋 检查Chakra UI元素:')
  const chakraElements = document.querySelectorAll('[data-chakra]')
  console.log('Chakra元素数量:', chakraElements.length)
  
  // 检查Toast容器
  console.log('\n📋 检查Toast容器:')
  const toastContainers = document.querySelectorAll('[role="alert"], [data-toast]')
  console.log('Toast容器数量:', toastContainers.length)
  
  // 检查全局对象
  console.log('\n📋 检查全局对象:')
  console.log('window.chakra:', window.chakra)
  console.log('window.toaster:', window.toaster)
  console.log('window.React:', window.React)
  
  // 尝试手动触发toast
  console.log('\n📋 尝试手动触发toast:')
  try {
    // 创建一个简单的toast元素
    const toastDiv = document.createElement('div')
    toastDiv.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: green;
      color: white;
      padding: 12px 16px;
      border-radius: 4px;
      z-index: 9999;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `
    toastDiv.textContent = '测试Toast消息'
    document.body.appendChild(toastDiv)
    
    console.log('✅ 手动创建的toast元素已添加')
    
    // 3秒后移除
    setTimeout(() => {
      document.body.removeChild(toastDiv)
      console.log('✅ 手动创建的toast元素已移除')
    }, 3000)
    
  } catch (error) {
    console.error('❌ 手动创建toast失败:', error)
  }
  
  console.log('\n📝 调试说明:')
  console.log('1. 如果手动创建的toast显示，说明DOM操作正常')
  console.log('2. 如果Chakra UI元素存在，说明ChakraProvider正常')
  console.log('3. 如果React元素存在，说明React应用正常')
  console.log('4. 如果toast容器存在，说明toast系统已初始化')
}

// 运行调试
debugToast() 