import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
import logging
import sys
import re

class GulfoodScraper:
    def __init__(self):
        self.base_url = "https://exhibitors.gulfood.com"
        self.api_url = f"{self.base_url}/gulfood-2026/Exhibitor/fetchExhibitors"
        self.session = requests.Session()
        self.setup_session()
        self.setup_logging()
        
    def setup_session(self):
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,fa;q=0.8',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': self.base_url,
            'referer': f'{self.base_url}/gulfood-2026/Exhibitor',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        })
        
        cookies = {
            '_ga': 'GA1.1.876438033.1771852033',
            'ci_sessions': 'bg9kgm8l1464784p81jja1gobc6trjnt',
        }
        self.session.cookies.update(cookies)
        
    def setup_logging(self):
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def clean_text(self, text):
        if not text:
            return ''
        text = ''.join(char for char in str(text) if ord(char) >= 32 or char in '\n\r\t')
        return text.strip()
    
    def fetch_page(self, start=0, limit=10):
        data = {
            'limit': limit,
            'start': start,
            'keyword_search': '',
            'cuntryId': '',
            'InitialKey': '',
            'start_up_exhibitors': '',
            'type': '',
            'new_category': '',
            'new_sub_category': '',
            'new_sub_sub_category': '',
            'event_sector_value': ''
        }
        
        try:
            response = self.session.post(self.api_url, data=data)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"خطا در دریافت صفحه {start}: {e}")
            return None
    
    def extract_companies_from_list(self, html_content):
        """استخراج اطلاعات پایه از صفحه لیست"""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        companies = []
        items = soup.find_all('div', class_='item')
        
        for item in items:
            try:
                company = {
                    'نام شرکت': '',
                    'کتگوری فعالیت': '',
                    'محصولات': '',
                    'کشور': '',
                    'آدرس': '',
                    'وبسایت': '',
                    'ایمیل': '',
                    'لینکدین': '',
                    'توییتر': '',
                    'فیسبوک': '',
                    'اینستاگرام': '',
                    'profile_url': ''
                }
                
                # نام شرکت
                name_tag = item.find('h4', class_='heading')
                if name_tag:
                    company['نام شرکت'] = self.clean_text(name_tag.get_text(strip=True))
                
                # کشور
                country_span = item.find('span', style=re.compile(r'font-weight:600'))
                if country_span:
                    company['کشور'] = self.clean_text(country_span.get_text(strip=True))
                
                # آدرس (شماره غرفه)
                stand_p = item.find('p', string=re.compile(r'Stand No-'))
                if stand_p:
                    company['آدرس'] = self.clean_text(stand_p.get_text(strip=True))
                
                # کتگوری فعالیت از عکس sector
                sector_div = item.find('div', class_='eventlogoshow')
                if sector_div:
                    img = sector_div.find('img')
                    if img and img.get('src'):
                        img_url = img['src']
                        sector_name = img_url.split('/')[-1].replace('.jpg', '').replace('-', ' ')
                        company['کتگوری فعالیت'] = self.clean_text(sector_name)
                
                # پیدا کردن لینک صفحه جزئیات
                profile_link = None
                all_links = item.find_all('a', href=True)
                for link in all_links:
                    link_text = link.get_text(strip=True).upper()
                    if 'VIEW PROFILE' in link_text or 'PROFILE' in link_text:
                        profile_link = link
                        break
                
                if profile_link and profile_link.get('href'):
                    href = profile_link['href']
                    if href.startswith('/'):
                        company['profile_url'] = self.base_url + href
                    else:
                        company['profile_url'] = href
                
                companies.append(company)
                
            except Exception as e:
                self.logger.error(f"خطا در پردازش آیتم: {e}")
                continue
        
        return companies
    
    def extract_company_details(self, profile_url):
        """استخراج اطلاعات تکمیلی از صفحه جزئیات"""
        try:
            response = self.session.get(profile_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {
                'وبسایت': '',
                'ایمیل': '',
                'محصولات': '',
                'لینکدین': '',
                'توییتر': '',
                'فیسبوک': '',
                'اینستاگرام': ''
            }
            
            # ========== استخراج وبسایت (رفع مشکل) ==========
            all_links = soup.find_all('a', href=True)
            website_candidates = []
            
            for link in all_links:
                href = link.get('href', '')
                
                # نادیده گرفتن لینک‌های بی‌ربط
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                
                # نادیده گرفتن لینک‌های نمایشگاه
                if any(site in href.lower() for site in ['gulfood.com', 'exhibitors.gulfood', 'map.gulfood']):
                    continue
                
                # نادیده گرفتن شبکه‌های اجتماعی
                if any(social in href.lower() for social in ['linkedin', 'twitter', 'facebook', 'instagram']):
                    continue
                
                # نادیده گرفتن ایمیل
                if href.startswith('mailto:'):
                    continue
                
                # بررسی اینکه لینک واقعاً یک وبسایت است
                if re.match(r'^https?://([a-zA-Z0-9.-]+\.)+[a-zA-Z]{2,}', href):
                    link_text = link.get_text(strip=True).lower()
                    
                    # امتیازدهی به لینک‌ها
                    score = 0
                    if 'website' in link_text or 'www' in link_text or 'visit' in link_text:
                        score += 3
                    if 'click here' in link_text:
                        score += 1
                    if len(href) < 100:  # لینک‌های کوتاه‌تر بهترند
                        score += 1
                    
                    website_candidates.append((href, score))
            
            # انتخاب بهترین کاندیدا (با بالاترین امتیاز)
            if website_candidates:
                website_candidates.sort(key=lambda x: x[1], reverse=True)
                details['وبسایت'] = website_candidates[0][0]
            
            # ========== استخراج ایمیل ==========
            email_link = soup.find('a', href=re.compile(r'^mailto:'))
            if email_link:
                details['ایمیل'] = email_link.get('href', '').replace('mailto:', '')
            else:
                text = soup.get_text()
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                if emails:
                    # فیلتر کردن ایمیل‌های نمایشگاه
                    filtered_emails = [e for e in emails if 'gulfood' not in e.lower()]
                    if filtered_emails:
                        details['ایمیل'] = filtered_emails[0]
                    else:
                        details['ایمیل'] = emails[0]
            
            # ========== استخراج محصولات ==========
            products = []
            
            # روش ۱: پیدا کردن بخش Products
            products_section = soup.find(['div', 'section', 'h2', 'h3'], 
                                        string=re.compile(r'Products|Brands|Product Categories|Our Products', re.I))
            if products_section:
                next_elem = products_section.find_next(['ul', 'div', 'table', 'p'])
                if next_elem:
                    if next_elem.name == 'ul':
                        products = [li.get_text(strip=True) for li in next_elem.find_all('li')]
                    else:
                        text = next_elem.get_text(strip=True)
                        if text and len(text) > 5:
                            products = [text]
            
            # روش ۲: پیدا کردن با کلاس‌های مرتبط
            if not products:
                product_elements = soup.find_all(['div', 'span', 'p', 'li'], 
                                                class_=re.compile(r'product|brand|category|item', re.I))
                for elem in product_elements[:10]:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 3 and text not in products:
                        if not re.match(r'^(Tel|Email|Fax|Phone|www|http)', text, re.I):
                            products.append(text)
            
            # روش ۳: جستجوی تگ‌های جدول
            if not products:
                tables = soup.find_all('table')
                for table in tables:
                    if re.search(r'product|brand', table.get_text(), re.I):
                        rows = table.find_all('tr')
                        for row in rows[:5]:
                            cells = row.find_all(['td', 'th'])
                            for cell in cells:
                                text = cell.get_text(strip=True)
                                if text and len(text) > 3 and text not in products:
                                    products.append(text)
                        if products:
                            break
            
            if products:
                details['محصولات'] = ', '.join(products[:15])
            
            # ========== استخراج شبکه‌های اجتماعی ==========
            for link in all_links:
                href = link.get('href', '').lower()
                if 'linkedin.com' in href:
                    details['لینکدین'] = link.get('href', '')
                elif 'twitter.com' in href or 'x.com' in href:
                    details['توییتر'] = link.get('href', '')
                elif 'facebook.com' in href:
                    details['فیسبوک'] = link.get('href', '')
                elif 'instagram.com' in href:
                    details['اینستاگرام'] = link.get('href', '')
            
            return details
            
        except Exception as e:
            self.logger.error(f"خطا در پردازش صفحه جزئیات {profile_url}: {e}")
            return None
    
    def scrape_all_companies(self, max_pages=None):
        """استخراج کامل اطلاعات (لیست + جزئیات)"""
        all_companies = []
        start = 0
        limit = 10
        page = 1
        
        self.logger.info("شروع استخراج اطلاعات شرکت‌ها...")
        
        while True:
            if max_pages and page > max_pages:
                break
                
            self.logger.info(f"دریافت صفحه {page} (start={start})...")
            html_content = self.fetch_page(start=start, limit=limit)
            
            if not html_content:
                break
            
            companies = self.extract_companies_from_list(html_content)
            
            if not companies:
                self.logger.info("به انتهای لیست رسیدیم")
                break
            
            for i, company in enumerate(companies, 1):
                if company.get('profile_url'):
                    self.logger.info(f"  دریافت جزئیات شرکت {i}/{len(companies)}: {company['نام شرکت'][:30]}...")
                    details = self.extract_company_details(company['profile_url'])
                    if details:
                        company.update(details)
                    time.sleep(1)
                else:
                    self.logger.warning(f"  شرکت {company['نام شرکت']} لینک صفحه جزئیات ندارد!")
            
            all_companies.extend(companies)
            self.logger.info(f"تعداد شرکت‌های این صفحه: {len(companies)}")
            self.logger.info(f"تعداد کل شرکت‌ها تاکنون: {len(all_companies)}")
            
            if len(all_companies) % 20 == 0:
                self.save_companies_data(all_companies, f'companies_backup_{len(all_companies)}.json')
            
            start += limit
            page += 1
            time.sleep(2)
        
        self.logger.info(f"استخراج کامل شد. تعداد کل شرکت‌ها: {len(all_companies)}")
        return all_companies
    
    def save_companies_data(self, data, filename='companies_data.json'):
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"اطلاعات در {filepath} ذخیره شد")
        return filepath

    def load_companies_data(self, filename='companies_data.json'):
        filepath = Path('output') / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []