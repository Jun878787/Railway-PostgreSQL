"""
List formatting functionality for the North Sea Financial Bot
Handles customer information parsing and formatting
"""

import re
import logging
import googlemaps
import os

logger = logging.getLogger(__name__)

class ListFormatter:
    """格式化客戶資訊列表"""
    
    def __init__(self):
        self.required_fields = ['customer', 'amount', 'time', 'address', 'company']
        # Initialize Google Maps client
        self.gmaps = None
        try:
            api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if api_key:
                self.gmaps = googlemaps.Client(key=api_key)
                logger.info("Google Maps client initialized successfully")
            else:
                logger.warning("Google Maps API key not found")
        except Exception as e:
            logger.error(f"Failed to initialize Google Maps client: {e}")
            self.gmaps = None
    
    def format_customer_name(self, text):
        """格式化客戶姓名 - 全名或姓Ms.r"""
        # 提取姓名的各種模式
        patterns = [
            r'客戶名稱[：:]\s*([^\s\n\(（]+)',
            r'客戶名字[：:]\s*([^\s\n\(（]+)',
            r'姓名[：:]\s*([^\s\n\(（]+)',
            r'代表人姓名[：:]\s*([^\s\n\(（]+)',
            r'客戶[：:]\s*([^\s\n\(（]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # 移除可能的後綴
                name = re.sub(r'[（(].*?[）)]', '', name)
                if len(name) == 1:
                    return f"{name}Ms.r"
                else:
                    return name
        return None
    
    def format_amount(self, text):
        """格式化金額為 NN.N萬 格式"""
        # 匹配各種金額格式，支援逗號分隔的數字
        patterns = [
            r'金額[：:]\s*(\d+)[萬万]',
            r'預約金額[：:]\s*(\d+)[萬万]',
            r'收款金額[：:]\s*(\d+)[萬万]',
            r'存入操作金額[：:]\s*(\d+)[萬万]現金',
            r'額度[：:]\s*(\d+)[萬万]',
            r'儲值金額[：:]\s*(\d+)公克',
            r'現場辦理金額[：:]\s*([\d,]+)',
            r'存入操作金額[：:]\s*([\d,]+)',
            r'金額[：:]\s*([\d,]+)',
            r'收款金額[：:]\s*([\d,]+)',
            r'歸還信用金[：:]\s*([\d,]+)[萬万]',
            r'(\d+)[萬万]元整',
            r'(\d+)[萬万]現金',
            r'(\d+)[萬万]',
            r'(\d+)公克'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')  # 移除逗號
                amount = float(amount_str)
                # 如果原本就是萬為單位的格式
                if '萬' in pattern or '公克' in pattern:
                    return f"{amount:.1f}萬"
                else:
                    # 將元轉換為萬
                    wan_amount = amount / 10000
                    return f"{wan_amount:.1f}萬"
        return None
    
    def format_time(self, text):
        """格式化時間為24小時制"""
        # 檢查是否包含下午/晚上標記
        is_afternoon = '下午' in text or '晚上' in text
        is_morning = '早上' in text or '上午' in text
        
        # 匹配時間格式
        time_patterns = [
            r'時間[：:]\s*(\d{1,2})[：:](\d{2})',
            r'預約時間[：:]\s*(\d{1,2})[：:](\d{2})',
            r'時間[：:]\s*(\d{1,2})[點点](\d{1,2})',
            r'預約時間[：:]\s*(\d{1,2})[點点](\d{1,2})',
            r'日期時間[：:]\s*.*?(\d{1,2})[點点](\d{1,2})',
            r'時間[：:]\s*(\d{1,2})[點点]半',
            r'預約時間[：:]\s*(\d{1,2})[點点]半',
            r'時間[：:]\s*[下午晚上](\d{1,2})[點点]半',
            r'時間[：:]\s*[上午早上](\d{1,2})[點点]半',
            r'時間[：:]\s*(\d{1,2})[點点]',
            r'預約時間[：:]\s*(\d{1,2})[點点]',
            r'日期時間[：:]\s*.*?(\d{1,2})[點点]',
            r'(\d{1,2})[點点](\d{1,2})',
            r'(\d{1,2})[點点]半',
            r'(\d{1,2})[：:](\d{2})',
            r'(\d{1,2})[點点]',
            r'(\d{1,2})時',
            r'[下午晚上](\d{1,2})[點点]半',
            r'[上午早上](\d{1,2})[點点]半',
            r'[下午晚上](\d{1,2})[點点]',
            r'[上午早上](\d{1,2})[點点]'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                
                # 處理分鐘
                if '點半' in pattern:
                    minute = 30
                elif len(match.groups()) > 1 and match.group(2):
                    minute = int(match.group(2))
                else:
                    minute = 0
                
                # 處理時間轉換
                if is_afternoon and hour < 12:
                    hour += 12
                elif is_morning and hour == 12:
                    hour = 0
                    
                return f"{hour:02d}:{minute:02d}"
        return None
    
    def search_landmark_location(self, landmark_text):
        """使用 Google Maps API 搜尋地標的實際位置"""
        if not self.gmaps:
            return None
            
        try:
            # 檢測地標關鍵字
            landmark_keywords = ['7-11', '7-ELEVEN', '全家', 'FamilyMart', '萊爾富', 'Hi-Life', '麥當勞', 'McDonald', 
                               'KFC', '肯德基', '星巴克', 'Starbucks', '85度C', '摩斯漢堡', 'MOS', '便利商店']
            
            has_landmark = any(keyword in landmark_text for keyword in landmark_keywords)
            
            if has_landmark:
                # 使用地理編碼 API 搜尋地標
                geocode_result = self.gmaps.geocode(landmark_text, region='tw')
                
                if geocode_result:
                    formatted_address = geocode_result[0]['formatted_address']
                    logger.info(f"地標搜尋成功: {landmark_text} -> {formatted_address}")
                    
                    # 從結果中提取縣市區域
                    return self.extract_city_district_from_address(formatted_address)
                else:
                    logger.warning(f"無法找到地標位置: {landmark_text}")
                    return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"地標搜尋失敗: {e}")
            return None
    
    def extract_city_district_from_address(self, address):
        """從地址中提取縣市區域資訊"""
        # 縣市區域匹配模式
        city_pattern = r'(台北市|新北市|桃園市|台中市|台南市|高雄市|基隆市|新竹市|嘉義市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義縣|屏東縣|宜蘭縣|花蓮縣|台東縣|澎湖縣|金門縣|連江縣)'
        city_match = re.search(city_pattern, address)
        
        if city_match:
            city = city_match.group(1)
            # 在找到縣市後，尋找區域名稱
            remaining_text = address[city_match.end():]
            district_match = re.search(r'([^0-9\s，]*?[鄉鎮市區])', remaining_text)
            
            if district_match:
                district = district_match.group(1)
                return f"{city}{district}"
            else:
                return city
        
        return None

    def format_address(self, text):
        """格式化地址，返回 縣市鄉鎮市區 格式"""
        # 如果包含"公司地址"則跳過這行
        if '公司地址' in text:
            return None
            
        # 排除公司地址，只匹配交易/收款/預約地點
        address_patterns = [
            r'預約地點[：:]\s*([^，\n]+)',
            r'地點[：:]\s*([^，\n]+)', 
            r'交易地點[：:]\s*([^，\n]+)',
            r'收款地點[：:]\s*([^，\n]+)',
            r'預約地址[：:]\s*([^，\n]+)',
            r'收款地址[：:]\s*([^，\n]+)',
            r'現場辦理地址[：:]\s*([^，\n]+)'
        ]
            
        for pattern in address_patterns:
            match = re.search(pattern, text)
            if match:
                address = match.group(1).strip()
                
                # 首先嘗試地標搜尋
                landmark_result = self.search_landmark_location(address)
                if landmark_result:
                    return landmark_result
                
                # 如果不是地標或搜尋失敗，使用原本的邏輯
                return self.extract_city_district_from_address(address)
        
        return None
    
    def format_company(self, text):
        """格式化公司名稱 - 提取前兩個字加投資"""
        # 匹配公司名稱的各種格式
        company_patterns = [
            r'公司名稱[：:]\s*([^\n]+)',
            r'公司[：:]\s*([^\n]+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                company_name = match.group(1).strip()
                # 移除常見後綴 - 注意順序很重要，先移除長的後綴
                company_name = re.sub(r'(投資股份有限公司|股份有限公司|企業有限公司|投顧企業有限公司|資本有限公司|有限公司).*$', '', company_name)
                
                # 提取前兩個字
                if len(company_name) >= 2:
                    return f"{company_name[:2]}投資"
                elif len(company_name) == 1:
                    return f"{company_name}投資"
        return None
    
    def parse_list_message(self, text):
        """解析列表訊息內容"""
        result = {
            'customer': '',
            'amount': '',
            'time': '',
            'address': '',
            'company': ''
        }
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 尋找客戶名稱 - 支援多種格式
            if any(keyword in line for keyword in ['姓名', '客戶名稱', '客戶：']):
                customer = self.format_customer_name(line)
                if customer:
                    result['customer'] = customer
                
            # 尋找金額 - 支援多種格式
            if any(keyword in line for keyword in ['金額', '萬', '克', '額度', '收款金額', '儲值金額']):
                amount = self.format_amount(line)
                if amount:
                    result['amount'] = amount
                
            # 尋找時間 - 支援多種格式
            if any(keyword in line for keyword in ['時間', '點', '：', ':', '時', '預約時間', '收款時間']):
                time = self.format_time(line)
                if time:
                    result['time'] = time
                
            # 尋找地址 - 支援多種格式
            if any(keyword in line for keyword in ['地點', '地址', '交易地點', '收款地點', '預約地址']):
                address = self.format_address(line)
                if address:
                    result['address'] = address
                
            # 尋找公司名稱
            if '公司名稱' in line and '地址' not in line:
                company = self.format_company(line)
                if company:
                    result['company'] = company
        
        return result
    
    def validate_format(self, text):
        """驗證文本格式是否包含必要信息"""
        if not text or len(text.strip()) < 10:
            return False
        
        # 檢查是否包含至少一些關鍵字段
        keywords = ['姓名', '金額', '時間', '地址', '公司', '萬', '克', '點']
        found_keywords = sum(1 for keyword in keywords if keyword in text)
        
        return found_keywords >= 2
    
    def format_list(self, text):
        """格式化列表並返回結果"""
        try:
            parsed_data = self.parse_list_message(text)
            
            # 檢查缺失的字段
            missing_fields = []
            for field in self.required_fields:
                if not parsed_data[field]:
                    parsed_data[field] = "未知"
                    missing_fields.append(field)
            
            # 生成緊湊的格式化文本：姓名/時間/金額/地址/公司
            formatted_text = f"{parsed_data['customer']}/{parsed_data['time']}/{parsed_data['amount']}/{parsed_data['address']}/{parsed_data['company']}"
            
            return {
                'formatted_text': formatted_text,
                'missing_fields': missing_fields,
                'parsed_data': parsed_data
            }
            
        except Exception as e:
            logger.error(f"格式化列表時出錯: {str(e)}")
            return None