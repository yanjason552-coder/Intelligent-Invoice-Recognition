"""
SYNTAX服务 - 用于调用SYNTAX API进行票据识别
"""

import logging
import httpx
import json
from typing import Optional, Dict, Any
from uuid import UUID
from pathlib import Path
from sqlmodel import Session, select
from datetime import datetime
try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

from app.models.models_invoice import (
    RecognitionTask, RecognitionResult, Invoice, InvoiceFile,
    ModelConfig, OutputSchema, LLMConfig, InvoiceItem
)

# 配置日志 - 确保日志级别为INFO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SyntaxService:
    """SYNTAX服务类（基于Dify API规范）"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def process_task(self, task_id: UUID) -> bool:
        """
        处理识别任务（同步执行）
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            task = self.session.get(RecognitionTask, task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return False
            
            if not task.params:
                logger.error(f"任务参数不存在: {task_id}")
                self._mark_task_failed(task, "DIFY_BAD_PARAMS", "任务参数不存在")
                return False
            
            # 获取模型配置
            model_config_id = task.params.get("model_config_id")
            if not model_config_id:
                logger.error(f"任务参数中缺少model_config_id: {task_id}")
                self._mark_task_failed(task, "DIFY_BAD_PARAMS", "任务参数中缺少model_config_id")
                return False
            
            model_config = self.session.get(ModelConfig, UUID(model_config_id))
            if not model_config:
                logger.error(f"模型配置不存在: {model_config_id}")
                self._mark_task_failed(task, "DIFY_BAD_PARAMS", "模型配置不存在")
                return False
            
            # 获取文件信息
            invoice = self.session.get(Invoice, task.invoice_id)
            if not invoice:
                logger.error(f"票据不存在: {task.invoice_id}")
                self._mark_task_failed(task, "FILE_NOT_FOUND", "票据不存在")
                return False
            
            file = self.session.get(InvoiceFile, invoice.file_id)
            if not file:
                logger.error(f"文件不存在: {invoice.file_id}")
                self._mark_task_failed(task, "FILE_NOT_FOUND", "文件不存在")
                return False
            
            if not Path(file.file_path).exists():
                logger.error(f"文件路径不存在: {file.file_path}")
                self._mark_task_failed(task, "FILE_NOT_FOUND", "文件路径不存在")
                return False
            
            # 调用Dify API
            result = self._call_dify_api(task, model_config, file)
            
            if result["success"]:
                # 保存识别结果
                self._save_result(task, invoice, result["data"])
                self._mark_task_completed(task)
                return True
            else:
                # 标记任务失败
                error_code = result.get("error_code", "DIFY_ERROR")
                error_message = result.get("error_message", "识别失败")
                self._mark_task_failed(task, error_code, error_message)
                return False
                
        except Exception as e:
            logger.error(f"处理任务失败: {task_id}, 错误: {str(e)}", exc_info=True)
            task = self.session.get(RecognitionTask, task_id)
            if task:
                self._mark_task_failed(task, "INTERNAL_ERROR", str(e))
            return False
    
    def _call_dify_api(
        self,
        task: RecognitionTask,
        model_config: ModelConfig,
        file: InvoiceFile
    ) -> Dict[str, Any]:
        """
        调用SYNTAX API（使用workflows/run接口）
        
        Args:
            task: 识别任务
            model_config: 模型配置
            file: 文件信息
            
        Returns:
            dict: 包含success、data或error_code、error_message
        """
        try:
            # 获取API配置（优先使用syntax_*字段，兼容dify_*字段）
            endpoint = model_config.syntax_endpoint or model_config.dify_endpoint
            api_key = model_config.syntax_api_key or model_config.dify_api_key
            
            if not endpoint:
                return {
                    "success": False,
                    "error_code": "API_CONFIG_ERROR",
                    "error_message": "API endpoint未配置"
                }
            
            if not api_key:
                return {
                    "success": False,
                    "error_code": "API_AUTH_ERROR",
                    "error_message": "API key未配置"
                }
            
            # 检查是否有外部文件ID
            logger.info("--- 检查文件信息 ---")
            logger.info(f"文件ID: {file.id}")
            logger.info(f"文件名: {file.file_name}")
            logger.info(f"文件类型: {file.file_type}")
            logger.info(f"MIME类型: {file.mime_type}")
            logger.info(f"外部文件ID (external_file_id): {file.external_file_id}")
            
            if not file.external_file_id:
                logger.error("文件缺少外部文件ID，无法调用外部API")
                return {
                    "success": False,
                    "error_code": "FILE_ID_ERROR",
                    "error_message": "文件缺少外部文件ID，请使用模型配置上传"
                }
            
            # 根据文件类型确定type
            file_type_lower = file.file_type.lower() if file.file_type else ""
            if file_type_lower == "pdf":
                file_type_value = "document"
            elif file_type_lower in ["jpg", "jpeg", "png", "gif", "bmp"]:
                file_type_value = "image"
            else:
                # 默认根据mime_type判断
                if file.mime_type and "pdf" in file.mime_type.lower():
                    file_type_value = "document"
                elif file.mime_type and "image" in file.mime_type.lower():
                    file_type_value = "image"
                else:
                    file_type_value = "document"  # 默认使用document
            
            logger.info(f"文件类型判断结果: {file_type_value}")
            
            # 获取用户信息（用于user字段）
            user_id = f"user_{task.operator_id}"
            logger.info(f"用户ID: {user_id}")
            
            # 构建请求报文（使用external_file_id作为upload_file_id）
            endpoint_clean = endpoint.rstrip('/')
            url = f"{endpoint_clean}/workflows/run"
            
            payload = {
                "inputs": {
                    "InvoiceFile": {
                        "transfer_method": "local_file",
                        "type": file_type_value,
                        "upload_file_id": file.external_file_id  # 使用invoice_file表中的external_file_id
                    }
                },
                "response_mode": "blocking",
                "user": user_id
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info("=" * 80)
            logger.info("=== 调用SYNTAX API ===")
            logger.info(f"URL: {url}")
            logger.info(f"请求头: {json.dumps({k: ('***' if k.lower() == 'authorization' else v) for k, v in headers.items()}, ensure_ascii=False)}")
            logger.info(f"请求报文: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            logger.info(f"使用的external_file_id: {file.external_file_id}")
            logger.info("=" * 80)
            
            # 发送请求
            start_time = datetime.now()
            try:
                with httpx.Client(timeout=300.0) as client:  # 5分钟超时
                    logger.info("开始发送HTTP请求...")
                    response = client.post(url, json=payload, headers=headers)
                    elapsed_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info("=" * 80)
                    logger.info("=== SYNTAX API 响应 ===")
                    logger.info(f"HTTP状态码: {response.status_code}")
                    logger.info(f"响应时间: {elapsed_time:.2f} 秒")
                    logger.info(f"响应头: {dict(response.headers)}")
                    
                    # 检查HTTP状态码 - 只有2xx才认为是成功
                    status_code = response.status_code
                    logger.info(f"HTTP状态码: {status_code}")
                    
                    # 如果HTTP状态码不是2xx，直接返回失败
                    if not (200 <= status_code < 300):
                        logger.error("=" * 80)
                        logger.error("=== SYNTAX API 调用失败 (HTTP状态码非2xx) ===")
                        logger.error(f"HTTP状态码: {status_code}")
                        logger.error(f"响应时间: {elapsed_time:.2f} 秒")
                        try:
                            error_body = response.json()
                            logger.error(f"错误响应体: {json.dumps(error_body, ensure_ascii=False, indent=2)}")
                            error_message = error_body.get("message") or error_body.get("error") or f"HTTP错误: {status_code}"
                        except:
                            logger.error(f"错误响应文本: {response.text[:1000]}")
                            error_message = f"HTTP错误: {status_code}"
                        logger.error("=" * 80)
                        
                        # 根据状态码返回相应的错误信息
                        if status_code == 401:
                            return {
                                "success": False,
                                "error_code": "DIFY_AUTH_ERROR",
                                "error_message": "Dify认证失败"
                            }
                        elif status_code == 429:
                            return {
                                "success": False,
                                "error_code": "DIFY_RATE_LIMIT",
                                "error_message": "Dify请求频率限制"
                            }
                        else:
                            return {
                                "success": False,
                                "error_code": "DIFY_HTTP_ERROR",
                                "error_message": error_message
                            }
                    
                    # HTTP状态码为2xx，继续处理响应
                    logger.info("HTTP状态码为2xx，继续处理响应")
                    
                    # 尝试解析响应
                    try:
                        result = response.json()
                        logger.info("响应类型: JSON")
                        logger.info(f"完整响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        
                        # 提取关键信息
                        if isinstance(result, dict):
                            logger.info("--- 响应关键字段 ---")
                            if "id" in result:
                                logger.info(f"响应ID: {result['id']}")
                            if "request_id" in result:
                                logger.info(f"请求ID: {result['request_id']}")
                            if "trace_id" in result:
                                logger.info(f"追踪ID: {result['trace_id']}")
                            if "data" in result:
                                logger.info(f"数据字段: {type(result['data'])}")
                                if isinstance(result['data'], dict):
                                    logger.info(f"数据内容: {json.dumps(result['data'], ensure_ascii=False, indent=2)}")
                            if "outputs" in result:
                                logger.info(f"输出字段: {type(result['outputs'])}")
                                if isinstance(result['outputs'], dict):
                                    logger.info(f"输出内容: {json.dumps(result['outputs'], ensure_ascii=False, indent=2)}")
                            if "answer" in result:
                                logger.info(f"答案字段: {result['answer'][:200]}...")  # 只显示前200字符
                            if "error" in result:
                                logger.error(f"错误信息: {result['error']}")
                            if "message" in result:
                                logger.info(f"消息: {result['message']}")
                            if "status" in result:
                                logger.info(f"状态: {result['status']}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"响应不是有效的JSON格式: {str(e)}")
                        logger.info(f"原始响应文本: {response.text[:1000]}")  # 只显示前1000字符
                        result = {"raw_text": response.text}
                    
            except httpx.HTTPStatusError as e:
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.error("=" * 80)
                logger.error("=== SYNTAX API 调用失败 (HTTP错误) ===")
                logger.error(f"HTTP状态码: {e.response.status_code}")
                logger.error(f"响应时间: {elapsed_time:.2f} 秒")
                logger.error(f"错误响应头: {dict(e.response.headers)}")
                try:
                    error_body = e.response.json()
                    logger.error(f"错误响应体: {json.dumps(error_body, ensure_ascii=False, indent=2)}")
                except:
                    logger.error(f"错误响应文本: {e.response.text[:1000]}")
                logger.error("=" * 80)
                raise
            except httpx.TimeoutException:
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.error("=" * 80)
                logger.error("=== SYNTAX API 调用超时 ===")
                logger.error(f"超时时间: {elapsed_time:.2f} 秒")
                logger.error("=" * 80)
                raise
            except Exception as e:
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.error("=" * 80)
                logger.error("=== SYNTAX API 调用异常 ===")
                logger.error(f"异常类型: {type(e).__name__}")
                logger.error(f"异常信息: {str(e)}")
                logger.error(f"响应时间: {elapsed_time:.2f} 秒")
                logger.error("=" * 80)
                raise
            
            logger.info("=" * 80)
            logger.info("=== SYNTAX API 调用成功 ===")
            logger.info("=" * 80)
            
            # 解析响应并返回
            logger.info("--- 解析响应数据 ---")
            normalized_fields = self._normalize_response(result, task.params)
            logger.info(f"标准化后的字段数量: {len(normalized_fields)}")
            logger.info(f"标准化后的字段: {json.dumps(normalized_fields, ensure_ascii=False, indent=2)}")
            
            response_data = {
                "raw_payload": json.dumps(result, ensure_ascii=False),
                "normalized_fields": normalized_fields,
                "model_usage": result.get("usage", {}),
                "request_id": result.get("id") or result.get("request_id"),
                "trace_id": result.get("trace_id"),
                "full_response": result  # 保存完整响应用于后续解析
            }
            
            logger.info(f"提取的request_id: {response_data['request_id']}")
            logger.info(f"提取的trace_id: {response_data['trace_id']}")
            logger.info(f"模型使用情况: {json.dumps(response_data['model_usage'], ensure_ascii=False)}")
            logger.info(f"原始响应大小: {len(response_data['raw_payload'])} 字符")
            
            logger.info("=" * 80)
            logger.info("=== 响应解析完成，准备返回 ===")
            logger.info("=" * 80)
            
            return {
                "success": True,
                "data": response_data
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {
                    "success": False,
                    "error_code": "DIFY_AUTH_ERROR",
                    "error_message": "Dify认证失败"
                }
            elif e.response.status_code == 429:
                return {
                    "success": False,
                    "error_code": "DIFY_RATE_LIMIT",
                    "error_message": "Dify请求频率限制"
                }
            else:
                return {
                    "success": False,
                    "error_code": "DIFY_HTTP_ERROR",
                    "error_message": f"HTTP错误: {e.response.status_code}"
                }
        except httpx.TimeoutException:
            return {
                "success": False,
                "error_code": "DIFY_TIMEOUT",
                "error_message": "Dify请求超时"
            }
        except Exception as e:
            logger.error(f"调用Dify API失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error_code": "DIFY_ERROR",
                "error_message": str(e)
            }
    
    def _normalize_response(self, syntax_response: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        将SYNTAX API响应转换为系统内部统一字段结构
        
        Args:
            syntax_response: SYNTAX API原始响应
            params: 任务参数
            
        Returns:
            dict: 标准化字段结构
        """
        try:
            # 获取输出schema
            schema_id = params.get("output_schema_id") if params else None
            if schema_id:
                schema = self.session.get(OutputSchema, UUID(schema_id))
                if schema and schema.schema_definition:
                    # 根据schema定义映射字段
                    return self._map_fields_by_schema(syntax_response, schema.schema_definition)
            
            # 默认映射：尝试从SYNTAX响应中提取常见字段
            normalized = {}
            
            # 尝试从不同可能的路径提取数据
            # SYNTAX API可能返回的数据结构：
            # 1. outputs字段（工作流输出）
            # 2. data字段
            # 3. answer字段（文本回答）
            
            outputs = syntax_response.get("outputs", {})
            data = syntax_response.get("data", {})
            answer = syntax_response.get("answer", "")
            
            # 优先使用outputs（工作流输出）
            if isinstance(outputs, dict):
                normalized = outputs.copy()
            elif isinstance(data, dict):
                # 使用data字段
                normalized = data.copy()
            elif isinstance(answer, str):
                # 尝试解析JSON字符串
                try:
                    parsed = json.loads(answer)
                    if isinstance(parsed, dict):
                        normalized = parsed
                except:
                    # 如果不是JSON，可能是纯文本，尝试提取关键信息
                    pass
            
            # 标准化常见字段名
            field_mapping = {
                "invoice_code": "invoice_code",
                "invoice_no": "invoice_no",
                "invoice_number": "invoice_no",
                "invoice_date": "invoice_date",
                "date": "invoice_date",
                "amount": "amount",
                "total_amount": "total_amount",
                "tax_amount": "tax_amount",
                "supplier_name": "supplier_name",
                "buyer_name": "buyer_name",
                "supplier_tax_no": "supplier_tax_no",
                "buyer_tax_no": "buyer_tax_no",
                "invoice_type": "invoice_type"
            }
            
            result = {}
            for key, value in normalized.items():
                standard_key = field_mapping.get(key, key)
                result[standard_key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"标准化响应失败: {str(e)}", exc_info=True)
            return {}
    
    def _map_fields_by_schema(self, dify_response: Dict[str, Any], schema_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据schema定义映射字段
        
        Args:
            dify_response: Dify响应
            schema_definition: Schema定义
            
        Returns:
            dict: 映射后的字段
        """
        # TODO: 实现根据schema定义进行字段映射
        # 这里可以根据schema_definition中的字段定义，从dify_response中提取对应字段
        return self._normalize_response(dify_response, {})
    
    def _save_result(
        self,
        task: RecognitionTask,
        invoice: Invoice,
        result_data: Dict[str, Any]
    ):
        """
        保存识别结果并更新invoice表
        
        Args:
            task: 识别任务
            invoice: 票据
            result_data: 识别结果数据
        """
        try:
            logger.info("=" * 80)
            logger.info("=== 开始保存识别结果并更新invoice表 ===")
            logger.info(f"任务ID: {task.id}")
            logger.info(f"票据ID: {invoice.id}")
            
            # 解析返回结果
            full_response = result_data.get("full_response", {})
            normalized_fields = result_data.get("normalized_fields", {})
            
            logger.info(f"完整响应: {json.dumps(full_response, ensure_ascii=False, indent=2)}")
            logger.info(f"标准化字段: {json.dumps(normalized_fields, ensure_ascii=False, indent=2)}")
            
            # 从响应中提取字段并更新invoice表
            # 根据新的字段映射关系解析字段
            if isinstance(full_response, dict):
                # 优先从outputs字段提取数据（工作流输出）
                outputs = full_response.get("outputs", {})
                data = full_response.get("data", {})
                
                # 尝试多种路径提取数据
                source_data = {}
                
                # 路径1: data.outputs.text (工作流返回的常见格式)
                if isinstance(data, dict):
                    data_outputs = data.get("outputs", {})
                    if isinstance(data_outputs, dict):
                        # 检查是否有text字段
                        if "text" in data_outputs and isinstance(data_outputs["text"], dict):
                            source_data = data_outputs["text"]
                            logger.info("从 data.outputs.text 提取数据")
                        # 如果没有text字段，直接使用outputs
                        elif data_outputs:
                            source_data = data_outputs
                            logger.info("从 data.outputs 提取数据")
                        # 如果outputs也没有，直接使用data
                        elif data:
                            source_data = data
                            logger.info("从 data 提取数据")
                
                # 路径2: 直接使用outputs (如果路径1没有找到)
                if not source_data and isinstance(outputs, dict) and outputs:
                    source_data = outputs
                    logger.info("从 outputs 提取数据")
                
                # 路径3: 直接使用full_response (如果前面都没找到)
                if not source_data and full_response:
                    source_data = full_response
                    logger.info("从 full_response 提取数据")
                
                logger.info(f"最终数据源: {json.dumps(source_data, ensure_ascii=False, indent=2)}")
                
                if source_data:
                    # 根据映射关系提取字段
                    # invoice_title -> invoice_type
                    if "invoice_title" in source_data:
                        invoice.invoice_type = str(source_data["invoice_title"])[:50]  # 限制长度
                        logger.info(f"更新 invoice_type: {invoice.invoice_type}")
                    
                    # invoice_no -> invoice_no
                    if "invoice_no" in source_data:
                        invoice.invoice_no = str(source_data["invoice_no"])[:100]  # 限制长度
                        logger.info(f"更新 invoice_no: {invoice.invoice_no}")
                    
                    # supplier_no -> supplier_name (如果seller_info->name不存在)
                    if "supplier_no" in source_data and not invoice.supplier_name:
                        invoice.supplier_name = str(source_data["supplier_no"])[:200]
                        logger.info(f"更新 supplier_name (from supplier_no): {invoice.supplier_name}")
                    
                    # docdate -> invoice_date
                    if "docdate" in source_data:
                        date_str = source_data["docdate"]
                        if date_str:
                            try:
                                if date_parser:
                                    invoice.invoice_date = date_parser.parse(str(date_str))
                                else:
                                    from datetime import datetime as dt
                                    invoice.invoice_date = dt.fromisoformat(str(date_str).replace('Z', '+00:00'))
                                logger.info(f"更新 invoice_date: {invoice.invoice_date}")
                            except Exception as e:
                                logger.warning(f"解析日期失败: {date_str}, 错误: {str(e)}")
                    
                    # buyer_info->name -> buyer_name
                    if "buyer_info" in source_data and isinstance(source_data["buyer_info"], dict):
                        buyer_info = source_data["buyer_info"]
                        if "name" in buyer_info:
                            invoice.buyer_name = str(buyer_info["name"])[:200]
                            logger.info(f"更新 buyer_name: {invoice.buyer_name}")
                        if "tax_id" in buyer_info:
                            invoice.buyer_tax_no = str(buyer_info["tax_id"])[:50]
                            logger.info(f"更新 buyer_tax_no: {invoice.buyer_tax_no}")
                    
                    # seller_info->name -> supplier_name
                    if "seller_info" in source_data and isinstance(source_data["seller_info"], dict):
                        seller_info = source_data["seller_info"]
                        if "name" in seller_info:
                            invoice.supplier_name = str(seller_info["name"])[:200]
                            logger.info(f"更新 supplier_name: {invoice.supplier_name}")
                        if "tax_id" in seller_info:
                            invoice.supplier_tax_no = str(seller_info["tax_id"])[:50]
                            logger.info(f"更新 supplier_tax_no: {invoice.supplier_tax_no}")
                    
                    # total_amount_exclusive_tax -> amount
                    if "total_amount_exclusive_tax" in source_data:
                        try:
                            invoice.amount = float(source_data["total_amount_exclusive_tax"])
                            logger.info(f"更新 amount: {invoice.amount}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"解析amount失败: {source_data['total_amount_exclusive_tax']}, 错误: {str(e)}")
                    
                    # total_tax_amount -> tax_amount
                    if "total_tax_amount" in source_data:
                        try:
                            invoice.tax_amount = float(source_data["total_tax_amount"])
                            logger.info(f"更新 tax_amount: {invoice.tax_amount}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"解析tax_amount失败: {source_data['total_tax_amount']}, 错误: {str(e)}")
                    
                    # total_amount_inclusive_tax->in_figures -> total_amount
                    if "total_amount_inclusive_tax" in source_data:
                        if isinstance(source_data["total_amount_inclusive_tax"], dict):
                            if "in_figures" in source_data["total_amount_inclusive_tax"]:
                                try:
                                    invoice.total_amount = float(source_data["total_amount_inclusive_tax"]["in_figures"])
                                    logger.info(f"更新 total_amount: {invoice.total_amount}")
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"解析total_amount失败: {source_data['total_amount_inclusive_tax']['in_figures']}, 错误: {str(e)}")
                        elif isinstance(source_data["total_amount_inclusive_tax"], (int, float)):
                            # 如果直接是数字，也尝试使用
                            try:
                                invoice.total_amount = float(source_data["total_amount_inclusive_tax"])
                                logger.info(f"更新 total_amount (直接值): {invoice.total_amount}")
                            except (ValueError, TypeError) as e:
                                logger.warning(f"解析total_amount失败: {source_data['total_amount_inclusive_tax']}, 错误: {str(e)}")
                    
                    # currency -> currency
                    if "currency" in source_data:
                        currency = str(source_data["currency"]).strip().upper()
                        if currency:
                            invoice.currency = currency[:10]  # 限制长度
                            logger.info(f"更新 currency: {invoice.currency}")
                    
                    # remarks -> remark
                    if "remarks" in source_data:
                        remarks = str(source_data["remarks"])
                        invoice.remark = remarks[:500] if len(remarks) <= 500 else remarks[:500]  # 限制长度
                        logger.info(f"更新 remark: {invoice.remark[:100]}...")  # 只显示前100字符
                
                # 如果normalized_fields有数据，也尝试更新（作为备用）
                if normalized_fields:
                    logger.info("使用标准化字段作为备用数据源")
                    if "invoice_no" in normalized_fields and not invoice.invoice_no:
                        invoice.invoice_no = str(normalized_fields["invoice_no"])[:100]
                    if "invoice_type" in normalized_fields and not invoice.invoice_type:
                        invoice.invoice_type = str(normalized_fields["invoice_type"])[:50]
                    if "invoice_date" in normalized_fields and not invoice.invoice_date:
                        date_str = normalized_fields["invoice_date"]
                        if date_str:
                            try:
                                if date_parser:
                                    invoice.invoice_date = date_parser.parse(str(date_str))
                                else:
                                    from datetime import datetime as dt
                                    invoice.invoice_date = dt.fromisoformat(str(date_str).replace('Z', '+00:00'))
                            except:
                                pass
                    if "amount" in normalized_fields and invoice.amount is None:
                        try:
                            invoice.amount = float(normalized_fields["amount"])
                        except:
                            pass
                    if "tax_amount" in normalized_fields and invoice.tax_amount is None:
                        try:
                            invoice.tax_amount = float(normalized_fields["tax_amount"])
                        except:
                            pass
                    if "total_amount" in normalized_fields and invoice.total_amount is None:
                        try:
                            invoice.total_amount = float(normalized_fields["total_amount"])
                        except:
                            pass
                    if "supplier_name" in normalized_fields and not invoice.supplier_name:
                        invoice.supplier_name = str(normalized_fields["supplier_name"])[:200]
                    if "supplier_tax_no" in normalized_fields and not invoice.supplier_tax_no:
                        invoice.supplier_tax_no = str(normalized_fields["supplier_tax_no"])[:50]
                    if "buyer_name" in normalized_fields and not invoice.buyer_name:
                        invoice.buyer_name = str(normalized_fields["buyer_name"])[:200]
                    if "buyer_tax_no" in normalized_fields and not invoice.buyer_tax_no:
                        invoice.buyer_tax_no = str(normalized_fields["buyer_tax_no"])[:50]
            
            # 计算统计信息
            total_fields = len(normalized_fields) if normalized_fields else 0
            recognized_fields = sum(1 for v in normalized_fields.values() if v is not None and v != "") if normalized_fields else 0
            
            # 计算准确率和置信度
            accuracy = result_data.get("accuracy", 0.95)
            confidence = result_data.get("confidence", 0.9)
            
            # 创建或更新识别结果
            existing_result = self.session.exec(
                select(RecognitionResult).where(RecognitionResult.task_id == task.id)
            ).first()
            
            if existing_result:
                result = existing_result
            else:
                result = RecognitionResult(
                    invoice_id=invoice.id,
                    task_id=task.id,
                    total_fields=total_fields,
                    recognized_fields=recognized_fields,
                    accuracy=accuracy,
                    confidence=confidence,
                    status="success"
                )
                self.session.add(result)
            
            # 更新结果数据
            result.raw_payload = result_data.get("raw_payload")
            result.raw_response_uri = result_data.get("raw_response_uri")
            result.normalized_fields = normalized_fields
            result.model_usage = result_data.get("model_usage")
            
            # 更新任务信息
            if result_data.get("request_id"):
                task.request_id = result_data["request_id"]
            if result_data.get("trace_id"):
                task.trace_id = result_data["trace_id"]
            
            # 更新票据状态和时间
            invoice.recognition_status = "completed"  # 识别成功，设置为completed
            invoice.recognition_accuracy = accuracy
            invoice.update_time = datetime.now()
            
            logger.info("--- 更新后的invoice字段 ---")
            logger.info(f"invoice_no: {invoice.invoice_no}")
            logger.info(f"invoice_type: {invoice.invoice_type}")
            logger.info(f"invoice_date: {invoice.invoice_date}")
            logger.info(f"amount: {invoice.amount}")
            logger.info(f"tax_amount: {invoice.tax_amount}")
            logger.info(f"total_amount: {invoice.total_amount}")
            logger.info(f"currency: {invoice.currency}")
            logger.info(f"supplier_name: {invoice.supplier_name}")
            logger.info(f"supplier_tax_no: {invoice.supplier_tax_no}")
            logger.info(f"buyer_name: {invoice.buyer_name}")
            logger.info(f"buyer_tax_no: {invoice.buyer_tax_no}")
            logger.info(f"remark: {invoice.remark}")
            logger.info(f"recognition_status: {invoice.recognition_status}")
            
            # 保存发票行项目到INVOICE_ITEM表
            if source_data and "items" in source_data and isinstance(source_data["items"], list):
                logger.info("=" * 80)
                logger.info("=== 开始保存发票行项目 ===")
                logger.info(f"找到 {len(source_data['items'])} 个行项目")
                
                # 先删除该invoice的所有旧items（如果存在）
                existing_items = self.session.exec(
                    select(InvoiceItem).where(InvoiceItem.id == invoice.id)
                ).all()
                if existing_items:
                    logger.info(f"删除 {len(existing_items)} 个旧的行项目")
                    for old_item in existing_items:
                        self.session.delete(old_item)
                
                # 遍历items数组，创建InvoiceItem记录
                items_saved = 0
                for idx, item_data in enumerate(source_data["items"]):
                    if not isinstance(item_data, dict):
                        logger.warning(f"跳过无效的行项目数据（索引 {idx}）: {item_data}")
                        continue
                    
                    try:
                        # 确定line_no：优先使用LineId（如果是数字），否则使用索引+1
                        line_no = idx + 1  # 默认使用索引+1
                        if "LineId" in item_data and item_data["LineId"]:
                            try:
                                line_no = int(item_data["LineId"])
                            except (ValueError, TypeError):
                                # 如果LineId不是数字，使用索引+1
                                line_no = idx + 1
                        
                        # 确保invoice_no已更新（如果还没有）
                        invoice_no = invoice.invoice_no or "UNKNOWN"
                        
                        # 创建InvoiceItem记录
                        invoice_item = InvoiceItem(
                            id=invoice.id,
                            invoice_no=invoice_no,
                            line_no=line_no,
                            name=str(item_data.get("name", ""))[:500] if item_data.get("name") else None,
                            part_no=str(item_data.get("part_no", ""))[:100] if item_data.get("part_no") else None,
                            supplier_partno=str(item_data.get("supplier_partno", ""))[:100] if item_data.get("supplier_partno") else None,
                            unit=str(item_data.get("unit", ""))[:50] if item_data.get("unit") else None,
                            quantity=float(item_data["quantity"]) if item_data.get("quantity") is not None else None,
                            unit_price=float(item_data["unit_price"]) if item_data.get("unit_price") is not None else None,
                            amount=float(item_data["amount"]) if item_data.get("amount") is not None else None,
                            tax_rate=str(item_data.get("tax_rate", ""))[:20] if item_data.get("tax_rate") else None,
                            tax_amount=float(item_data["tax_amount"]) if item_data.get("tax_amount") is not None else None,
                            create_time=datetime.now(),
                            update_time=datetime.now()
                        )
                        
                        self.session.add(invoice_item)
                        items_saved += 1
                        logger.info(f"保存行项目 {line_no}: {invoice_item.name}")
                        
                    except Exception as e:
                        logger.error(f"保存行项目失败（索引 {idx}）: {str(e)}", exc_info=True)
                        # 继续处理下一个item，不中断整个流程
                        continue
                
                logger.info(f"成功保存 {items_saved} 个行项目到INVOICE_ITEM表")
                logger.info("=" * 80)
            else:
                logger.info("未找到items数组或items为空，跳过保存行项目")
            
            self.session.add(result)
            self.session.add(task)
            self.session.add(invoice)
            self.session.commit()
            
            logger.info("=" * 80)
            logger.info(f"识别结果已保存并更新invoice表: task_id={task.id}, invoice_id={invoice.id}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"保存识别结果失败: {str(e)}", exc_info=True)
            self.session.rollback()
            raise
    
    def _mark_task_completed(self, task: RecognitionTask):
        """标记任务为完成"""
        task.status = "completed"
        task.end_time = datetime.now()
        if task.start_time:
            duration = (task.end_time - task.start_time).total_seconds()
            task.duration = duration
        self.session.add(task)
        self.session.commit()
    
    def _mark_task_failed(self, task: RecognitionTask, error_code: str, error_message: str):
        """标记任务为失败"""
        task.status = "failed"
        task.end_time = datetime.now()
        task.error_code = error_code
        task.error_message = error_message
        if task.start_time:
            duration = (task.end_time - task.start_time).total_seconds()
            task.duration = duration
        self.session.add(task)
        
        # 更新票据状态
        invoice = self.session.get(Invoice, task.invoice_id)
        if invoice:
            invoice.recognition_status = "failed"
            self.session.add(invoice)
        
        self.session.commit()

