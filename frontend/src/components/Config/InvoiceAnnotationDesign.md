# 发票预览与标注页面设计方案

## 📋 一、功能需求分析

### 1.1 核心功能
- ✅ 发票图片/PDF预览
- ✅ 字段位置标注（矩形框）
- ✅ Logo位置标注
- ✅ 正则匹配区域标注
- ✅ 标注与模板字段关联
- ✅ 标注编辑、删除、重命名
- ✅ 标注列表管理
- ✅ 坐标系统（支持缩放）

### 1.2 用户体验需求
- 直观的可视化标注界面
- 流畅的交互操作
- 清晰的标注信息展示
- 便捷的字段关联操作

---

## 🎨 二、UI布局设计

### 2.1 整体布局（三栏式）

```
┌─────────────────────────────────────────────────────────────┐
│  模板编辑页面                                                │
├──────────────┬──────────────────────────┬───────────────────┤
│              │                          │                   │
│  左侧：      │  中间：                  │  右侧：           │
│  模板配置    │  发票预览与标注          │  标注列表与字段  │
│              │                          │                   │
│  - 基本信息  │  ┌────────────────────┐  │  ┌──────────────┐ │
│  - Schema    │  │                    │  │  │ 标注列表     │ │
│  - 字段定义  │  │   发票预览图        │  │  │ - Logo      │ │
│              │  │   (Canvas/Image)   │  │  │ - 字段1     │ │
│              │  │                    │  │  │ - 字段2     │ │
│              │  │   [标注框显示]     │  │  │              │ │
│              │  │                    │  │  └──────────────┘ │
│              │  └────────────────────┘  │                   │
│              │                          │  ┌──────────────┐ │
│              │  [工具栏]                │  │ 字段关联     │ │
│              │  - 选择工具              │  │ - 字段名称   │ │
│              │  - 标注工具              │  │ - 字段类型   │ │
│              │  - 删除工具              │  │              │ │
│              │  - 缩放控制              │  └──────────────┘ │
│              │                          │                   │
└──────────────┴──────────────────────────┴───────────────────┘
```

### 2.2 响应式布局
- **大屏（>1200px）**：三栏布局
- **中屏（768-1200px）**：两栏布局（左侧+中间，右侧可折叠）
- **小屏（<768px）**：单栏布局（标签页切换）

---

## 🛠️ 三、功能模块设计

### 3.1 预览区域

#### 3.1.1 图片预览
- **支持格式**：JPG、PNG、PDF（PDF需转换为图片）
- **显示方式**：
  - Canvas渲染（支持标注绘制）
  - 或 SVG覆盖层（更灵活）
- **缩放功能**：
  - 鼠标滚轮缩放
  - 缩放滑块（0.5x - 2x）
  - 适应窗口按钮
- **平移功能**：
  - 拖拽移动（当图片大于容器时）
  - 重置位置按钮

#### 3.1.2 PDF预览
- **方案1**：PDF.js转换为Canvas
- **方案2**：后端API转换为图片
- **方案3**：iframe嵌入（标注功能受限）

**推荐方案**：后端转换为图片，前端使用Canvas标注

### 3.2 标注工具

