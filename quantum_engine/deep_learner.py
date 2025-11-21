import numpy as np
import pandas as pd
import json
import pickle
from datetime import datetime
from collections import deque
import warnings
warnings.filterwarnings('ignore')

class QuantumDeepLearner:
    def __init__(self):
        self.learning_memory = deque(maxlen=10000)
        self.pattern_database = {}
        self.strategy_performance = {}
        self.market_regime_knowledge = {}
        self.learning_progress = 0
        
        # تحميل المعرفة السابقة
        self.load_knowledge_base()
    
    def recognize_patterns(self, market_data):
        """التعرف على الأنماط السوقية المتقدمة"""
        patterns = {
            'trend_patterns': self.analyze_trend_patterns(market_data),
            'reversal_patterns': self.analyze_reversal_patterns(market_data),
            'consolidation_patterns': self.analyze_consolidation_patterns(market_data),
            'breakout_patterns': self.analyze_breakout_patterns(market_data),
            'confidence': 0.0
        }
        
        # حساب ثقة النمط
        patterns['confidence'] = self.calculate_pattern_confidence(patterns)
        
        return patterns
    
    def analyze_trend_patterns(self, market_data):
        """تحليل أنماط الاتجاه"""
        trends = {
            'uptrend_detected': False,
            'downtrend_detected': False,
            'trend_strength': 0.0,
            'trend_duration': 0,
            'acceleration': 0.0
        }
        
        # تحليل متعدد الأطر الزمنية
        for timeframe, data in market_data.items():
            if timeframe != 'symbol' and not data.empty:
                trend_analysis = self.calculate_trend_metrics(data)
                trends['uptrend_detected'] |= trend_analysis['is_uptrend']
                trends['downtrend_detected'] |= trend_analysis['is_downtrend']
                trends['trend_strength'] = max(trends['trend_strength'], trend_analysis['strength'])
                trends['acceleration'] = max(trends['acceleration'], trend_analysis['acceleration'])
        
        return trends
    
    def calculate_trend_metrics(self, data):
        """حساب مقاييس الاتجاه"""
        if len(data) < 20:
            return {'is_uptrend': False, 'is_downtrend': False, 'strength': 0.0, 'acceleration': 0.0}
        
        closes = data['close'].values
        
        # المتوسطات المتحركة
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-min(50, len(closes)):])
        
        # قوة الاتجاه
        trend_strength = abs(sma_20 - sma_50) / sma_50
        
        # التسارع
        recent_momentum = (closes[-1] / closes[-5] - 1) if len(closes) >= 5 else 0
        previous_momentum = (closes[-5] / closes[-10] - 1) if len(closes) >= 10 else 0
        acceleration = recent_momentum - previous_momentum
        
        return {
            'is_uptrend': sma_20 > sma_50,
            'is_downtrend': sma_20 < sma_50,
            'strength': trend_strength,
            'acceleration': acceleration
        }
    
    def analyze_reversal_patterns(self, market_data):
        """تحليل أنماط الانعكاس"""
        reversals = {
            'potential_reversal': False,
            'reversal_type': None,  # 'bullish' or 'bearish'
            'confidence': 0.0,
            'trigger_level': 0.0
        }
        
        # تحليل الشموع اليابانية
        candle_patterns = self.analyze_candlestick_patterns(market_data)
        
        # تحليل الـ RSI divergence
        rsi_divergence = self.analyze_rsi_divergence(market_data)
        
        if candle_patterns['reversal_detected'] or rsi_divergence['divergence_detected']:
            reversals['potential_reversal'] = True
            reversals['confidence'] = max(candle_patterns['confidence'], rsi_divergence['confidence'])
            reversals['reversal_type'] = candle_patterns.get('reversal_type') or rsi_divergence.get('reversal_type')
        
        return reversals
    
    def analyze_candlestick_patterns(self, market_data):
        """تحليل أنماط الشموع اليابانية"""
        patterns = {
            'reversal_detected': False,
            'reversal_type': None,
            'confidence': 0.0
        }
        
        # تحليل مبسط للشموع (في التطبيق الحقيقي يستخدم مكتبة متخصصة)
        for timeframe, data in market_data.items():
            if timeframe != 'symbol' and not data.empty and len(data) >= 3:
                recent_candles = data.tail(3)
                
                # نمط engulfing
                if self.is_bullish_engulfing(recent_candles):
                    patterns['reversal_detected'] = True
                    patterns['reversal_type'] = 'bullish'
                    patterns['confidence'] = 0.7
                
                elif self.is_bearish_engulfing(recent_candles):
                    patterns['reversal_detected'] = True
                    patterns['reversal_type'] = 'bearish'
                    patterns['confidence'] = 0.7
        
        return patterns
    
    def is_bullish_engulfing(self, candles):
        """الكشف عن نمط الـ Bullish Engulfing"""
        if len(candles) < 2:
            return False
        
        prev, curr = candles.iloc[-2], candles.iloc[-1]
        return (prev['close'] < prev['open'] and  # شمعة هابطة سابقة
                curr['close'] > curr['open'] and  # شمعة صاعدة حالية
                curr['open'] < prev['close'] and   # فتح الحالية أقل من إغلاق السابقة
                curr['close'] > prev['open'])      # إغلاق الحالية أعلى من فتح السابقة
    
    def is_bearish_engulfing(self, candles):
        """الكشف عن نمط الـ Bearish Engulfing"""
        if len(candles) < 2:
            return False
        
        prev, curr = candles.iloc[-2], candles.iloc[-1]
        return (prev['close'] > prev['open'] and  # شمعة صاعدة سابقة
                curr['close'] < curr['open'] and  # شمعة هابطة حالية
                curr['open'] > prev['close'] and   # فتح الحالية أعلى من إغلاق السابقة
                curr['close'] < prev['open'])      # إغلاق الحالية أقل من فتح السابقة
    
    def analyze_rsi_divergence(self, market_data):
        """تحليل الـ RSI divergence"""
        divergence = {
            'divergence_detected': False,
            'reversal_type': None,
            'confidence': 0.0
        }
        
        # تحليل مبسط للـ divergence
        for timeframe, data in market_data.items():
            if timeframe != 'symbol' and not data.empty and len(data) >= 20:
                rsi = self.calculate_rsi(data['close'], 14)
                prices = data['close'].values
                
                if len(rsi) >= 5:
                    # تح divergence بين السعر والـ RSI
                    price_trend = prices[-1] - prices[-5]
                    rsi_trend = rsi[-1] - rsi[-5]
                    
                    if price_trend > 0 and rsi_trend < 0:  # bearish divergence
                        divergence['divergence_detected'] = True
                        divergence['reversal_type'] = 'bearish'
                        divergence['confidence'] = 0.6
                    
                    elif price_trend < 0 and rsi_trend > 0:  # bullish divergence
                        divergence['divergence_detected'] = True
                        divergence['reversal_type'] = 'bullish'
                        divergence['confidence'] = 0.6
        
        return divergence
    
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
        
        # إضافة قيم للبداية لتتناسب مع طول prices
        rsi_full = np.concatenate([np.array([50] * (len(prices) - len(rsi))), rsi])
        
        return rsi_full
    
    def analyze_consolidation_patterns(self, market_data):
        """تحليل أنماط التجميع"""
        consolidation = {
            'in_consolidation': False,
            'consolidation_range': 0.0,
            'breakout_direction': None,
            'breakout_probability': 0.0
        }
        
        for timeframe, data in market_data.items():
            if timeframe != 'symbol' and not data.empty and len(data) >= 20:
                volatility = self.calculate_volatility(data)
                price_range = (data['high'].max() - data['low'].min()) / data['close'].mean()
                
                if volatility < 0.02 and price_range < 0.05:  # تقلب منخفض ونطاق سعري ضيق
                    consolidation['in_consolidation'] = True
                    consolidation['consolidation_range'] = price_range
                    consolidation['breakout_probability'] = self.calculate_breakout_probability(data)
        
        return consolidation
    
    def analyze_breakout_patterns(self, market_data):
        """تحليل أنماط الاختراق"""
        breakout = {
            'breakout_imminent': False,
            'expected_direction': None,
            'confidence': 0.0,
            'target_levels': {'short_term': 0, 'medium_term': 0}
        }
        
        for timeframe, data in market_data.items():
            if timeframe != 'symbol' and not data.empty and len(data) >= 30:
                # تحليل مستويات الدعم والمقاومة
                support, resistance = self.identify_support_resistance(data)
                current_price = data['close'].iloc[-1]
                
                # تحديد قرب السعر من المستويات الحرجة
                distance_to_resistance = abs(resistance - current_price) / current_price
                distance_to_support = abs(support - current_price) / current_price
                
                if distance_to_resistance < 0.01:  # قريب من المقاومة
                    breakout['breakout_imminent'] = True
                    breakout['expected_direction'] = 'bullish' if self.is_strong_bullish_momentum(data) else 'bearish'
                    breakout['confidence'] = 0.7
                
                elif distance_to_support < 0.01:  # قريب من الدعم
                    breakout['breakout_imminent'] = True
                    breakout['expected_direction'] = 'bullish' if self.is_strong_bullish_momentum(data) else 'bearish'
                    breakout['confidence'] = 0.7
        
        return breakout
    
    def calculate_volatility(self, data):
        """حساب التقلب"""
        returns = data['close'].pct_change().dropna()
        return returns.std() * np.sqrt(365)  # تقلب سنوي
    
    def calculate_breakout_probability(self, data):
        """حساب احتمالية الاختراق"""
        if len(data) < 20:
            return 0.5
        
        # عوامل مؤثرة في احتمالية الاختراق
        volume_trend = self.analyze_volume_trend(data)
        volatility_compression = self.analyze_volatility_compression(data)
        time_in_consolidation = min(len(data) / 50, 1.0)  # نسبة الوقت في التجميع
        
        probability = (volume_trend * 0.4 + volatility_compression * 0.3 + time_in_consolidation * 0.3)
        return min(probability, 1.0)
    
    def analyze_volume_trend(self, data):
        """تحليل اتجاه الحجم"""
        if len(data) < 10:
            return 0.5
        
        volumes = data['volume'].values
        recent_volume = np.mean(volumes[-5:])
        previous_volume = np.mean(volumes[-10:-5])
        
        if previous_volume == 0:
            return 0.5
        
        volume_ratio = recent_volume / previous_volume
        return min(volume_ratio / 2, 1.0)  # تطبيع
    
    def analyze_volatility_compression(self, data):
        """تحليل انضغاط التقلب"""
        if len(data) < 20:
            return 0.5
        
        recent_volatility = self.calculate_volatility(data.tail(10))
        historical_volatility = self.calculate_volatility(data)
        
        if historical_volatility == 0:
            return 0.5
        
        compression_ratio = recent_volatility / historical_volatility
        return 1 - min(compression_ratio, 1.0)  # انضغاط أعلى = احتمالية اختراق أعلى
    
    def identify_support_resistance(self, data):
        """تحديد مستويات الدعم والمقاومة"""
        if len(data) < 20:
            return data['low'].min(), data['high'].max()
        
        # طريقة مبسطة لتحديد الدعم والمقاومة
        support = data['low'].tail(20).min()
        resistance = data['high'].tail(20).max()
        
        return support, resistance
    
    def is_strong_bullish_momentum(self, data):
        """التحقق من وجود زخم صاعد قوي"""
        if len(data) < 10:
            return False
        
        recent_gain = (data['close'].iloc[-1] / data['close'].iloc[-5] - 1)
        volume_increase = (data['volume'].iloc[-1] / data['volume'].iloc[-5] - 1)
        
        return recent_gain > 0.02 and volume_increase > 0.1
    
    def calculate_pattern_confidence(self, patterns):
        """حساب ثقة الأنماط المكتشفة"""
        confidence_factors = []
        
        if patterns['trend_patterns']['trend_strength'] > 0.1:
            confidence_factors.append(0.3)
        
        if patterns['reversal_patterns']['confidence'] > 0:
            confidence_factors.append(patterns['reversal_patterns']['confidence'] * 0.3)
        
        if patterns['consolidation_patterns']['breakout_probability'] > 0.6:
            confidence_factors.append(0.2)
        
        if patterns['breakout_patterns']['confidence'] > 0:
            confidence_factors.append(patterns['breakout_patterns']['confidence'] * 0.2)
        
        return sum(confidence_factors) if confidence_factors else 0.0
    
    def update_learning(self, recent_trades, market_data):
        """تحديث التعلم من الصفقات الحديثة"""
        for trade in recent_trades:
            learning_insight = {
                'trade_data': trade,
                'market_conditions': self.extract_market_conditions(trade, market_data),
                'outcome': 'WIN' if trade['execution_result']['profit'] > 0 else 'LOSS',
                'timestamp': datetime.now(),
                'lessons_learned': self.extract_lessons(trade)
            }
            
            self.learning_memory.append(learning_insight)
            self.update_strategy_performance(learning_insight)
        
        self.learning_progress = min(len(self.learning_memory) / 1000, 1.0)
    
    def extract_market_conditions(self, trade, market_data):
        """استخراج ظروف السوق أثناء الصفقة"""
        symbol = trade['symbol']
        if symbol in market_data:
            data = market_data[symbol]
            return {
                'trend_strength': self.calculate_trend_metrics(data)['strength'],
                'volatility': self.calculate_volatility(data),
                'volume_profile': self.analyze_volume_profile(data),
                'market_regime': self.classify_market_regime(data)
            }
        return {}
    
    def analyze_volume_profile(self, data):
        """تحليل ملف الحجم"""
        if len(data) < 10:
            return 'UNKNOWN'
        
        recent_volume = data['volume'].tail(5).mean()
        historical_volume = data['volume'].mean()
        
        if recent_volume > historical_volume * 1.5:
            return 'HIGH_VOLUME'
        elif recent_volume < historical_volume * 0.5:
            return 'LOW_VOLUME'
        else:
            return 'NORMAL_VOLUME'
    
    def classify_market_regime(self, data):
        """تصنيف النظام السوقي"""
        volatility = self.calculate_volatility(data)
        trend_strength = self.calculate_trend_metrics(data)['strength']
        
        if volatility > 0.03:
            return 'HIGH_VOLATILITY'
        elif trend_strength > 0.05:
            return 'TRENDING'
        else:
            return 'SIDEWAYS'
    
    def extract_lessons(self, trade):
        """استخراج الدروس المستفادة من الصفقة"""
        profit = trade['execution_result']['profit']
        expected_profit = trade.get('expected_profit', 0)
        
        lessons = []
        
        if profit > 0:
            if profit > expected_profit * 1.2:
                lessons.append("STRONG_SIGNAL_CONFIRMATION")
            else:
                lessons.append("MODERATE_SUCCESS")
        else:
            if abs(profit) > trade.get('max_loss', 0) * 0.8:
                lessons.append("RISK_MANAGEMENT_WORKED")
            else:
                lessons.append("NEED_BETTER_ENTRY")
        
        return lessons
    
    def update_strategy_performance(self, learning_insight):
        """تحديث أداء الاستراتيجيات"""
        strategy = learning_insight['trade_data'].get('strategy', 'default')
        outcome = learning_insight['outcome']
        
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {'wins': 0, 'losses': 0, 'total_profit': 0}
        
        if outcome == 'WIN':
            self.strategy_performance[strategy]['wins'] += 1
            self.strategy_performance[strategy]['total_profit'] += learning_insight['trade_data']['execution_result']['profit']
        else:
            self.strategy_performance[strategy]['losses'] += 1
            self.strategy_performance[strategy]['total_profit'] += learning_insight['trade_data']['execution_result']['profit']
    
    def get_best_strategies(self, top_n=3):
        """الحصول على أفضل الاستراتيجيات أداءً"""
        if not self.strategy_performance:
            return []
        
        strategies = []
        for strategy, performance in self.strategy_performance.items():
            total_trades = performance['wins'] + performance['losses']
            win_rate = performance['wins'] / total_trades if total_trades > 0 else 0
            avg_profit = performance['total_profit'] / total_trades if total_trades > 0 else 0
            
            strategies.append({
                'strategy': strategy,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'total_trades': total_trades,
                'score': win_rate * avg_profit * min(total_trades / 10, 1.0)
            })
        
        strategies.sort(key=lambda x: x['score'], reverse=True)
        return strategies[:top_n]
    
    def save_model(self):
        """حفظ نموذج التعلم"""
        try:
            knowledge = {
                'learning_memory': list(self.learning_memory),
                'pattern_database': self.pattern_database,
                'strategy_performance': self.strategy_performance,
                'market_regime_knowledge': self.market_regime_knowledge,
                'learning_progress': self.learning_progress,
                'last_updated': datetime.now().isoformat()
            }
            
            with open('data/models/quantum_knowledge.pkl', 'wb') as f:
                pickle.dump(knowledge, f)
            
            print("💾 Quantum learning model saved")
        except Exception as e:
            print(f"⚠️ Error saving quantum model: {e}")
    
    def load_knowledge_base(self):
        """تحميل قاعدة المعرفة"""
        try:
            with open('data/models/quantum_knowledge.pkl', 'rb') as f:
                knowledge = pickle.load(f)
                
            self.learning_memory = deque(knowledge.get('learning_memory', []), maxlen=10000)
            self.pattern_database = knowledge.get('pattern_database', {})
            self.strategy_performance = knowledge.get('strategy_performance', {})
            self.market_regime_knowledge = knowledge.get('market_regime_knowledge', {})
            self.learning_progress = knowledge.get('learning_progress', 0)
            
            print("🧠 Quantum knowledge base loaded")
        except:
            print("🆕 Starting with fresh quantum knowledge")
