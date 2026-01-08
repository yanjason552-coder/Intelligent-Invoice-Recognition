# 销售订单显示页面表格测试

## 新增功能

### 表格设计
- **位置**：工具栏下方
- **样式**：白色背景，圆角边框，带滚动条
- **数据源**：基于salesOrderDocD实体的字段结构
- **功能**：支持多选、排序、状态显示

### 表格列结构

#### 1. 选择列
- **功能**：全选/取消全选，单选行
- **样式**：复选框，支持半选状态

#### 2. 基本信息列
- **客户名称**：customer_full_name
- **订单单号**：doc_no
- **行号**：sequence
- **订单日期**：doc_date

#### 3. 物料信息列
- **物料编码**：material_code
- **物料描述**：material_description
- **材质编码**：material_type_code
- **规格**：dimensions_desc

#### 4. 数量和交期列
- **数量**：qty（右对齐）
- **交期**：delivery_date

#### 5. 状态和审计列
- **审批状态**：approve_status（带颜色标识）
- **创建人**：creator
- **创建日期**：create_date

### 状态显示
- **已审批**：蓝色背景 (#e6f7ff)，蓝色文字 (#1890ff)
- **待审批**：橙色背景 (#fff2e8)，橙色文字 (#fa8c16)

## 技术实现

### 数据结构
```typescript
interface SalesOrderItem {
  sales_order_doc_d_id: string
  customer_full_name: string
  doc_id: string
  doc_no: string
  sequence: string
  doc_date: string
  material_code: string
  material_description: string
  material_type_code: string
  dimensions_desc: string
  qty: number
  delivery_date: string
  approve_status: string
  creator: string
  create_date: string
}
```

### 状态管理
```typescript
const [selectedRows, setSelectedRows] = useState<string[]>([])

// 全选/取消全选
const handleSelectAll = (checked: boolean) => {
  if (checked) {
    setSelectedRows(mockData.map(item => item.sales_order_doc_d_id))
  } else {
    setSelectedRows([])
  }
}

// 单选行
const handleSelectRow = (id: string, checked: boolean) => {
  if (checked) {
    setSelectedRows([...selectedRows, id])
  } else {
    setSelectedRows(selectedRows.filter(rowId => rowId !== id))
  }
}
```

### 表格样式
```css
/* 表格容器 */
overflow: auto
borderRadius: md
border: 1px solid gray.200

/* 表头 */
backgroundColor: #f7fafc
borderBottom: 1px solid #e2e8f0

/* 表格行 */
borderBottom: 1px solid #f1f5f9

/* 状态标签 */
padding: 2px 6px
borderRadius: 4px
fontSize: 12px
```

## 测试步骤

1. 打开"销售订单-显示"页面
2. 验证表格正确显示在工具栏下方
3. 检查表格列标题和内容
4. 测试全选/取消全选功能
5. 测试单选行功能
6. 验证审批状态的颜色显示
7. 测试删除按钮（选中行后）
8. 验证表格滚动功能

## 预期结果

- ✅ 表格正确显示所有列
- ✅ 数据内容正确显示
- ✅ 全选/单选功能正常工作
- ✅ 审批状态颜色标识正确
- ✅ 表格支持水平滚动
- ✅ 删除按钮能获取选中行
- ✅ 表格样式美观，符合设计规范

## 后续扩展

- **分页功能**：添加分页控件
- **排序功能**：点击列标题排序
- **筛选功能**：添加筛选条件
- **编辑功能**：双击行编辑
- **导出功能**：导出选中数据
- **API集成**：连接后端API获取真实数据 