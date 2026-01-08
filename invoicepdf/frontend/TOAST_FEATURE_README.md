# Toast 浮动提示功能说明

## 功能概述

Toast浮动提示功能用于在页面右下角显示临时的成功、错误或信息提示，提供现代化的用户体验。

## 功能特点

### 1. 显示位置
- **位置**: 右下角固定位置
- **层级**: 最高层级，不会被其他元素遮挡
- **动画**: 平滑的滑入动画效果

### 2. 自动消失
- **持续时间**: 3秒后自动消失
- **手动关闭**: 用户可以点击关闭按钮手动关闭
- **堆叠显示**: 支持多个Toast同时显示

### 3. 样式类型
- **成功提示**: 绿色背景，用于成功操作
- **错误提示**: 红色背景，用于错误信息
- **信息提示**: 蓝色背景，用于一般信息

## 使用方法

### 1. 导入Hook
```typescript
import useCustomToast from '@/hooks/useCustomToast'
```

### 2. 在组件中使用
```typescript
const { showSuccessToast, showErrorToast, showInfoToast } = useCustomToast()

// 显示成功提示
showSuccessToast('操作成功完成！')

// 显示错误提示
showErrorToast('操作失败，请重试！')

// 显示信息提示
showInfoToast('这是一条提示信息')
```

## 应用场景

### 1. 导入功能
- **成功**: "导入成功！成功导入 X 条记录"
- **错误**: "导入失败: 具体错误信息"

### 2. 导出功能
- **成功**: "成功导出 X 条记录"
- **错误**: "导出失败，请重试"

### 3. 查询功能
- **成功**: "条件查询成功，找到 X 条记录"
- **错误**: "查询失败: 具体错误信息"

### 4. 数据验证
- **错误**: "请选择Excel文件 (.xlsx 或 .xls)"
- **错误**: "文件中没有有效数据"
- **错误**: "没有数据可导出"

## 技术实现

### 1. Toast组件
- 基于React Context的自定义Toast组件
- 使用CSS动画实现滑入效果
- 支持多种类型和颜色

### 2. Hook封装
- 提供简洁的API接口
- 统一的中文标题
- 预定义的配置选项

### 3. 全局配置
- 通过ToastProvider全局注册
- 统一的显示位置和持续时间
- 响应式设计支持

## 配置选项

### 1. 显示位置
```typescript
position: "fixed"
bottom: "20px"
right: "20px"
```

### 2. 持续时间
```typescript
duration: 3000 // 3秒
```

### 3. 样式配置
```typescript
// 成功提示
backgroundColor: "#10b981"

// 错误提示
backgroundColor: "#ef4444"

// 信息提示
backgroundColor: "#3b82f6"
```

## 测试方法

### 1. 浏览器控制台测试
```javascript
// 运行测试脚本
// 在浏览器控制台中执行 frontend/test_floating_toast.js
```

### 2. 功能测试
1. 点击"测试"按钮验证Toast功能
2. 执行导入操作，观察成功/失败提示
3. 执行导出操作，观察成功/失败提示
4. 执行查询操作，观察结果提示
5. 测试多个Toast同时显示

## 优势特点

### 1. 用户体验
- **非阻塞**: 不会阻止用户操作
- **美观**: 现代化的UI设计
- **自动消失**: 无需用户手动关闭
- **动画效果**: 平滑的滑入动画

### 2. 技术优势
- **轻量级**: 纯React实现，无外部依赖
- **可定制**: 支持自定义样式和动画
- **类型安全**: 完整的TypeScript支持
- **性能优化**: 使用React.memo和useCallback

### 3. 功能完整
- **多类型支持**: 成功、错误、信息三种类型
- **堆叠显示**: 支持多个Toast同时显示
- **手动关闭**: 提供关闭按钮
- **自动清理**: 自动移除过期的Toast

## 注意事项

1. **Provider配置**: 确保ToastProvider正确包裹应用
2. **样式冲突**: 避免与其他组件的样式冲突
3. **性能考虑**: 大量Toast可能影响性能
4. **移动端适配**: 在小屏幕上可能需要调整样式

## 扩展功能

### 1. 自定义样式
- 支持自定义颜色主题
- 支持自定义动画效果
- 支持自定义位置

### 2. 高级功能
- 支持Toast队列管理
- 支持Toast优先级
- 支持Toast持久化显示
- 支持Toast分组显示

## 相关文件

- `frontend/src/components/ui/toast.tsx`: Toast组件实现
- `frontend/src/hooks/useCustomToast.ts`: Toast Hook封装
- `frontend/src/components/ui/provider.tsx`: Provider配置
- `frontend/test_floating_toast.js`: 测试脚本
- `frontend/TOAST_FEATURE_README.md`: 本文档 