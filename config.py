import os
from binance.client import Client
import logging

class QuantumConfig:
    def __init__(self):
        # إعدادات API
        self.api_key = os.getenv('BINANCE_API_KEY', '')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY', '')
        self.testnet = os.getenv('TESTNET', 'true').lower() == 'true'
        self.trading_mode = os.getenv('TRADING_MODE', 'paper_trading')
        
        # إعدادات البوت
        self.initial_balance = float(os.getenv('INITIAL_BALANCE', '50'))
        self.cycle_interval = int(os.getenv('CYCLE_INTERVAL', '180'))
        self.max_trades_per_cycle = int(os.getenv('MAX_TRADES_PER_CYCLE', '3'))
        
        # إعدادات المخاطرة
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '0.03'))
        self.max_trade_loss = float(os.getenv('MAX_TRADE_LOSS', '0.015'))
        self.max_portfolio_risk = float(os.getenv('MAX_PORTFOLIO_RISK', '0.25'))
        
        # إعدادات التعلم
        self.learning_enabled = os.getenv('LEARNING_ENABLED', 'true').lower() == 'true'
        self.model_save_interval = int(os.getenv('MODEL_SAVE_INTERVAL', '20'))
        
        # العملات المستهدفة
        self.target_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT',
            'XRPUSDT', 'DOTUSDT', 'DOGEUSDT', 'MATICUSDT', 'AVAXUSDT'
        ]
        
        # إعدادات التسجيل
        self.log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
        
        print("🔧 Quantum Configuration Loaded")
    
    def get_client(self):
        """إنشاء عميل Binance مع معالجة الأخطاء"""
        try:
            if not self.api_key or not self.api_secret:
                print("⚠️ API keys not provided - Running in simulation mode")
                return None
            
            if self.testnet:
                client = Client(
                    self.api_key, 
                    self.api_secret,
                    testnet=True
                )
                print("🔗 Connected to Binance Testnet")
            else:
                client = Client(self.api_key, self.api_secret)
                print("🔗 Connected to Binance Live")
            
            # اختبار الاتصال
            client.get_account()
            print("✅ Binance connection validated")
            return client
            
        except Exception as e:
            print(f"❌ Binance connection failed: {e}")
            print("💡 Using simulation mode only")
            return None
    
    def validate_config(self):
        """التحقق من صحة الإعدادات"""
        errors = []
        warnings = []
        
        # فحص الإعدادات الحرجة
        if self.trading_mode == 'live_trading':
            if not self.api_key or not self.api_secret:
                errors.append("API keys are required for live trading")
            
            if self.initial_balance < 100:
                warnings.append("Low initial balance for live trading")
        
        if self.initial_balance < 10:
            errors.append("Initial balance must be at least $10")
        
        if self.cycle_interval < 60:
            errors.append("Cycle interval must be at least 60 seconds")
        
        if self.max_daily_loss > 0.1:
            warnings.append("High daily loss limit configured")
        
        # نتائج التحقق
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
        
        if warnings:
            print("⚠️ Configuration warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        
        return len(errors) == 0
    
    def get_trading_hours(self):
        """الحصول على ساعات التداول المفضلة"""
        # التركيز على أوقات السيولة العالية
        return {
            'london_open': (8, 0),    # 8:00 GMT
            'ny_open': (13, 30),       # 13:30 GMT
            'asia_open': (0, 0),       # 00:00 GMT
            'preferred_hours': [(8, 17)]  # 8 AM to 5 PM GMT
        }
    
    def get_risk_parameters(self):
        """الحصول على معاملات المخاطرة"""
        return {
            'position_size_range': (0.02, 0.15),  # 2% إلى 15%
            'stop_loss_range': (0.01, 0.03),      # 1% إلى 3%
            'take_profit_range': (0.02, 0.05),    # 2% إلى 5%
            'risk_reward_ratio': (1.5, 3.0)       # نسبة المخاطرة إلى العائد
        }
    
    def get_performance_targets(self):
        """الحصول على أهداف الأداء"""
        return {
            'daily_target': 0.02,      # 2% يومياً
            'weekly_target': 0.10,     # 10% أسبوعياً
            'monthly_target': 0.30,    # 30% شهرياً
            'quarterly_target': 1.00,  # 100% ربع سنوياً (10x في 3 أشهر)
            'max_drawdown_limit': 0.15 # 15% حد أقصى للتراجع
        }

# كائن الإعدادات العالمي
quantum_config = QuantumConfig()
