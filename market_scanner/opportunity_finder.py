import numpy as np
import pandas as pd
from datetime import datetime

class OpportunityFinder:
    def __init__(self):
        self.opportunity_metrics = {}
        self.market_conditions = {}
        self.scan_history = []
    
    def scan_high_probability_opportunities(self, market_data, top_n=5):
        """مسح الفرص عالية الاحتمال"""
        opportunities = []
        
        for symbol, data in market_data.items():
            if symbol == 'symbol':
                continue
                
            # تحليل متعدد الأبعاد للفرص
            opportunity_score = self.calculate_opportunity_score(data)
            trend_direction = self.determine_trend_direction(data)
            momentum_strength = self.assess_momentum_strength(data)
            volatility_profile = self.analyze_volatility_profile(data)
            
            if opportunity_score > 0.6:  # فرص ذات جودة عالية فقط
                opportunities.append({
                    'symbol': symbol,
                    'score': opportunity_score,
                    'direction': trend_direction,
                    'momentum': momentum_strength,
                    'volatility': volatility_profile,
                    'entry_confidence': self.calculate_entry_confidence(data, trend_direction),
                    'timestamp': datetime.now()
                })
        
        # ترتيب الفرص حسب الجودة
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # حفظ تاريخ المسح
        self.scan_history.append({
            'timestamp': datetime.now(),
            'opportunities_found': len(opportunities),
            'top_opportunity': opportunities[0] if opportunities else None
        })
        
        return opportunities[:top_n]
    
    def calculate_opportunity_score(self, data):
        """حساب درجة الفرصة الشاملة"""
        scores = []
        
        # 1. تحليل الاتجاه
        trend_score = self.analyze_trend_quality(data)
        scores.append(trend_score * 0.3)
        
        # 2. تحليل الزخم
        momentum_score = self.analyze_momentum_quality(data)
        scores.append(momentum_score * 0.25)
        
        # 3. تحليل التقلب
        volatility_score = self.analyze_volatility_quality(data)
        scores.append(volatility_score * 0.2)
        
        # 4. تحليل الحجم
        volume_score = self.analyze_volume_quality(data)
        scores.append(volume_score * 0.15)
        
        # 5. تحليل السيولة
        liquidity_score = self.analyze_liquidity_quality(data)
        scores.append(liquidity_score * 0.1)
        
        return sum(scores)
    
    def analyze_trend_quality(self, data):
        """تحليل جودة الاتجاه"""
        if data['1h'].empty or len(data['1h']) < 50:
            return 0.5
        
        df = data['1h']
        
        # المتوسطات المتحركة
        sma_20 = df['close'].rolling(20).mean()
        sma_50 = df['close'].rolling(50).mean()
        
        # اتجاه المتوسطات
        sma_trend = 1.0 if sma_20.iloc[-1] > sma_50.iloc[-1] else 0.0
        
        # قوة الاتجاه
        trend_strength = abs(sma_20.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1]
        
        # استقرار الاتجاه
        recent_trend = (df['close'].iloc[-1] / df['close'].iloc[-20] - 1)
        trend_consistency = 1.0 if abs(recent_trend) > 0.02 else 0.5
        
        return (sma_trend * 0.4 + min(trend_strength / 0.05, 1.0) * 0.4 + trend_consistency * 0.2)
    
    def analyze_momentum_quality(self, data):
        """تحليل جودة الزخم"""
        if data['15m'].empty or len(data['15m']) < 14:
            return 0.5
        
        df = data['15m']
        
        # RSI
        rsi = self.calculate_rsi(df['close'], 14)
        rsi_score = 0.0
        if rsi[-1] < 30:  # ذروة بيع
            rsi_score = (30 - rsi[-1]) / 30
        elif rsi[-1] > 70:  # ذروة شراء
            rsi_score = (rsi[-1] - 70) / 30
        
        # MACD
        macd, signal = self.calculate_macd(df['close'])
        macd_score = 1.0 if macd[-1] > signal[-1] else 0.0
        
        # Stochastic
        stoch = self.calculate_stochastic(df, 14)
        stoch_score = 0.0
        if stoch[-1] < 20:  # ذروة بيع
            stoch_score = (20 - stoch[-1]) / 20
        elif stoch[-1] > 80:  # ذروة شراء
            stoch_score = (stoch[-1] - 80) / 20
        
        return (rsi_score * 0.4 + macd_score * 0.3 + stoch_score * 0.3)
    
    def analyze_volatility_quality(self, data):
        """تحليل جودة التقلب"""
        if data['1h'].empty or len(data['1h']) < 20:
            return 0.5
        
        df = data['1h']
        
        # حساب التقلب
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(24)  # تقلب يومي
        
        # تقلب مثالي للتداول (1-3%)
        ideal_volatility_min = 0.01
        ideal_volatility_max = 0.03
        
        if volatility < ideal_volatility_min:
            # تقلب منخفض جداً - فرص محدودة
            return volatility / ideal_volatility_min * 0.5
        elif volatility > ideal_volatility_max:
            # تقلب مرتفع جداً - مخاطرة عالية
            excess_volatility = volatility - ideal_volatility_max
            return max(0.5 - (excess_volatility / ideal_volatility_max), 0.2)
        else:
            # تقلب مثالي
            return 1.0
    
    def analyze_volume_quality(self, data):
        """تحليل جودة الحجم"""
        if data['1h'].empty or len(data['1h']) < 20:
            return 0.5
        
        df = data['1h']
        
        # متوسط الحجم
        avg_volume = df['volume'].mean()
        
        # حجم حديث
        recent_volume = df['volume'].tail(5).mean()
        
        # نسبة الحجم
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        # حجم عالي = اهتمام = جودة أفضل
        return min(volume_ratio / 2, 1.0)
    
    def analyze_liquidity_quality(self, data):
        """تحليل جودة السيولة"""
        # في التطبيق الحقيقي، نتحقق من فروق الأسعار وعمق السوق
        # هنا نستخدم بيانات حجم مبسطة
        if data['1h'].empty:
            return 0.5
        
        df = data['1h']
        avg_volume = df['volume'].mean()
        
        # سيولة جيدة إذا كان الحجم فوق 1M
        if avg_volume > 1000000:
            return 1.0
        elif avg_volume > 500000:
            return 0.7
        elif avg_volume > 100000:
            return 0.4
        else:
            return 0.2
    
    def determine_trend_direction(self, data):
        """تحديد اتجاه الاتجاه"""
        if data['1h'].empty or len(data['1h']) < 50:
            return 'SIDEWAYS'
        
        df = data['1h']
        
        sma_20 = df['close'].rolling(20).mean()
        sma_50 = df['close'].rolling(50).mean()
        
        if sma_20.iloc[-1] > sma_50.iloc[-1] and df['close'].iloc[-1] > sma_20.iloc[-1]:
            return 'UPTREND'
        elif sma_20.iloc[-1] < sma_50.iloc[-1] and df['close'].iloc[-1] < sma_20.iloc[-1]:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def assess_momentum_strength(self, data):
        """تقييم قوة الزخم"""
        if data['15m'].empty or len(data['15m']) < 14:
            return 'NEUTRAL'
        
        df = data['15m']
        
        rsi = self.calculate_rsi(df['close'], 14)
        macd, signal = self.calculate_macd(df['close'])
        
        if rsi[-1] > 70 and macd[-1] > signal[-1]:
            return 'STRONG_BULLISH'
        elif rsi[-1] < 30 and macd[-1] < signal[-1]:
            return 'STRONG_BEARISH'
        elif rsi[-1] > 60 and macd[-1] > signal[-1]:
            return 'BULLISH'
        elif rsi[-1] < 40 and macd[-1] < signal[-1]:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def analyze_volatility_profile(self, data):
        """تحليل ملف التقلب"""
        if data['1h'].empty or len(data['1h']) < 20:
            return 'UNKNOWN'
        
        df = data['1h']
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(24)
        
        if volatility > 0.04:
            return 'HIGH'
        elif volatility > 0.02:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def calculate_entry_confidence(self, data, direction):
        """ثقة الدخول للصفقة"""
        confidence_factors = []
        
        # محاذاة الإطار الزمني
        if self.check_timeframe_alignment(data, direction):
            confidence_factors.append(0.3)
        
        # تأكيد الحجم
        if self.check_volume_confirmation(data, direction):
            confidence_factors.append(0.3)
        
        # تأكيد الزخم
        if self.check_momentum_confirmation(data, direction):
            confidence_factors.append(0.2)
        
        # تأكيد النمط
        if self.check_pattern_confirmation(data, direction):
            confidence_factors.append(0.2)
        
        return sum(confidence_factors)
    
    def check_timeframe_alignment(self, data, direction):
        """التحقق من محاذاة الأطر الزمنية"""
        timeframes = ['1h', '15m', '5m']
        aligned_count = 0
        
        for tf in timeframes:
            if tf in data and not data[tf].empty:
                tf_direction = self.determine_trend_direction({tf: data[tf]})
                if tf_direction == direction:
                    aligned_count += 1
        
        return aligned_count >= 2  # محاذاة على إطارين على الأقل
    
    def check_volume_confirmation(self, data, direction):
        """التحقق من تأكيد الحجم"""
        if '1h' not in data or data['1h'].empty:
            return False
        
        df = data['1h']
        recent_volume = df['volume'].tail(5).mean()
        historical_volume = df['volume'].mean()
        
        # حجم أعلى من المتوسط يؤكد الاتجاه
        return recent_volume > historical_volume * 1.2
    
    def check_momentum_confirmation(self, data, direction):
        """التحقق من تأكيد الزخم"""
        if '15m' not in data or data['15m'].empty:
            return False
        
        momentum = self.assess_momentum_strength(data)
        
        if direction == 'UPTREND' and momentum in ['BULLISH', 'STRONG_BULLISH']:
            return True
        elif direction == 'DOWNTREND' and momentum in ['BEARISH', 'STRONG_BEARISH']:
            return True
        
        return False
    
    def check_pattern_confirmation(self, data, direction):
        """التحقق من تأكيد النمط"""
        # تحقق مبسط من أنماط التأكيد
        if '15m' not in data or data['15m'].empty:
            return False
        
        df = data['15m']
        
        # تحقق من نمط الهبوط/الصعود المستمر
        if len(df) >= 3:
            recent_trend = (df['close'].iloc[-1] / df['close'].iloc[-3] - 1)
            if direction == 'UPTREND' and recent_trend > 0:
                return True
            elif direction == 'DOWNTREND' and recent_trend < 0:
                return True
        
        return False
    
    def calculate_rsi(self, prices, period=14):
        """حساب مؤشر RSI"""
        if len(prices) < period:
            return np.array([50] * len(prices))
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.convolve(gains, np.ones(period)/period, mode='valid')
        avg_losses = np.convolve(losses, np.ones(period)/period, mode='valid')
        
        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        rsi_full = np.concatenate([np.array([50] * (len(prices) - len(rsi))), rsi])
        
        return rsi_full
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """حساب مؤشر MACD"""
        if len(prices) < slow:
            return np.array([0] * len(prices)), np.array([0] * len(prices))
        
        exp1 = pd.Series(prices).ewm(span=fast).mean()
        exp2 = pd.Series(prices).ewm(span=slow).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal).mean()
        
        return macd.values, macd_signal.values
    
    def calculate_stochastic(self, data, period=14):
        """حساب مؤشر Stochastic"""
        if len(data) < period:
            return np.array([50] * len(data))
        
        lows = data['low'].rolling(period).min()
        highs = data['high'].rolling(period).max()
        
        stoch = 100 * (data['close'] - lows) / (highs - lows)
        return stoch.fillna(50).values
    
    def get_scan_statistics(self):
        """الحصول على إحصائيات المسح"""
        if not self.scan_history:
            return {}
        
        recent_scans = self.scan_history[-10:]  # آخر 10 مسوح
        
        avg_opportunities = np.mean([scan['opportunities_found'] for scan in recent_scans])
        avg_top_score = np.mean([scan['top_opportunity']['score'] for scan in recent_scans if scan['top_opportunity']])
        
        return {
            'total_scans': len(self.scan_history),
            'avg_opportunities_per_scan': avg_opportunities,
            'avg_top_opportunity_score': avg_top_score,
            'scan_success_rate': min(avg_opportunities / 5, 1.0)  # نجاح نسبي
        }
