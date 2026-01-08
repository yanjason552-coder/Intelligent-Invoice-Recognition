"""
恢复已上传文件的相关数据库记录

此脚本会：
1. 扫描上传目录，找到所有已存在的文件
2. 计算每个文件的哈希值
3. 检查数据库中是否已存在该文件记录
4. 如果不存在，创建 invoice_file 和 invoice 记录
5. 从文件名和文件信息中提取尽可能多的元数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
import hashlib
from datetime import datetime
from uuid import uuid4, UUID
from sqlalchemy import select
from sqlmodel import Session
from app.core.db import engine
from app.models.models_invoice import InvoiceFile, Invoice
from app.models.models import User
import logging
import mimetypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 上传目录配置（与 invoice.py 中的配置保持一致）
BACKEND_DIR = Path(__file__).parent
UPLOAD_DIR = BACKEND_DIR / "uploads" / "invoices"

def calculate_file_hash(file_path: Path) -> str:
    """计算文件的 SHA256 哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_mime_type(file_path: Path) -> str:
    """获取文件的 MIME 类型"""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"

def restore_file_record(file_path: Path, session: Session) -> dict:
    """恢复单个文件的数据库记录"""
    try:
        # 1. 获取文件信息
        file_name = file_path.name
        file_size = file_path.stat().st_size
        file_ext = file_path.suffix.lower()
        file_type = file_ext[1:] if file_ext else "pdf"
        mime_type = get_file_mime_type(file_path)
        
        # 2. 计算文件哈希值
        logger.info(f"计算文件哈希值: {file_name}")
        file_hash = calculate_file_hash(file_path)
        logger.info(f"文件哈希值: {file_hash}")
        
        # 3. 检查文件是否已存在（使用更安全的查询方式）
        try:
            existing_file = session.exec(
                select(InvoiceFile).where(InvoiceFile.file_hash == file_hash)
            ).one_or_none()
            
            if existing_file:
                # 确保对象已完全加载
                file_id = existing_file.id
                logger.info(f"○ 文件已存在: {file_name} (ID: {file_id})")
                return {
                    "status": "exists",
                    "file_id": file_id,
                    "invoice_file": existing_file
                }
        except Exception as e:
            logger.warning(f"检查文件是否存在时出错: {str(e)}，将创建新记录")
        
        # 4. 获取第一个可用用户作为上传者（如果没有用户，使用系统用户）
        # 这里假设至少有一个用户，如果没有用户会报错
        try:
            # 使用更安全的方式查询用户
            users = session.exec(select(User.id, User.email).limit(1)).all()
            if not users:
                logger.error("数据库中没有用户，无法创建文件记录")
                return {
                    "status": "error",
                    "error": "没有用户"
                }
            
            # 获取用户ID（从查询结果中）
            user_id = users[0][0] if isinstance(users[0], tuple) else users[0].id
            logger.info(f"使用用户ID: {user_id}")
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return {
                "status": "error",
                "error": f"获取用户失败: {str(e)}"
            }
        
        # 5. 获取文件的上传时间（使用文件的修改时间或当前时间）
        try:
            upload_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        except:
            upload_time = datetime.now()
        
        # 6. 创建文件记录
        logger.info(f"创建文件记录: {file_name}")
        invoice_file = InvoiceFile(
            file_name=file_name,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            file_hash=file_hash,
            uploader_id=user_id,
            upload_time=upload_time,
            status="uploaded"
        )
        session.add(invoice_file)
        session.commit()
        session.refresh(invoice_file)
        logger.info(f"✓ 文件记录已创建: {invoice_file.id}")
        
        # 7. 创建票据记录
        logger.info(f"创建票据记录: {file_name}")
        invoice = Invoice(
            invoice_no=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}",
            invoice_type="未知",
            file_id=invoice_file.id,
            creator_id=user_id,
            recognition_status="pending",
            review_status="pending"
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        logger.info(f"✓ 票据记录已创建: {invoice.id}, 票据编号: {invoice.invoice_no}")
        
        return {
            "status": "created",
            "file_id": invoice_file.id,
            "invoice_id": invoice.id,
            "invoice_no": invoice.invoice_no,
            "invoice_file": invoice_file,
            "invoice": invoice
        }
        
    except Exception as e:
        logger.error(f"✗ 恢复文件记录失败: {file_name}, 错误: {str(e)}", exc_info=True)
        session.rollback()
        return {
            "status": "error",
            "error": str(e)
        }

def restore_all_files():
    """恢复所有上传文件"""
    logger.info("=" * 60)
    logger.info("开始恢复已上传文件的数据库记录")
    logger.info("=" * 60)
    
    # 检查上传目录是否存在
    if not UPLOAD_DIR.exists():
        logger.error(f"上传目录不存在: {UPLOAD_DIR}")
        return False
    
    logger.info(f"上传目录: {UPLOAD_DIR}")
    
    # 获取所有文件
    all_files = list(UPLOAD_DIR.glob("*"))
    files = [f for f in all_files if f.is_file()]
    
    logger.info(f"找到 {len(files)} 个文件")
    logger.info("")
    
    if len(files) == 0:
        logger.info("没有需要恢复的文件")
        return True
    
    # 统计信息
    stats = {
        "total": len(files),
        "created": 0,
        "exists": 0,
        "errors": 0
    }
    
    # 使用数据库会话
    with Session(engine) as session:
        for i, file_path in enumerate(files, 1):
            logger.info(f"[{i}/{len(files)}] 处理文件: {file_path.name}")
            result = restore_file_record(file_path, session)
            
            if result["status"] == "created":
                stats["created"] += 1
            elif result["status"] == "exists":
                stats["exists"] += 1
            elif result["status"] == "error":
                stats["errors"] += 1
            
            logger.info("")
    
    # 输出统计信息
    logger.info("=" * 60)
    logger.info("恢复完成统计:")
    logger.info(f"  总文件数: {stats['total']}")
    logger.info(f"  新创建记录: {stats['created']}")
    logger.info(f"  已存在记录: {stats['exists']}")
    logger.info(f"  错误数量: {stats['errors']}")
    logger.info("=" * 60)
    
    return stats["errors"] == 0

def main():
    """主函数"""
    try:
        print("\n" + "=" * 60)
        print("恢复已上传文件的数据库记录")
        print("=" * 60)
        print(f"上传目录: {UPLOAD_DIR}")
        print("=" * 60)
        
        confirm = input("\n确认执行此操作？(输入 'YES' 确认): ")
        
        if confirm != 'YES':
            print("操作已取消")
            return
        
        # 执行恢复
        success = restore_all_files()
        
        if success:
            print("\n✓ 文件记录恢复成功完成")
        else:
            print("\n✗ 文件记录恢复过程中出现错误，请检查日志")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

