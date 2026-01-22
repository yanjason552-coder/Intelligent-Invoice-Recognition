"""
票据识别系统数据模型定义
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, String, Integer, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import field_validator, ConfigDict
import sqlalchemy as sa


# ==================== 票据文件表 ====================
class InvoiceFile(SQLModel, table=True):
    """票据文件表 - 存储上传的票据文件信息"""
    __tablename__ = "invoice_file"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    file_name: str = Field(max_length=255, description="文件名")
    file_path: str = Field(max_length=500, description="文件存储路径")
    file_size: int = Field(description="文件大小（字节）")
    file_type: str = Field(max_length=50, description="文件类型（pdf/jpg/png）")
    mime_type: str = Field(max_length=100, description="MIME类型")
    file_hash: str = Field(max_length=64, index=True, description="文件内容哈希值（SHA256）")
    upload_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="上传时间")
    uploader_id: UUID = Field(foreign_key="user.id", description="上传人ID")
    status: str = Field(default="uploaded", max_length=20, description="状态：uploaded/processing/processed/error")
    external_file_id: Optional[str] = Field(default=None, max_length=100, description="外部API返回的文件ID")
    
    # 关联关系
    invoices: list["Invoice"] = Relationship(back_populates="file")


# ==================== 票据表 ====================
class Invoice(SQLModel, table=True):
    """票据表 - 存储票据基本信息"""
    __tablename__ = "invoice"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    invoice_no: str = Field(max_length=100, index=True, description="票据编号")
    invoice_type: str = Field(max_length=50, description="票据类型（增值税发票/普通发票等）")
    invoice_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="开票日期")
    
    # 金额信息
    amount: Optional[float] = Field(default=None, sa_column=Column(Float), description="金额（不含税）")
    tax_amount: Optional[float] = Field(default=None, sa_column=Column(Float), description="税额")
    total_amount: Optional[float] = Field(default=None, sa_column=Column(Float), description="合计金额")
    currency: Optional[str] = Field(default=None, max_length=10, description="币种（如：CNY、USD等）")
    
    # 供应商和采购方信息
    supplier_name: Optional[str] = Field(default=None, max_length=200, description="供应商名称")
    supplier_tax_no: Optional[str] = Field(default=None, max_length=50, description="供应商税号")
    buyer_name: Optional[str] = Field(default=None, max_length=200, description="采购方名称")
    buyer_tax_no: Optional[str] = Field(default=None, max_length=50, description="采购方税号")
    
    # 文件关联
    file_id: UUID = Field(foreign_key="invoice_file.id", description="文件ID")
    file: Optional[InvoiceFile] = Relationship(back_populates="invoices")
    
    # 识别信息
    recognition_accuracy: Optional[float] = Field(default=None, sa_column=Column(Float), description="识别准确率")
    recognition_status: str = Field(default="pending", max_length=20, description="识别状态：pending/processing/completed/failed")
    
    # 审核信息
    review_status: str = Field(default="pending", max_length=20, description="审核状态：pending/approved/rejected")
    reviewer_id: Optional[UUID] = Field(default=None, foreign_key="user.id", description="审核人ID")
    review_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="审核时间")
    review_comment: Optional[str] = Field(default=None, sa_column=Column(Text), description="审核意见")
    
    # 元数据
    remark: Optional[str] = Field(default=None, max_length=500, description="备注")
    creator_id: UUID = Field(foreign_key="user.id", description="创建人ID")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="更新时间")
    
    # 关联关系
    recognition_results: list["RecognitionResult"] = Relationship(back_populates="invoice")
    recognition_fields: list["RecognitionField"] = Relationship(back_populates="invoice")
    review_records: list["ReviewRecord"] = Relationship(back_populates="invoice")
    items: list["InvoiceItem"] = Relationship(back_populates="invoice")
    schema_validation_records: list["SchemaValidationRecord"] = Relationship(back_populates="invoice")


# ==================== 发票行项目表 ====================
class InvoiceItem(SQLModel, table=True):
    """发票行项目表 - 存储发票识别后的行项目数据"""
    __tablename__ = "invoice_item"
    
    # 复合主键：id + invoice_no + line_no
    id: UUID = Field(foreign_key="invoice.id", description="发票ID")
    invoice_no: str = Field(max_length=100, description="发票编号")
    line_no: int = Field(description="行号（整数类型）")
    
    # 行项目字段
    name: Optional[str] = Field(default=None, max_length=500, description="项目名称")
    part_no: Optional[str] = Field(default=None, max_length=100, description="零件号")
    supplier_partno: Optional[str] = Field(default=None, max_length=100, description="供应商零件号")
    unit: Optional[str] = Field(default=None, max_length=50, description="单位")
    quantity: Optional[float] = Field(default=None, sa_column=Column(Float), description="数量")
    unit_price: Optional[float] = Field(default=None, sa_column=Column(Float), description="单价")
    amount: Optional[float] = Field(default=None, sa_column=Column(Float), description="金额")
    tax_rate: Optional[str] = Field(default=None, max_length=20, description="税率")
    tax_amount: Optional[float] = Field(default=None, sa_column=Column(Float), description="税额")
    
    # 元数据
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="更新时间")
    
    # 关联关系
    invoice: Optional["Invoice"] = Relationship(back_populates="items")
    
    # 定义复合主键
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", "invoice_no", "line_no"),
    )


# 行项目更新模型
class InvoiceItemUpdate(SQLModel):
    line_no: int = Field(description="行号")
    name: Optional[str] = Field(default=None, max_length=500)
    part_no: Optional[str] = Field(default=None, max_length=100)
    supplier_partno: Optional[str] = Field(default=None, max_length=100)
    unit: Optional[str] = Field(default=None, max_length=50)
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    tax_rate: Optional[str] = Field(default=None, max_length=20)
    tax_amount: Optional[float] = None


# 批量更新行项目请求模型
class InvoiceItemsBatchUpdate(SQLModel):
    items: list[InvoiceItemUpdate] = Field(description="行项目列表")


# ==================== 识别任务表 ====================
class RecognitionTask(SQLModel, table=True):
    """识别任务表 - 存储识别任务信息"""
    __tablename__ = "recognition_task"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_no: str = Field(max_length=100, unique=True, index=True, description="任务编号")
    invoice_id: UUID = Field(foreign_key="invoice.id", description="票据ID")
    template_id: Optional[UUID] = Field(default=None, foreign_key="template.id", description="模板ID")
    
    # 任务参数快照（JSON格式）
    params: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="任务参数快照")
    
    # 任务状态
    status: str = Field(default="pending", max_length=20, description="任务状态：pending/processing/completed/failed")
    priority: int = Field(default=0, description="优先级（数字越大优先级越高）")
    
    # 执行信息
    start_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="开始时间")
    end_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="结束时间")
    duration: Optional[float] = Field(default=None, sa_column=Column(Float), description="耗时（秒）")
    
    # 错误信息
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text), description="错误信息")
    error_code: Optional[str] = Field(default=None, max_length=50, description="错误代码")
    
    # Dify相关
    provider: str = Field(default="dify", max_length=50, description="识别服务提供商")
    request_id: Optional[str] = Field(default=None, max_length=100, index=True, description="Dify请求ID")
    trace_id: Optional[str] = Field(default=None, max_length=100, description="追踪ID")
    
    # 元数据
    operator_id: UUID = Field(foreign_key="user.id", description="操作人ID")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    
    # 关联关系
    result: Optional["RecognitionResult"] = Relationship(back_populates="task")
    schema_validation_records: list["SchemaValidationRecord"] = Relationship(back_populates="task")


# ==================== 识别结果表 ====================
class RecognitionResult(SQLModel, table=True):
    """识别结果表 - 存储识别结果"""
    __tablename__ = "recognition_result"
    model_config = ConfigDict(protected_namespaces=())
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    invoice_id: UUID = Field(foreign_key="invoice.id", description="票据ID")
    task_id: UUID = Field(foreign_key="recognition_task.id", unique=True, description="任务ID")
    
    # 识别统计
    total_fields: int = Field(default=0, description="总字段数")
    recognized_fields: int = Field(default=0, description="已识别字段数")
    accuracy: float = Field(sa_column=Column(Float), description="整体准确率")
    confidence: float = Field(sa_column=Column(Float), description="置信度")
    
    # 识别状态
    status: str = Field(default="success", max_length=20, description="状态：success/failed/partial")
    
    # 原始识别数据（JSON格式）
    raw_data: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="原始识别数据（兼容旧数据）")
    raw_payload: Optional[str] = Field(default=None, sa_column=Column(Text), description="原始响应存储（大文本/大JSON，建议落对象存储）")
    raw_response_uri: Optional[str] = Field(default=None, max_length=500, description="原始响应存储URI")
    
    # 标准化字段（系统内部统一字段结构）
    normalized_fields: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="标准化字段结构")
    
    # 模型使用统计
    model_usage: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="模型使用统计（token、耗时、费用）")
    
    # 元数据
    recognition_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="识别时间")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    
    # 关联关系
    invoice: Optional[Invoice] = Relationship(back_populates="recognition_results")
    task: Optional[RecognitionTask] = Relationship(back_populates="result")
    fields: list["RecognitionField"] = Relationship(back_populates="result")


# ==================== 识别字段表 ====================
class RecognitionField(SQLModel, table=True):
    """识别字段表 - 存储识别出的具体字段"""
    __tablename__ = "recognition_field"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    invoice_id: UUID = Field(foreign_key="invoice.id", description="票据ID")
    result_id: UUID = Field(foreign_key="recognition_result.id", description="识别结果ID")
    template_field_id: Optional[UUID] = Field(default=None, description="模板字段ID（已废弃，不再使用）")
    
    # 字段值
    field_name: str = Field(max_length=100, description="字段名称")
    field_value: Optional[str] = Field(default=None, sa_column=Column(Text), description="字段值")
    original_value: Optional[str] = Field(default=None, sa_column=Column(Text), description="原始识别值")
    
    # 识别质量
    confidence: float = Field(sa_column=Column(Float), description="置信度")
    accuracy: float = Field(sa_column=Column(Float), description="准确率")
    
    # 位置信息（JSON格式，存储坐标）
    position: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="字段位置信息")
    
    # 是否手动修正
    is_manual_corrected: bool = Field(default=False, description="是否手动修正")
    corrected_by: Optional[UUID] = Field(default=None, foreign_key="user.id", description="修正人ID")
    corrected_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="修正时间")
    
    # 元数据
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    
    # 关联关系
    invoice: Optional[Invoice] = Relationship(back_populates="recognition_fields")
    result: Optional[RecognitionResult] = Relationship(back_populates="fields")


# ==================== 审核记录表 ====================
class ReviewRecord(SQLModel, table=True):
    """审核记录表 - 存储审核记录"""
    __tablename__ = "review_record"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    invoice_id: UUID = Field(foreign_key="invoice.id", description="票据ID")
    
    # 审核信息
    review_status: str = Field(max_length=20, description="审核状态：approved/rejected")
    review_comment: Optional[str] = Field(default=None, sa_column=Column(Text), description="审核意见")
    
    # 审核人信息
    reviewer_id: UUID = Field(foreign_key="user.id", description="审核人ID")
    review_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="审核时间")
    
    # 审核详情（JSON格式，存储修改的字段）
    review_details: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="审核详情")
    
    # 关联关系
    invoice: Optional[Invoice] = Relationship(back_populates="review_records")


# ==================== 大模型配置表 ====================
class LLMConfig(SQLModel, table=True):
    """大模型配置表 - 存储SYNTAX大模型API配置"""
    __tablename__ = "llm_config"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True, description="配置名称")
    
    # SYNTAX API配置（基于Dify API规范）
    endpoint: str = Field(max_length=500, description="API端点地址（如：https://api.syntax.ai/v1）")
    api_key: str = Field(max_length=200, description="API密钥")
    app_id: Optional[str] = Field(default=None, max_length=100, description="应用ID（用于对话型应用）")
    workflow_id: Optional[str] = Field(default=None, max_length=100, description="工作流ID（用于工作流应用）")
    
    # 应用类型
    app_type: str = Field(default="workflow", max_length=20, description="应用类型：chat/workflow/completion")
    
    # 超时配置
    timeout: int = Field(default=300, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")
    
    # 状态
    is_active: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否默认配置")
    
    # 元数据
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="配置描述")
    creator_id: UUID = Field(foreign_key="user.id", description="创建人ID")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="更新时间")
    updater_id: Optional[UUID] = Field(default=None, foreign_key="user.id", description="更新人ID")


# ==================== OCR配置表（保留用于兼容） ====================
class OCRConfig(SQLModel, table=True):
    """OCR配置表 - 存储OCR配置（已废弃，保留用于兼容）"""
    __tablename__ = "ocr_config"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    config_key: str = Field(max_length=100, unique=True, index=True, description="配置键")
    config_value: str = Field(sa_column=Column(Text), description="配置值（JSON格式）")
    description: Optional[str] = Field(default=None, max_length=200, description="配置描述")
    
    # 元数据
    update_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="更新时间")
    updater_id: UUID = Field(foreign_key="user.id", description="更新人ID")


# ==================== 识别规则表 ====================
class RecognitionRule(SQLModel, table=True):
    """识别规则表 - 存储识别规则"""
    __tablename__ = "recognition_rule"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    rule_name: str = Field(max_length=100, description="规则名称")
    rule_type: str = Field(max_length=50, description="规则类型（validation/format/extract等）")
    
    # 规则定义（JSON格式）
    rule_definition: dict = Field(sa_column=Column(JSON), description="规则定义")
    
    # 应用范围
    template_id: Optional[UUID] = Field(default=None, description="应用的模板ID（null表示全局规则，已废弃）")
    field_name: Optional[str] = Field(default=None, max_length=100, description="应用的字段名（null表示模板级规则）")
    
    # 规则状态
    is_active: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=0, description="优先级")
    
    # 元数据
    remark: Optional[str] = Field(default=None, max_length=200, description="备注")
    creator_id: UUID = Field(foreign_key="user.id", description="创建人ID")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="更新时间")


# ==================== 模型配置表 ====================
class ModelConfig(SQLModel, table=True):
    """模型配置表 - 存储可用的识别模型配置"""
    __tablename__ = "model_config"
    model_config = ConfigDict(protected_namespaces=())
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True, description="模型配置名称")
    provider: str = Field(default="syntax", max_length=50, description="提供商（syntax等）")
    
    # SYNTAX配置（基于Dify API规范）
    syntax_endpoint: Optional[str] = Field(default=None, max_length=500, description="SYNTAX API endpoint")
    syntax_api_key: Optional[str] = Field(default=None, max_length=200, description="SYNTAX API key")
    syntax_app_id: Optional[str] = Field(default=None, max_length=100, description="SYNTAX app id")
    syntax_workflow_id: Optional[str] = Field(default=None, max_length=100, description="SYNTAX workflow id")
    
    # 兼容旧字段（已废弃，保留用于数据迁移）
    dify_endpoint: Optional[str] = Field(default=None, max_length=500, description="Dify endpoint（已废弃）")
    dify_api_key: Optional[str] = Field(default=None, max_length=200, description="Dify API key（已废弃）")
    dify_app_id: Optional[str] = Field(default=None, max_length=100, description="Dify app id（已废弃）")
    dify_workflow_id: Optional[str] = Field(default=None, max_length=100, description="Dify workflow id（已废弃）")
    
    # 模型信息
    model_name: str = Field(max_length=100, description="模型名称")
    model_version: Optional[str] = Field(default=None, max_length=50, description="模型版本")
    cost_level: str = Field(default="standard", max_length=20, description="成本级别（low/standard/high）")
    
    # 默认配置
    default_mode: str = Field(default="llm_extract", max_length=50, description="默认识别方式")
    allowed_modes: list[str] = Field(default_factory=list, sa_column=Column(JSON), description="允许的识别方式列表")
    default_schema_id: Optional[UUID] = Field(default=None, foreign_key="output_schema.id", description="默认输出结构标准ID")
    
    # 权限控制
    allowed_user_ids: Optional[list[UUID]] = Field(default=None, sa_column=Column(JSON), description="允许使用的用户ID列表（null表示所有用户）")
    allowed_role_ids: Optional[list[UUID]] = Field(default=None, sa_column=Column(JSON), description="允许使用的角色ID列表（null表示所有角色）")
    
    # 状态
    is_active: bool = Field(default=True, description="是否启用")
    
    # 元数据
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="描述")
    creator_id: UUID = Field(foreign_key="user.id", description="创建人ID")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="更新时间")


# ==================== 输出结构标准表 ====================
class OutputSchema(SQLModel, table=True):
    """输出结构标准表 - 存储不同业务字段集合的schema定义"""
    __tablename__ = "output_schema"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True, description="Schema名称")
    version: str = Field(default="1.0.0", max_length=20, description="版本号")

    # Schema定义（JSON格式，定义字段结构）
    schema_definition: dict = Field(sa_column=Column(JSON), description="Schema定义（字段列表、类型、验证规则等）")

    # 状态
    is_active: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否默认schema")

    # 元数据
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="描述")
    creator_id: UUID = Field(foreign_key="user.id", description="创建人ID")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="更新时间")

    # 关联关系
    validation_records: list["SchemaValidationRecord"] = Relationship(back_populates="schema")


# ==================== Schema验证记录表 ====================
class SchemaValidationRecord(SQLModel, table=True):
    """Schema验证记录表 - 存储Schema验证的结果和修复记录"""
    __tablename__ = "schema_validation_record"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    invoice_id: UUID = Field(foreign_key="invoice.id", description="发票ID")
    task_id: UUID = Field(foreign_key="recognition_task.id", description="识别任务ID")
    schema_id: Optional[UUID] = Field(default=None, foreign_key="output_schema.id", description="Schema ID")

    # 验证结果
    is_valid: bool = Field(description="是否验证通过")
    error_count: int = Field(default=0, description="错误数量")
    warning_count: int = Field(default=0, description="警告数量")
    validation_errors: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="验证错误详情")
    validation_warnings: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="验证警告详情")

    # 修复结果
    repair_attempted: bool = Field(default=False, description="是否尝试修复")
    repair_success: bool = Field(default=False, description="修复是否成功")
    repair_actions: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="修复动作详情")

    # 降级结果
    fallback_type: Optional[str] = Field(default=None, max_length=20, description="降级类型：partial/empty/text/error")
    fallback_data: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="降级返回数据")

    # 性能指标
    validation_time_ms: float = Field(sa_column=Column(Float), description="验证耗时(毫秒)")
    repair_time_ms: Optional[float] = Field(default=None, sa_column=Column(Float), description="修复耗时(毫秒)")
    total_time_ms: float = Field(sa_column=Column(Float), description="总耗时(毫秒)")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")

    # 关联关系
    invoice: Optional[Invoice] = Relationship(back_populates="schema_validation_records")
    task: Optional[RecognitionTask] = Relationship(back_populates="schema_validation_records")
    schema: Optional[OutputSchema] = Relationship(back_populates="validation_records")


# ==================== API 请求/响应模型 ====================

# 票据创建模型
class InvoiceCreate(SQLModel):
    invoice_no: str = Field(max_length=100, description="票据编号")
    invoice_type: str = Field(max_length=50, description="票据类型")
    file_id: UUID = Field(description="文件ID")
    template_id: Optional[UUID] = Field(default=None, description="模板ID")
    remark: Optional[str] = Field(default=None, max_length=500, description="备注")
    
    @field_validator('invoice_no')
    @classmethod
    def validate_invoice_no(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("票据编号不能为空")
        if len(v) > 100:
            raise ValueError("票据编号长度不能超过100个字符")
        return v.strip()
    
    @field_validator('invoice_type')
    @classmethod
    def validate_invoice_type(cls, v: str) -> str:
        allowed_types = [
            "增值税专用发票",
            "增值税普通发票",
            "增值税电子普通发票",
            "增值税电子专用发票",
            "其他"
        ]
        if v not in allowed_types:
            raise ValueError(f"票据类型必须是以下之一: {', '.join(allowed_types)}")
        return v


# 票据更新模型
class InvoiceUpdate(SQLModel):
    invoice_no: Optional[str] = Field(default=None, max_length=100)
    invoice_type: Optional[str] = Field(default=None, max_length=50)
    invoice_date: Optional[datetime] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = Field(default=None, max_length=10)
    supplier_name: Optional[str] = Field(default=None, max_length=200)
    supplier_tax_no: Optional[str] = Field(default=None, max_length=50)
    buyer_name: Optional[str] = Field(default=None, max_length=200)
    buyer_tax_no: Optional[str] = Field(default=None, max_length=50)
    review_status: Optional[str] = Field(default=None, max_length=20)
    review_comment: Optional[str] = None
    remark: Optional[str] = Field(default=None, max_length=500)
    
    @field_validator('amount', 'tax_amount', 'total_amount')
    @classmethod
    def validate_amount(cls, v: float | None) -> float | None:
        if v is not None:
            if v < 0:
                raise ValueError("金额不能为负数")
            if v > 999999999.99:
                raise ValueError("金额超出允许范围")
        return v
    
    @field_validator('review_status')
    @classmethod
    def validate_review_status(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = ["pending", "approved", "rejected"]
            if v not in allowed:
                raise ValueError(f"审核状态必须是以下之一: {', '.join(allowed)}")
        return v


# 票据响应模型
class InvoiceResponse(SQLModel):
    id: UUID
    invoice_no: str
    invoice_type: str
    invoice_date: Optional[datetime]
    amount: Optional[float]
    tax_amount: Optional[float]
    total_amount: Optional[float]
    currency: Optional[str]
    supplier_name: Optional[str]
    supplier_tax_no: Optional[str]
    buyer_name: Optional[str]
    buyer_tax_no: Optional[str]
    recognition_accuracy: Optional[float]
    recognition_status: str
    review_status: str
    create_time: datetime


# 识别任务参数模型
class RecognitionTaskParams(SQLModel):
    """识别任务参数"""
    model_config = ConfigDict(protected_namespaces=())
    model_config_id: UUID = Field(description="模型配置ID")
    recognition_mode: str = Field(description="识别方式：llm_extract/ocr_llm/template")
    template_strategy: str = Field(default="auto", description="模板策略：auto/fixed/none")
    template_id: Optional[UUID] = Field(default=None, description="模板ID（已废弃，不再使用）")
    template_version: Optional[str] = Field(default=None, description="模板版本")
    output_schema_id: Optional[UUID] = Field(default=None, description="输出字段标准ID")
    language: str = Field(default="zh-CN", description="语言：zh-CN/auto")
    confidence_threshold: float = Field(default=0.8, ge=0, le=1, description="置信度阈值")
    page_range: str = Field(default="all", description="页范围：all/1st/custom")
    enhance_options: str = Field(default="auto", description="图像增强策略：auto/none/strong")
    callback_url: Optional[str] = Field(default=None, description="完成回调URL")


# 识别任务创建模型
class RecognitionTaskCreate(SQLModel):
    invoice_id: UUID = Field(description="票据ID")
    params: RecognitionTaskParams = Field(description="任务参数")
    priority: int = Field(default=0, ge=0, le=100, description="优先级")


# 批量创建任务模型
class RecognitionTaskBatchCreate(SQLModel):
    uploaded_file_ids: list[UUID] = Field(description="文件ID列表")
    params: RecognitionTaskParams = Field(description="任务参数（同一批使用同一参数）")


# 识别任务响应模型
class RecognitionTaskResponse(SQLModel):
    model_config = ConfigDict(protected_namespaces=())
    id: UUID
    task_no: str
    invoice_id: UUID
    template_id: Optional[UUID]
    params: Optional[dict]
    status: str
    provider: str
    recognition_mode: Optional[str] = None
    model_name: Optional[str] = None
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    create_time: datetime


# 识别结果响应模型
class RecognitionResultResponse(SQLModel):
    id: UUID
    invoice_id: UUID
    total_fields: int
    recognized_fields: int
    accuracy: float
    confidence: float
    status: str
    recognition_time: datetime


# ==================== 票据文件列表响应模型 ====================
class InvoiceFileListItem(SQLModel):
    """
    票据文件列表项 - 用于列表展示和状态追踪
    包含文件、票据、识别、审核等综合信息
    """
    # 文件基本信息
    file_id: UUID = Field(description="文件ID")
    file_name: str = Field(description="文件名")
    file_size: int = Field(description="文件大小（字节）")
    file_type: str = Field(description="文件类型（pdf/jpg/png）")
    file_hash: Optional[str] = Field(default=None, description="文件哈希值")
    upload_time: datetime = Field(description="上传时间")
    
    # 票据基本信息
    invoice_id: UUID = Field(description="票据ID")
    invoice_no: str = Field(description="票据编号")
    invoice_type: str = Field(description="票据类型")
    invoice_date: Optional[datetime] = Field(default=None, description="开票日期")
    
    # 金额信息
    amount: Optional[float] = Field(default=None, description="金额（不含税）")
    tax_amount: Optional[float] = Field(default=None, description="税额")
    total_amount: Optional[float] = Field(default=None, description="合计金额")
    
    # 供应商和采购方信息
    supplier_name: Optional[str] = Field(default=None, description="供应商名称")
    supplier_tax_no: Optional[str] = Field(default=None, description="供应商税号")
    buyer_name: Optional[str] = Field(default=None, description="采购方名称")
    buyer_tax_no: Optional[str] = Field(default=None, description="采购方税号")
    
    # 状态信息
    file_status: str = Field(description="文件状态：uploaded/processing/processed/error")
    recognition_status: str = Field(description="识别状态：pending/processing/completed/failed")
    review_status: str = Field(description="审核状态：pending/approved/rejected")
    
    # 识别信息
    recognition_accuracy: Optional[float] = Field(default=None, description="识别准确率")
    recognition_time: Optional[datetime] = Field(default=None, description="识别完成时间")
    recognition_task_count: int = Field(default=0, description="识别任务数量")
    last_recognition_task_id: Optional[UUID] = Field(default=None, description="最新识别任务ID")
    
    # 审核信息
    reviewer_name: Optional[str] = Field(default=None, description="审核人姓名")
    review_time: Optional[datetime] = Field(default=None, description="审核时间")
    review_comment: Optional[str] = Field(default=None, description="审核意见")
    
    # 用户信息
    uploader_name: Optional[str] = Field(default=None, description="上传人姓名")
    creator_name: Optional[str] = Field(default=None, description="创建人姓名")
    
    # 模板信息
    template_id: Optional[UUID] = Field(default=None, description="使用的模板ID")
    template_name: Optional[str] = Field(default=None, description="模板名称")
    
    # 时间信息
    create_time: datetime = Field(description="创建时间")
    update_time: Optional[datetime] = Field(default=None, description="更新时间")
    
    # 备注
    remark: Optional[str] = Field(default=None, description="备注")


# ==================== 模板相关模型 ====================

class Template(SQLModel, table=True):
    """模板表 - 存储业务模板定义"""
    __tablename__ = "template"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True, description="模板名称")
    template_type: str = Field(max_length=50, index=True, description="模板类型（业务类型：增值税发票/采购订单等）")
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="模板描述")
    
    # 状态
    status: str = Field(default="enabled", max_length=20, description="状态：enabled/disabled/deprecated")
    
    # 版本管理
    current_version_id: Optional[UUID] = Field(default=None, foreign_key="template_version.id", description="当前版本ID")
    
    # 统计信息
    accuracy: Optional[float] = Field(default=None, sa_column=Column(Float), description="准确率（统计值）")
    
    # 元数据
    creator_id: UUID = Field(foreign_key="user.id", description="创建人ID")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    update_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="更新时间")
    
    # 关联关系
    versions: list["TemplateVersion"] = Relationship(
        back_populates="template",
        sa_relationship_kwargs={"foreign_keys": "[TemplateVersion.template_id]"}
    )
    current_version: Optional["TemplateVersion"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Template.current_version_id]",
            "remote_side": "TemplateVersion.id"
        }
    )


class TemplateVersion(SQLModel, table=True):
    """模板版本表 - 存储模板的版本信息"""
    __tablename__ = "template_version"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_id: UUID = Field(foreign_key="template.id", description="模板ID")
    version: str = Field(max_length=50, index=True, description="版本号（如：v1.0.0）")
    
    # 状态
    status: str = Field(default="draft", max_length=20, description="状态：draft/published/deprecated")
    
    # Schema快照（发布时生成，不可变）
    schema_snapshot: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="Schema快照（发布时生成）")
    
    # 统计信息
    accuracy: Optional[float] = Field(default=None, sa_column=Column(Float), description="准确率（从评估回写）")
    
    # 乐观锁
    etag: Optional[str] = Field(default=None, max_length=100, description="版本标签（用于乐观锁）")
    
    # 草稿锁定
    locked_by: Optional[UUID] = Field(default=None, foreign_key="user.id", description="锁定人ID（草稿编辑锁）")
    locked_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="锁定时间")
    
    # 元数据
    created_by: UUID = Field(foreign_key="user.id", description="创建人ID")
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    published_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="发布时间")
    deprecated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="废弃时间")
    
    # 关联关系
    template: Optional[Template] = Relationship(
        back_populates="versions",
        sa_relationship_kwargs={"foreign_keys": "[TemplateVersion.template_id]"}
    )
    fields: list["TemplateField"] = Relationship(back_populates="template_version")


class TemplateField(SQLModel, table=True):
    """模板字段表 - 存储模板字段定义"""
    __tablename__ = "template_field"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_id: UUID = Field(foreign_key="template.id", description="模板ID")
    template_version_id: UUID = Field(foreign_key="template_version.id", description="模板版本ID")
    
    # 字段标识
    field_key: str = Field(max_length=100, index=True, description="字段标识（英文/下划线，如 invoice_no）")
    field_code: str = Field(max_length=50, description="字段代码（兼容字段，与field_key相同）")
    field_name: str = Field(max_length=200, description="字段名称（中文展示，如 发票号码）")
    
    # 字段类型
    data_type: str = Field(max_length=50, description="数据类型：string/number/date/datetime/boolean/enum/object/array")
    field_type: str = Field(max_length=20, description="字段类型（兼容字段，与data_type相同）")
    
    # 必填与默认值
    is_required: bool = Field(default=False, description="是否必填")
    required: bool = Field(default=False, description="是否必填（兼容字段）")
    default_value: Optional[str] = Field(default=None, sa_column=Column(Text), description="默认值")
    
    # 描述与示例
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="字段说明")
    example: Optional[str] = Field(default=None, sa_column=Column(Text), description="示例值")
    
    # 校验规则（JSON格式）
    validation: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="校验规则（regex/min/max/length等）")
    validation_rules: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="校验规则（兼容字段）")
    
    # 格式化规则（JSON格式）
    normalize: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="格式化规则（trim/upper/lower等）")
    
    # LLM提示
    prompt_hint: Optional[str] = Field(default=None, sa_column=Column(Text), description="对LLM的补充提示")
    confidence_threshold: Optional[float] = Field(default=None, sa_column=Column(Float), description="字段级置信度阈值")
    
    # 映射
    canonical_field: Optional[str] = Field(default=None, max_length=100, description="映射到系统通用字段")
    
    # 嵌套字段支持
    parent_field_id: Optional[UUID] = Field(default=None, foreign_key="template_field.id", description="父字段ID（用于嵌套结构）")
    
    # 废弃标记
    deprecated: bool = Field(default=False, description="是否废弃")
    deprecated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime), description="废弃时间")
    
    # 排序
    position: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="位置信息（JSON格式，兼容字段）")
    display_order: Optional[int] = Field(default=None, description="显示顺序")
    sort_order: int = Field(default=0, description="排序顺序")
    
    # 元数据
    remark: Optional[str] = Field(default=None, sa_column=Column(Text), description="备注")
    create_time: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime), description="创建时间")
    
    # 关联关系
    template_version: Optional[TemplateVersion] = Relationship(back_populates="fields")
    parent_field: Optional["TemplateField"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[TemplateField.parent_field_id]",
            "remote_side": "TemplateField.id"
        }
    )
    sub_fields: list["TemplateField"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[TemplateField.parent_field_id]",
            "overlaps": "parent_field"
        }
    )