#### 3.2.1 标注类型
1. **字段标注（Field）**
   - 颜色：蓝色 (#3B82F6)
   - 用途：标注字段位置
   - 关联：必须关联到模板字段

2. **Logo标注（Logo）**
   - 颜色：绿色 (#10B981)
   - 用途：标注Logo位置
   - 关联：关联到Logo匹配规则

3. **正则区域标注（Regex）**
   - 颜色：橙色 (#F59E0B)
   - 用途：标注正则匹配区域
   - 关联：关联到正则规则

#### 3.2.2 标注操作
- **创建标注**：
  - 点击"标注"按钮进入标注模式
  - 在图片上拖拽创建矩形框
  - 创建后弹出标注属性对话框

- **编辑标注**：
  - 点击标注框选中
  - 显示控制点（8个点：4角+4边中点）
  - 拖拽控制点调整大小
  - 拖拽标注框移动位置

- **删除标注**：
  - 选中标注后按Delete键
  - 或点击删除按钮
  - 确认对话框

- **标注属性**：
  - 标注类型选择
  - 标注名称/标签
  - 关联字段选择
  - 坐标信息显示（x, y, width, height）

### 3.3 标注列表面板

#### 3.3.1 列表显示
```
┌─────────────────────────────┐
│ 标注列表 (3)                │
├─────────────────────────────┤
│ 🟢 Logo - 公司Logo          │
│   位置: (50, 30, 100, 50)   │
│   [编辑] [删除]             │
├─────────────────────────────┤
│ 🔵 字段 - 发票号码           │
│   位置: (200, 100, 150, 30) │
│   关联: invoice_no          │
│   [编辑] [删除]             │
├─────────────────────────────┤
│ 🟠 正则 - 金额匹配          │
│   位置: (300, 200, 200, 30) │
│   规则: \d+\.\d{2}          │
│   [编辑] [删除]             │
└─────────────────────────────┘
```

#### 3.3.2 交互功能
- **点击列表项**：高亮对应标注框
- **悬停列表项**：预览标注位置
- **拖拽排序**：调整标注优先级
- **批量操作**：全选、批量删除

### 3.4 字段关联面板

#### 3.4.1 字段选择
- **下拉选择**：从模板字段列表选择
- **自动匹配**：根据标注名称自动匹配字段
- **字段信息**：显示字段类型、是否必填等

#### 3.4.2 关联状态
- **已关联**：显示绿色标记
- **未关联**：显示黄色警告
- **关联冲突**：多个标注关联同一字段时警告

---

## 💻 四、技术实现方案

### 4.1 组件架构

```
InvoiceAnnotationEditor (主组件)
├── AnnotationToolbar (工具栏)
│   ├── ToolSelector (工具选择)
│   ├── ZoomControls (缩放控制)
│   └── ActionButtons (操作按钮)
├── AnnotationCanvas (标注画布)
│   ├── ImageRenderer (图片渲染)
│   ├── AnnotationLayer (标注层)
│   └── InteractionHandler (交互处理)
├── AnnotationList (标注列表)
│   ├── AnnotationItem (标注项)
│   └── AnnotationFilter (筛选器)
└── FieldAssociationPanel (字段关联面板)
    ├── FieldSelector (字段选择器)
    └── AssociationStatus (关联状态)
```

### 4.2 坐标系统

#### 4.2.1 坐标转换
```typescript
// 屏幕坐标 -> 图片坐标
function screenToImage(screenX: number, screenY: number, scale: number, offset: {x: number, y: number}) {
  return {
    x: (screenX - offset.x) / scale,
    y: (screenY - offset.y) / scale
  }
}

// 图片坐标 -> 屏幕坐标
function imageToScreen(imageX: number, imageY: number, scale: number, offset: {x: number, y: number}) {
  return {
    x: imageX * scale + offset.x,
    y: imageY * scale + offset.y
  }
}
```

#### 4.2.2 坐标存储
- **存储格式**：相对于原始图片的坐标（不受缩放影响）
- **单位**：像素（px）
- **精度**：整数或保留1位小数

### 4.3 标注数据结构

```typescript
interface Annotation {
  id: string
  type: 'field' | 'logo' | 'regex'
  label: string  // 标注名称
  x: number      // 左上角X坐标（图片坐标）
  y: number      // 左上角Y坐标（图片坐标）
  width: number  // 宽度（图片坐标）
  height: number // 高度（图片坐标）
  color: string  // 标注颜色
  fieldId?: string  // 关联的字段ID
  fieldName?: string // 关联的字段名称
  regexPattern?: string // 正则表达式（仅regex类型）
  priority?: number    // 优先级（仅regex类型）
  createdAt: string
  updatedAt: string
}
```

### 4.4 状态管理

```typescript
interface AnnotationState {
  // 图片相关
  imageUrl: string | null
  imageSize: { width: number, height: number } | null
  scale: number
  offset: { x: number, y: number }
  
  // 标注相关
  annotations: Annotation[]
  selectedAnnotationId: string | null
  currentTool: 'select' | 'annotate' | 'delete'
  isDrawing: boolean
  
  // UI状态
  showAnnotationList: boolean
  showFieldPanel: boolean
  annotationDialogOpen: boolean
}
```

---

## 🎯 五、交互流程设计

### 5.1 创建标注流程

```
1. 用户点击"标注"按钮
   ↓
2. 进入标注模式（鼠标变为十字）
   ↓
3. 用户在图片上拖拽创建矩形框
   ↓
4. 释放鼠标，弹出标注属性对话框
   ↓
5. 用户填写：
   - 标注类型（字段/Logo/正则）
   - 标注名称
   - 关联字段（如果是字段类型）
   - 正则表达式（如果是正则类型）
   ↓
6. 点击"确定"，创建标注
   ↓
7. 标注显示在画布和列表中
```

### 5.2 编辑标注流程

```
1. 用户点击标注框或列表项
   ↓
2. 标注框高亮，显示控制点
   ↓
3. 用户操作：
   - 拖拽控制点：调整大小
   - 拖拽标注框：移动位置
   - 双击：打开属性对话框
   ↓
4. 修改属性后保存
```

### 5.3 字段关联流程

```
1. 用户创建或编辑字段标注
   ↓
2. 在属性对话框中选择"关联字段"
   ↓
3. 从下拉列表选择模板字段
   ↓
4. 系统验证：
   - 字段是否存在
   - 是否已被其他标注关联（可选）
   ↓
5. 保存关联关系
   ↓
6. 标注列表显示关联状态
```

---

## 📐 六、UI组件设计

### 6.1 工具栏组件

```tsx
<AnnotationToolbar>
  <ToolGroup>
    <ToolButton icon="select" active={tool === 'select'} />
    <ToolButton icon="annotate" active={tool === 'annotate'} />
    <ToolButton icon="delete" active={tool === 'delete'} />
  </ToolGroup>
  
  <Divider />
  
  <ZoomControls>
    <Button onClick={zoomOut}>-</Button>
    <Text>{Math.round(scale * 100)}%</Text>
    <Button onClick={zoomIn}>+</Button>
    <Button onClick={fitToWindow}>适应窗口</Button>
  </ZoomControls>
  
  <Divider />
  
  <ActionButtons>
    <Button onClick={clearAll}>清空所有</Button>
    <Button onClick={exportAnnotations}>导出</Button>
  </ActionButtons>
</AnnotationToolbar>
```

### 6.2 标注画布组件

```tsx
<AnnotationCanvas>
  {/* 背景图片 */}
  <ImageLayer src={imageUrl} />
  
  {/* 标注层 */}
  <AnnotationLayer>
    {annotations.map(annotation => (
      <AnnotationBox
        key={annotation.id}
        annotation={annotation}
        selected={selectedAnnotationId === annotation.id}
        onSelect={() => setSelectedAnnotationId(annotation.id)}
        onUpdate={handleAnnotationUpdate}
        onDelete={handleAnnotationDelete}
      />
    ))}
  </AnnotationLayer>
  
  {/* 交互层 */}
  <InteractionLayer
    tool={currentTool}
    onAnnotationCreate={handleAnnotationCreate}
  />
</AnnotationCanvas>
```

### 6.3 标注属性对话框

```tsx
<AnnotationDialog open={dialogOpen}>
  <DialogHeader>
    <DialogTitle>
      {editingAnnotation ? '编辑标注' : '新建标注'}
    </DialogTitle>
  </DialogHeader>
  
  <DialogBody>
    <Field label="标注类型">
      <Select value={type} onChange={setType}>
        <option value="field">字段标注</option>
        <option value="logo">Logo标注</option>
        <option value="regex">正则区域</option>
      </Select>
    </Field>
    
    <Field label="标注名称">
      <Input value={label} onChange={setLabel} />
    </Field>
    
    {type === 'field' && (
      <Field label="关联字段">
        <Select value={fieldId} onChange={setFieldId}>
          <option value="">未关联</option>
          {fields.map(field => (
            <option key={field.id} value={field.id}>
              {field.field_name}
            </option>
          ))}
        </Select>
      </Field>
    )}
    
    {type === 'regex' && (
      <Field label="正则表达式">
        <Input value={regexPattern} onChange={setRegexPattern} />
      </Field>
    )}
    
    <Field label="坐标信息">
      <Text fontSize="sm" color="gray.600">
        X: {x}, Y: {y}, 宽: {width}, 高: {height}
      </Text>
    </Field>
  </DialogBody>
  
  <DialogFooter>
    <Button onClick={handleCancel}>取消</Button>
    <Button onClick={handleSave} colorScheme="blue">保存</Button>
  </DialogFooter>
</AnnotationDialog>
```

---

## 🔧 七、实现建议

### 7.1 推荐技术栈

1. **Canvas渲染**
   - 使用HTML5 Canvas API
   - 优点：性能好，支持复杂绘制
   - 缺点：需要手动处理交互

2. **SVG覆盖层**
   - 使用SVG元素覆盖图片
   - 优点：DOM操作简单，CSS样式支持
   - 缺点：性能略差于Canvas

3. **React-Konva**（推荐）
   - 基于Canvas的React库
   - 优点：React组件化，性能好，功能强大
   - 缺点：需要额外依赖

### 7.2 推荐方案：React-Konva

```tsx
import { Stage, Layer, Image, Rect, Text } from 'react-konva'

<Stage width={800} height={600}>
  <Layer>
    <Image image={imageRef} />
    {annotations.map(ann => (
      <Rect
        key={ann.id}
        x={ann.x}
        y={ann.y}
        width={ann.width}
        height={ann.height}
        stroke={ann.color}
        strokeWidth={2}
        draggable
        onDragEnd={(e) => handleAnnotationMove(ann.id, e.target.position())}
        onTransformEnd={(e) => handleAnnotationResize(ann.id, e.target.getAttrs())}
      />
    ))}
  </Layer>
</Stage>
```

### 7.3 实现步骤

1. **第一阶段**：基础预览和标注
   - 实现图片预览
   - 实现基础矩形标注
   - 实现标注的创建、编辑、删除

2. **第二阶段**：增强功能
   - 添加标注类型区分
   - 实现字段关联
   - 添加标注列表

3. **第三阶段**：优化体验
   - 添加缩放和平移
   - 优化交互反馈
   - 添加快捷键支持

---

## 📝 八、关键实现细节

### 8.1 坐标转换

```typescript
// 计算标注框在屏幕上的位置（考虑缩放和偏移）
function getScreenRect(annotation: Annotation, scale: number, offset: {x: number, y: number}) {
  return {
    x: annotation.x * scale + offset.x,
    y: annotation.y * scale + offset.y,
    width: annotation.width * scale,
    height: annotation.height * scale
  }
}

// 将屏幕坐标转换为图片坐标
function screenToImage(screenX: number, screenY: number, scale: number, offset: {x: number, y: number}) {
  return {
    x: (screenX - offset.x) / scale,
    y: (screenY - offset.y) / scale
  }
}
```

### 8.2 标注碰撞检测

```typescript
// 检查点是否在标注框内
function isPointInAnnotation(x: number, y: number, annotation: Annotation): boolean {
  return x >= annotation.x &&
         x <= annotation.x + annotation.width &&
         y >= annotation.y &&
         y <= annotation.y + annotation.height
}

// 获取鼠标位置下的标注（从后往前检查，后绘制的在上层）
function getAnnotationAtPoint(x: number, y: number, annotations: Annotation[]): Annotation | null {
  for (let i = annotations.length - 1; i >= 0; i--) {
    if (isPointInAnnotation(x, y, annotations[i])) {
      return annotations[i]
    }
  }
  return null
}
```

### 8.3 标注框调整大小

```typescript
// 8个控制点的位置
const controlPoints = [
  { x: annotation.x, y: annotation.y }, // 左上
  { x: annotation.x + annotation.width / 2, y: annotation.y }, // 上中
  { x: annotation.x + annotation.width, y: annotation.y }, // 右上
  { x: annotation.x + annotation.width, y: annotation.y + annotation.height / 2 }, // 右中
  { x: annotation.x + annotation.width, y: annotation.y + annotation.height }, // 右下
  { x: annotation.x + annotation.width / 2, y: annotation.y + annotation.height }, // 下中
  { x: annotation.x, y: annotation.y + annotation.height }, // 左下
  { x: annotation.x, y: annotation.y + annotation.height / 2 }, // 左中
]

// 根据拖拽的控制点更新标注框
function resizeAnnotation(
  annotation: Annotation,
  controlPointIndex: number,
  newX: number,
  newY: number
): Annotation {
  // 根据控制点索引计算新的位置和大小
  // ...
}
```

---

## ✅ 九、最佳实践建议

### 9.1 性能优化
- 使用 `useMemo` 缓存计算结果
- 使用 `useCallback` 缓存事件处理函数
- 大量标注时使用虚拟滚动
- Canvas绘制使用 `requestAnimationFrame`

### 9.2 用户体验优化
- 添加加载状态提示
- 添加操作撤销/重做功能
- 添加快捷键支持（Delete删除，Esc取消）
- 添加操作提示和引导

### 9.3 错误处理
- 图片加载失败处理
- 标注坐标越界检查
- 字段关联验证
- 网络请求错误处理

---

## 🎨 十、UI设计建议

### 10.1 颜色方案
- **字段标注**：蓝色 (#3B82F6)
- **Logo标注**：绿色 (#10B981)
- **正则标注**：橙色 (#F59E0B)
- **选中状态**：红色 (#EF4444)
- **背景**：浅灰色 (#F7FAFC)

### 10.2 交互反馈
- **悬停效果**：标注框高亮
- **选中效果**：标注框加粗，显示控制点
- **拖拽反馈**：半透明预览
- **操作提示**：Toast通知

---

## 📦 十一、组件拆分建议

建议将功能拆分为以下独立组件：

1. **InvoiceAnnotationEditor** - 主容器组件
2. **AnnotationCanvas** - 标注画布组件
3. **AnnotationToolbar** - 工具栏组件
4. **AnnotationList** - 标注列表组件
5. **AnnotationDialog** - 标注属性对话框
6. **FieldAssociationPanel** - 字段关联面板
7. **ZoomControls** - 缩放控制组件

这样可以提高代码的可维护性和可复用性。

