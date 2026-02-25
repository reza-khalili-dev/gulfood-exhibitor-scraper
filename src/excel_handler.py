import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

class ExcelHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
    
    def save_to_excel(self, data, filename=None):
        """ذخیره اطلاعات در فایل اکسل"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'gulfood_exhibitors_{timestamp}.xlsx'
        
        filepath = self.output_dir / filename
        
        # ایجاد DataFrame
        df = pd.DataFrame(data)
        
        # ترتیب ستون‌ها
        columns_order = [
            'نام شرکت',
            'کتگوری فعالیت',
            'محصولات',
            'کشور',
            'آدرس',
            'وبسایت',
            'ایمیل',
            'لینکدین',
            'توییتر',
            'فیسبوک',
            'اینستاگرام'
        ]
        
        # اطمینان از وجود همه ستون‌ها
        for col in columns_order:
            if col not in df.columns:
                df[col] = ''
        
        df = df[columns_order]
        
        # ذخیره در اکسل
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Exhibitors', index=False)
            
            # تنظیم عرض ستون‌ها
            worksheet = writer.sheets['Exhibitors']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        self.logger.info(f"فایل اکسل در {filepath} ذخیره شد")
        return filepath
    
    def save_partial(self, data, page_num):
        """ذخیره موقت برای هر صفحه"""
        filename = f'partial_results_page_{page_num}.xlsx'
        return self.save_to_excel(data, filename)