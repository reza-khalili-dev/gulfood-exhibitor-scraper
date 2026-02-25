from src.scraper import GulfoodScraper
from src.excel_handler import ExcelHandler
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Gulfood 2026 Exhibitor Scraper')
    parser.add_argument('--max-pages', type=int, help='حداکثر تعداد صفحات')
    parser.add_argument('--resume', action='store_true', help='ادامه از فایل قبلی')
    
    args = parser.parse_args()
    
    scraper = GulfoodScraper()
    excel_handler = ExcelHandler()
    
    if args.resume:
        print("بارگذاری اطلاعات قبلی...")
        companies = scraper.load_companies_data()
        print(f"تعداد شرکت‌های بارگذاری شده: {len(companies)}")
    else:
        print("شروع استخراج اطلاعات جدید...")
        companies = scraper.scrape_all_companies(max_pages=args.max_pages)
    
    if companies:
        # ذخیره JSON پشتیبان
        scraper.save_companies_data(companies)
        
        # ذخیره اکسل
        excel_file = excel_handler.save_to_excel(companies)
        print(f"✅ اطلاعات {len(companies)} شرکت در فایل {excel_file} ذخیره شد.")
    else:
        print("❌ هیچ اطلاعاتی استخراج نشد!")

if __name__ == "__main__":
    main()