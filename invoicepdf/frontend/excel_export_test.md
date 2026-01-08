# Excel导出功能测试

## 功能描述

### 导出功能
- **触发方式**：点击工具栏中的导出按钮（紫色下载图标）
- **文件格式**：Excel (.xlsx)
- **导出内容**：选中行或全部数据
- **文件命名**：`销售订单数据_YYYY-MM-DDTHH-MM-SS.xlsx`

### Excel文件结构

#### 第一行：字段名
```
sales_order_doc_d_id | customer_full_name | doc_id | doc_no | sequence | doc_date | ...
```

#### 第二行：字段注释
```
物理主键 | 客户全名 | 订单类型 | 订单单号 | 订单行号 | 订单日期 | ...
```

#### 第三行开始：数据内容
```
1 | 客户A | SO001 | 2024001 | 0010 | 2024-01-15 | ...
2 | 客户B | SO002 | 2024002 | 0010 | 2024-01-16 | ...
```

## 技术实现

### 依赖库
```json
{
  "xlsx": "^0.18.5",
  "file-saver": "^2.0.5",
  "@types/file-saver": "^2.0.7"
}
```

### 核心代码
```typescript
// 字段定义
const fieldDefinitions = [
  { field: 'sales_order_doc_d_id', label: '物理主键' },
  { field: 'customer_full_name', label: '客户全名' },
  // ... 所有字段
]

// 导出函数
const handleExport = () => {
  // 1. 确定导出数据（选中行或全部）
  const dataToExport = selectedRows.length > 0 
    ? mockData.filter(item => selectedRows.includes(item.sales_order_doc_d_id))
    : mockData

  // 2. 创建工作簿
  const workbook = XLSX.utils.book_new()
  
  // 3. 准备Excel数据
  const excelData = []
  excelData.push(fieldNames)      // 第一行：字段名
  excelData.push(fieldLabels)     // 第二行：字段注释
  dataToExport.forEach(item => {  // 第三行开始：数据
    const row = fieldDefinitions.map(def => item[def.field])
    excelData.push(row)
  })
  
  // 4. 创建工作表并设置列宽
  const worksheet = XLSX.utils.aoa_to_sheet(excelData)
  worksheet['!cols'] = fieldDefinitions.map(() => ({ width: 15 }))
  
  // 5. 导出文件
  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
  const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  saveAs(blob, fileName)
}
```

## 测试步骤

### 1. 基本导出测试
1. 打开"销售订单-显示"页面
2. 不选择任何行，直接点击导出按钮
3. 验证浏览器下载了Excel文件
4. 打开Excel文件，检查内容结构

### 2. 选择性导出测试
1. 选择表格中的某些行（使用复选框）
2. 点击导出按钮
3. 验证只导出了选中的行数据

### 3. 文件内容验证
1. 检查Excel文件的第一行是否为字段名
2. 检查Excel文件的第二行是否为字段注释
3. 检查从第三行开始是否为表格数据
4. 验证数据内容与表格显示一致

### 4. 文件格式验证
1. 检查文件扩展名为.xlsx
2. 检查文件名包含时间戳
3. 验证文件可以在Excel中正常打开

## 预期结果

- ✅ 点击导出按钮触发文件下载
- ✅ 文件名格式正确（包含时间戳）
- ✅ Excel文件包含三行结构：字段名、注释、数据
- ✅ 选择性导出只包含选中的行
- ✅ 全部导出包含所有数据
- ✅ 文件可以在Excel中正常打开和编辑
- ✅ 列宽设置合理，内容可读

## 错误处理

- **无数据导出**：显示"没有数据可导出"提示
- **导出失败**：显示"导出失败，请重试"提示
- **浏览器兼容性**：支持现代浏览器的文件下载功能

## 用户体验

- **直观操作**：点击图标即可导出
- **灵活选择**：支持全部导出或选择性导出
- **文件命名**：自动生成带时间戳的文件名
- **格式规范**：符合Excel标准格式
- **内容完整**：包含字段名、注释和完整数据 