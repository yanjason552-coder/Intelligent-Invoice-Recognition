"""
简单检查发票识别情况
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select, func
from app.core.db import engine
from app.models.models_invoice import RecognitionTask, RecognitionResult

with Session(engine) as session:
    print("=" * 60)
    print("发票识别情况检查")
    print("=" * 60)
    
    # 任务状态统计
    print("\n【识别任务状态】")
    for status in ["pending", "processing", "completed", "failed"]:
        count = session.exec(
            select(func.count()).select_from(RecognitionTask)
            .where(RecognitionTask.status == status)
        ).one()
        labels = {"pending": "待处理", "processing": "处理中", "completed": "已完成", "failed": "失败"}
        print(f"  {labels.get(status, status)}: {count}")
    
    # 识别结果统计
    print("\n【识别结果统计】")
    result_total = session.exec(select(func.count()).select_from(RecognitionResult)).one()
    print(f"  结果总数: {result_total}")
    
    if result_total > 0:
        for status in ["success", "failed", "partial"]:
            count = session.exec(
                select(func.count()).select_from(RecognitionResult)
                .where(RecognitionResult.status == status)
            ).one()
            labels = {"success": "成功", "failed": "失败", "partial": "部分成功"}
            print(f"  {labels.get(status, status)}: {count}")
    
    print("\n" + "=" * 60)

