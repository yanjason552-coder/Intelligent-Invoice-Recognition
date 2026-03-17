import os
import json
import sys
sys.path.append('.')

os.environ['DATABASE_URL'] = 'postgresql://fits:fits@localhost:5432/fits'

from app.database import get_session
from app.models.models_invoice import Invoice, RecognitionResult
from sqlalchemy import select

def check_invoice():
    with get_session() as session:
        invoice = session.get(Invoice, '2b2701eb-36e2-4069-82d2-78b47877cff7')
        print('=== 发票信息 ===')
        print('ID:', invoice.id)
        print('invoice_no:', invoice.invoice_no)
        print('model_name:', getattr(invoice, 'model_name', None))

        result = session.exec(
            select(RecognitionResult).where(RecognitionResult.invoice_id == '2b2701eb-36e2-4069-82d2-78b47877cff7')
        ).first()

        print('\n=== 识别结果信息 ===')
        if result:
            print('result_id:', result.id)
            print('normalized_fields type:', type(result.normalized_fields))
            print('normalized_fields is None:', result.normalized_fields is None)

            if result.normalized_fields:
                if isinstance(result.normalized_fields, dict):
                    print('normalized_fields keys:', list(result.normalized_fields.keys()))
                    print('doc_type:', result.normalized_fields.get('doc_type'))
                    print('has items:', 'items' in result.normalized_fields)
                    if 'items' in result.normalized_fields:
                        items = result.normalized_fields['items']
                        print('items type:', type(items))
                        print('items length:', len(items) if isinstance(items, list) else 'N/A')
                        if isinstance(items, list) and len(items) > 0:
                            print('first item keys:', list(items[0].keys()) if isinstance(items[0], dict) else 'N/A')
                elif isinstance(result.normalized_fields, str):
                    print('normalized_fields is string, length:', len(result.normalized_fields))
                    try:
                        parsed = json.loads(result.normalized_fields)
                        print('parsed successfully, keys:', list(parsed.keys()) if isinstance(parsed, dict) else 'not dict')
                    except:
                        print('failed to parse as JSON')
        else:
            print('No recognition result found')

if __name__ == '__main__':
    check_invoice()