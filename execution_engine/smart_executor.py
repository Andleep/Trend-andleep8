import time
import random
from datetime import datetime
import pandas as pd
import numpy as np

class SmartExecutor:
    def __init__(self, mode='paper_trading'):
        self.mode = mode
        self.execution_history = []
        self.performance_metrics = {
            'success_rate': 0,
            'avg_slippage': 0,
            'avg_execution_time': 0,
            'total_executions': 0
        }
        
    def execute_trade(self, symbol, direction, amount, stop_loss, take_profit):
        """تنفيذ صفقة ذكي مع إدارة متقدمة"""
        execution_start = datetime.now()
        
        try:
            # 1. التحضير للتنفيذ
            preparation_result = self.prepare_execution(symbol, direction, amount)
            if not preparation_result['ready']:
                return {
                    'success': False,
                    'error': preparation_result['reason'],
                    'profit': 0
                }
            
            # 2. الحصول على السعر الأمثل
            optimal_price = self.get_optimal_price(symbol, direction, amount)
            
            # 3. تنفيذ الصفقة
            if self.mode == 'paper_trading':
                execution_result = self.execute_paper_trade(
                    symbol, direction, amount, optimal_price, stop_loss, take_profit
                )
            else:
                execution_result = self.execute_live_trade(
                    symbol, direction, amount, optimal_price
                )
            
            # 4. تسجيل التنفيذ
            execution_time = (datetime.now() - execution_start).total_seconds()
            execution_record = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'direction': direction,
                'amount': amount,
                'price': optimal_price,
                'execution_time': execution_time,
                'success': execution_result['success'],
                'profit': execution_result.get('profit', 0),
                'slippage': execution_result.get('slippage', 0)
            }
            
            self.execution_history.append(execution_record)
            self.update_performance_metrics(execution_record)
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Execution error for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'profit': 0
            }
    
    def prepare_execution(self, symbol, direction, amount):
        """التحضير للتنفيذ والتحقق من الجدوى"""
        checks = {
            'ready': True,
            'reason': None
        }
        
        # 1. فحص السيولة
        liquidity_check = self.check_liquidity(symbol, amount)
        if not liquidity_check['sufficient']:
            checks['ready'] = False
            checks['reason'] = f"سيولة غير كافية: {liquidity_check['message']}"
            return checks
        
        # 2. فحص التقلب
        volatility_check = self.check_volatility(symbol)
        if volatility_check['high_risk']:
            checks['ready'] = False
            checks['reason'] = f"تقلب مرتفع: {volatility_check['message']}"
            return checks
        
        # 3. فحص ظروف السوق
        market_conditions = self.analyze_market_conditions(symbol)
        if market_conditions['unfavorable']:
            checks['ready'] = False
            checks['reason'] = f"ظروف سوق غير مناسبة: {market_conditions['message']}"
            return checks
        
        return checks
    
    def check_liquidity(self, symbol, amount):
        """فحص سيولة السوق للكمية المطلوبة"""
        # في التطبيق الحقيقي، نتحقق من عمق السوق
        # هنا محاكاة مبسطة
        
        # افتراض سيولة كافية للكميات المعقولة
        sufficient = amount <= 10000  # حد افتراضي
        
        return {
            'sufficient': sufficient,
            'message': 'الكمية ضمن الحدود المقبولة' if sufficient else 'الكمية تتجاوز سيولة السوق'
        }
    
    def check_volatility(self, symbol):
        """فحص تقلب السوق"""
        # محاكاة تحليل التقلب
        current_volatility = random.uniform(0.01, 0.05)
        high_risk = current_volatility > 0.04
        
        return {
            'high_risk': high_risk,
            'current_volatility': current_volatility,
            'message': f'التقلب الحالي: {current_volatility:.2%}'
        }
    
    def analyze_market_conditions(self, symbol):
        """تحليل ظروف السوق العامة"""
        # محاكاة تحليل ظروف السوق
        conditions = {
            'unfavorable': False,
            'message': 'ظروف سوق مناسبة'
        }
        
        # فحص أوقات التقلب العالي (مثل إعلانات الأخبار)
        current_hour = datetime.now().hour
        if current_hour in [14, 15]:  # وقت إعلانات أمريكية
            conditions['unfavorable'] = True
            conditions['message'] = 'وقت إعلانات رئيسية - تجنب التداول'
        
        return conditions
    
    def get_optimal_price(self, symbol, direction, amount):
        """الحصول على السعر الأمثل للتنفيذ"""
        base_price = self.get_current_market_price(symbol)
        
        # حساب الانزلاق السعري المتوقع
        expected_slippage = self.calculate_expected_slippage(symbol, direction, amount)
        
        if direction == 'BUY':
            optimal_price = base_price * (1 + expected_slippage)
        else:  # SELL
            optimal_price = base_price * (1 - expected_slippage)
        
        return optimal_price
    
    def get_current_market_price(self, symbol):
        """الحصول على السعر السوقي الحالي"""
        # في التطبيق الحقيقي، نستخدم API البورصة
        # هنا نعيد سعرًا عشوائيًا واقعيًا
        price_ranges = {
            'BTCUSDT': (25000, 35000),
            'ETHUSDT': (1500, 2500),
            'BNBUSDT': (200, 400),
            'SOLUSDT': (20, 60),
            'ADAUSDT': (0.3, 0.6),
            'XRPUSDT': (0.4, 0.8),
            'DOTUSDT': (4, 8),
            'DOGEUSDT': (0.05, 0.15),
            'MATICUSDT': (0.5, 1.0),
            'AVAXUSDT': (10, 20)
        }
        
        price_range = price_ranges.get(symbol, (10, 100))
        return random.uniform(price_range[0], price_range[1])
    
    def calculate_expected_slippage(self, symbol, direction, amount):
        """حساب الانزلاق السعري المتوقع"""
        base_slippage = 0.001  # 0.1% انزلاق أساسي
        
        # تعديل بناءً على الحجم
        size_multiplier = min(amount / 5000, 2.0)  # مضاعفة الانزلاق للحجم الكبير
        
        # تعديل بناءً على السيولة (مبسط)
        liquidity_tiers = {
            'BTCUSDT': 0.8, 'ETHUSDT': 0.9, 'BNBUSDT': 1.0,
            'SOLUSDT': 1.2, 'ADAUSDT': 1.5, 'XRPUSDT': 1.3,
            'DOTUSDT': 1.4, 'DOGEUSDT': 1.8, 'MATICUSDT': 1.3,
            'AVAXUSDT': 1.4
        }
        
        liquidity_factor = liquidity_tiers.get(symbol, 1.5)
        
        expected_slippage = base_slippage * size_multiplier * liquidity_factor
        
        return min(expected_slippage, 0.01)  # حد أقصى 1% انزلاق
    
    def execute_paper_trade(self, symbol, direction, amount, entry_price, stop_loss, take_profit):
        """تنفيذ صفقة ورقية (محاكاة)"""
        try:
            # محاكاة حركة السعر بعد الدخول
            price_movement = self.simulate_price_movement(symbol, direction)
            exit_price = entry_price * (1 + price_movement)
            
            # تطبيق وقف الخسارة وجني الربح
            if direction == 'BUY':
                if exit_price <= stop_loss:
                    exit_price = stop_loss
                elif exit_price >= take_profit:
                    exit_price = take_profit
                
                profit = (exit_price - entry_price) * (amount / entry_price)
            else:  # SELL
                if exit_price >= stop_loss:
                    exit_price = stop_loss
                elif exit_price <= take_profit:
                    exit_price = take_profit
                
                profit = (entry_price - exit_price) * (amount / entry_price)
            
            # حساب الانزلاق الفعلي
            actual_slippage = abs(exit_price - entry_price) / entry_price
            
            return {
                'success': True,
                'profit': profit,
                'exit_price': exit_price,
                'slippage': actual_slippage,
                'efficiency_score': self.calculate_efficiency_score(actual_slippage, profit)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Paper trade execution failed: {e}",
                'profit': 0
            }
    
    def simulate_price_movement(self, symbol, direction):
        """محاكاة حركة السعر الواقعية"""
        # تقلب واقعي بناءً على نوع العملة
        volatility_profiles = {
            'BTCUSDT': 0.008,   # 0.8%
            'ETHUSDT': 0.010,   # 1.0%
            'BNBUSDT': 0.012,   # 1.2%
            'SOLUSDT': 0.015,   # 1.5%
            'ADAUSDT': 0.018,   # 1.8%
            'XRPUSDT': 0.016,   # 1.6%
            'DOTUSDT': 0.014,   # 1.4%
            'DOGEUSDT': 0.020,  # 2.0%
            'MATICUSDT': 0.015, # 1.5%
            'AVAXUSDT': 0.016   # 1.6%
        }
        
        base_volatility = volatility_profiles.get(symbol, 0.01)
        
        # حركة سعرية عشوائية مع اتجاه متوقع
        if direction == 'BUY':
            # اتجاه إيجابي محتمل للشراء
            movement = random.normalvariate(0.005, base_volatility)
        else:  # SELL
            # اتجاه سلبي محتمل للبيع
            movement = random.normalvariate(-0.005, base_volatility)
        
        return movement
    
    def execute_live_trade(self, symbol, direction, amount, price):
        """تنفيذ صفقة حقيقية (في الإصدار الحقيقي)"""
        # في التطبيق الحقيقي، نستخدم API البورصة
        # هذا هيكل أساسي للتنفيذ الحقيقي
        
        try:
            """
            # مثال باستخدام python-binance
            from binance.client import Client
            
            client = Client(api_key, api_secret)
            
            if direction == 'BUY':
                order = client.order_market_buy(
                    symbol=symbol,
                    quantity=amount
                )
            else:
                order = client.order_market_sell(
                    symbol=symbol,
                    quantity=amount
                )
            
            executed_price = float(order['fills'][0]['price'])
            executed_qty = float(order['executedQty'])
            
            profit = self.calculate_live_profit(direction, executed_price, executed_qty, price)
            
            return {
                'success': True,
                'profit': profit,
                'executed_price': executed_price,
                'executed_qty': executed_qty
            }
            """
            
            # محاكاة للتنفيذ الحقيقي
            executed_price = price * (1 + random.uniform(-0.002, 0.002))
            profit = (executed_price - price) * (amount / price) if direction == 'BUY' else (price - executed_price) * (amount / price)
            
            return {
                'success': True,
                'profit': profit,
                'executed_price': executed_price,
                'slippage': abs(executed_price - price) / price
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Live trade execution failed: {e}",
                'profit': 0
            }
    
    def calculate_efficiency_score(self, slippage, profit):
        """حساب كفاءة التنفيذ"""
        # كفاءة عالية عندما يكون الانزلاق منخفضاً والربح مرتفعاً
        slippage_score = 1 - min(slippage / 0.01, 1.0)  # 1% انزلاق = صفر
        profit_score = min(abs(profit) / (100), 1.0)    # ربح $100 = 1
        
        efficiency = (slippage_score * 0.6 + profit_score * 0.4)
        return efficiency
    
    def update_performance_metrics(self, execution_record):
        """تحديث مقاييس أداء التنفيذ"""
        successful_executions = [e for e in self.execution_history if e['success']]
        
        if successful_executions:
            self.performance_metrics['total_executions'] = len(successful_executions)
            self.performance_metrics['success_rate'] = len(successful_executions) / len(self.execution_history)
            self.performance_metrics['avg_slippage'] = np.mean([e['slippage'] for e in successful_executions])
            self.performance_metrics['avg_execution_time'] = np.mean([e['execution_time'] for e in successful_executions])
    
    def get_market_data(self, symbol, interval='1h', limit=100):
        """جلب بيانات السوق (محاكاة)"""
        # في التطبيق الحقيقي، نستخدم API البورصة
        dates = pd.date_range(end=datetime.now(), periods=limit, freq=interval)
        
        # محاكاة بيانات واقعية
        base_price = self.get_current_market_price(symbol)
        prices = [base_price]
        
        for i in range(1, limit):
            change = random.normalvariate(0, 0.002)  # تقلب 0.2%
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        df = pd.DataFrame({
            'open': [p * random.uniform(0.998, 1.002) for p in prices],
            'high': [p * random.uniform(1.001, 1.005) for p in prices],
            'low': [p * random.uniform(0.995, 0.999) for p in prices],
            'close': prices,
            'volume': [random.uniform(1000, 10000) for _ in prices],
            'timestamp': dates
        })
        
        return df
    
    def get_execution_analytics(self):
        """الحصول على تحليلات التنفيذ"""
        recent_executions = self.execution_history[-50:] if self.execution_history else []
        
        if not recent_executions:
            return {
                'total_trades': 0,
                'success_rate': 0,
                'avg_slippage': 0,
                'efficiency_trend': 'NEUTRAL'
            }
        
        successful_trades = [e for e in recent_executions if e['success']]
        success_rate = len(successful_trades) / len(recent_executions)
        
        # اتجاه الكفاءة
        if len(recent_executions) >= 10:
            first_half = recent_executions[:10]
            second_half = recent_executions[-10:]
            first_efficiency = np.mean([e.get('efficiency_score', 0.5) for e in first_half])
            second_efficiency = np.mean([e.get('efficiency_score', 0.5) for e in second_half])
            
            if second_efficiency > first_efficiency + 0.1:
                efficiency_trend = 'IMPROVING'
            elif second_efficiency < first_efficiency - 0.1:
                efficiency_trend = 'DECLINING'
            else:
                efficiency_trend = 'STABLE'
        else:
            efficiency_trend = 'NEUTRAL'
        
        return {
            'total_trades': len(recent_executions),
            'success_rate': success_rate,
            'avg_slippage': self.performance_metrics['avg_slippage'],
            'avg_execution_time': self.performance_metrics['avg_execution_time'],
            'efficiency_trend': efficiency_trend
        }
