import util
import yfinance as yf
from datetime import datetime, timedelta
import ssl
import requests
import json
import certifi
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Stock:
    def __init__(self, name, initial_price, initial_stock, is_new=False, symbol=None):
        self.name = name
        self.price = initial_price
        self.ideal_price = 0
        self.initial_stock = initial_stock
        self.history = {}   # {date: session_deal}
        self.session_deal = [] # [{"price", "amount"}]
        self.symbol = symbol  # Ticker symbol (e.g., "NVDA")
        self.real_prices = []  # Gerçek fiyat geçmişi
        
        # Eğer gerçek veri kullanılacaksa, fiyatları çek
        if util.USE_REAL_DATA and symbol:
            self._fetch_real_prices()

    def _fetch_real_prices(self):
        """NVIDIA icin gercek NASDAQ fiyatlarini cek (son 2 yil)"""
        print(f"{self.symbol} icin son 2 yillik veri cekiliyor...")
        
        # 1. Yahoo Query API (en hızlı ve güvenilir - SSL sorunu yok)
        success = self._fetch_from_alternative()
        
        # 2. Başarısızsa yfinance dene
        if not success:
            print("Yahoo Query basarisiz, yfinance deneniyor...")
            success = self._fetch_from_yahoo()
        
        # 3. Hala başarısızsa Alpha Vantage dene
        if not success:
            print("yfinance basarisiz, Alpha Vantage deneniyor...")
            success = self._fetch_from_alphavantage()
        
        # 4. Son çare: Polygon.io
        if not success:
            print("Alpha Vantage basarisiz, Polygon.io deneniyor...")
            success = self._fetch_from_polygon()
        
        if not success:
            print(f"Tum kaynaklar basarisiz, baslangic fiyati: ${self.price:.2f}")
    
    def _fetch_from_yahoo(self):
        """Yahoo Finance'den veri çek"""
        try:
            # SSL sertifika sorununu çöz
            import ssl
            import certifi
            import urllib3
            
            # Sertifika doğrulamasını devre dışı bırak (geçici)
            ssl._create_default_https_context = ssl._create_unverified_context
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            ticker = yf.Ticker(self.symbol)
            
            # Son 2 yıllık veri (730 gün)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty and len(hist) > 0:
                self.real_prices = hist['Close'].tolist()
                self.price = self.real_prices[-1]  # En son fiyatla başla (bugünkü)
                
                print(f"Yahoo Finance: {len(self.real_prices)} gunluk veri")
                print(f"Guncel Fiyat: ${self.price:.2f}")
                print(f"Aralik: ${min(self.real_prices):.2f} - ${max(self.real_prices):.2f}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Yahoo Finance hatasi: {str(e)[:100]}")
            return False
    
    def _fetch_from_alternative(self):
        """Alternatif kaynaklardan veri çek"""
        try:
            # Yahoo Finance Query API (alternatif endpoint)
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.symbol}"
            params = {
                'range': '2y',
                'interval': '1d'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    
                    # Fiyat verilerini al
                    closes = result['indicators']['quote'][0]['close']
                    self.real_prices = [p for p in closes if p is not None]
                    
                    if self.real_prices:
                        self.price = self.real_prices[-1]  # En son fiyat
                        
                        print(f"Alternatif API: {len(self.real_prices)} gunluk veri")
                        print(f"Guncel Fiyat: ${self.price:.2f}")
                        print(f"Aralik: ${min(self.real_prices):.2f} - ${max(self.real_prices):.2f}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"Alternatif API hatasi: {str(e)[:100]}")
            return False
    
    def _fetch_from_alphavantage(self):
        """Alpha Vantage API'den veri cek (ucretsiz, gunluk limit var)"""
        try:
            # Alpha Vantage ucretsiz API key: demo
            api_key = "demo"  # util.py'ye eklenebilir
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': self.symbol,
                'outputsize': 'full',
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=15, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']
                    
                    # Son 730 gunu al
                    prices = []
                    for date_str in sorted(time_series.keys())[-730:]:
                        close_price = float(time_series[date_str]['4. close'])
                        prices.append(close_price)
                    
                    if prices:
                        self.real_prices = prices
                        self.price = prices[-1]
                        
                        print(f"Alpha Vantage: {len(self.real_prices)} gunluk veri")
                        print(f"Guncel Fiyat: ${self.price:.2f}")
                        print(f"Aralik: ${min(self.real_prices):.2f} - ${max(self.real_prices):.2f}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"Alpha Vantage hatasi: {str(e)[:100]}")
            return False
    
    def _fetch_from_polygon(self):
        """Polygon.io'dan veri cek (bedava tier)"""
        try:
            # Polygon.io bedava API
            url = f"https://api.polygon.io/v2/aggs/ticker/{self.symbol}/range/1/day"
            
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)
            
            params = {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 5000,
                'apiKey': 'DEMO'  # Demo key, sinirli
            }
            
            response = requests.get(url, params=params, timeout=15, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'results' in data and data['results']:
                    prices = [result['c'] for result in data['results']]  # c = close price
                    
                    if prices:
                        self.real_prices = prices
                        self.price = prices[-1]
                        
                        print(f"Polygon.io: {len(self.real_prices)} gunluk veri")
                        print(f"Guncel Fiyat: ${self.price:.2f}")
                        print(f"Aralik: ${min(self.real_prices):.2f} - ${max(self.real_prices):.2f}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"Polygon.io hatasi: {str(e)[:100]}")
            return False
    
    def gen_financial_report(self, index):
        if self.name == "A":
            return util.FINANCIAL_REPORT_A[index]
        elif self.name == "B":
            return util.FINANCIAL_REPORT_B[index] if hasattr(util, 'FINANCIAL_REPORT_B') else ""

    def add_session_deal(self, price_and_amount):
        self.session_deal.append(price_and_amount)

    def update_price(self, date):
        # Gerçek veri kullanılıyorsa ve mevcutsa
        if util.USE_REAL_DATA and self.real_prices and date <= len(self.real_prices):
            self.price = self.real_prices[date - 1]
        # Simülasyon verisi kullanılıyorsa
        elif len(self.session_deal) > 0:
            self.price = self.session_deal[-1]["price"]
        
        self.history[date] = self.session_deal.copy()
        self.session_deal.clear()

    def get_price(self):
        return self.price
