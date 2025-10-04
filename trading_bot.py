import pandas as pd
import numpy as np
import talib
from binance.client import Client
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LorentzianTradingBot:
    def __init__(self, config, binance_client):
        self.config = config
        self.client = binance_client
        self.balance = config['initial_balance']
        self.initial_balance = config['initial_balance']
        self.positions = {}
        self.trade_history = []
        self.cumulative_profit = 0.0
        self.win_count = 0
        self.loss_count = 0
        
        logger.info(f"تم تهيئة البوت برصيد: ${self.balance}")

    def get_historical_data(self, symbol, interval, limit=100):
        """جلب البيانات التاريخية من Binance"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # تحويل الأنواع
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except Exception as e:
            logger.error(f"خطأ في جلب البيانات: {e}")
            return None

    def calculate_indicators(self, df):
        """حساب المؤشرات الفنية"""
        try:
            # RSI
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            
            # WaveTrend مبسط
            esa = talib.EMA(df['hlc3'], timeperiod=10)
            de = talib.EMA(abs(df['hlc3'] - esa), timeperiod=10)
            ci = (df['hlc3'] - esa) / (0.015 * de)
            wt1 = talib.EMA(ci, timeperiod=21)
            wt2 = talib.EMA(wt1, timeperiod=4)
            df['wt'] = wt1 - wt2
            
            # CCI
            df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20)
            
            # ADX
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            
            return df
            
        except Exception as e:
            logger.error(f"خطأ في حساب المؤشرات: {e}")
            return df

    def generate_signal(self, df):
        """توليد إشارة تداول"""
        try:
            if len(df) < 30:
                return 'HOLD'
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # استراتيجية مبسطة
            buy_signals = 0
            sell_signals = 0
            
            # RSI
            if current['rsi'] < 30:
                buy_signals += 1
            elif current['rsi'] > 70:
                sell_signals += 1
            
            # WaveTrend
            if current['wt'] > 0 and prev['wt'] <= 0:
                buy_signals += 1
            elif current['wt'] < 0 and prev['wt'] >= 0:
                sell_signals += 1
            
            # CCI
            if current['cci'] < -100:
                buy_signals += 1
            elif current['cci'] > 100:
                sell_signals += 1
            
            # قرار التداول
            if buy_signals >= 2:
                return 'BUY'
            elif sell_signals >= 2:
                return 'SELL'
            else:
                return 'HOLD'
                
        except Exception as e:
            logger.error(f"خطأ في توليد الإشارة: {e}")
            return 'HOLD'

    def calculate_position_size(self, current_price):
        """حجم المركز بناء على إدارة المخاطر"""
        risk_amount = self.balance * self.config['risk_per_trade']
        trade_amount = min(risk_amount, self.config.get('max_trade_amount', 100))
        
        if trade_amount < 10:  # الحد الأدنى
            return 0
        
        quantity = trade_amount / current_price
        return trade_amount, quantity

    def execute_trade(self, symbol, signal, amount, price, demo_mode=True):
        """تنفيذ الصفقة مع المرابحة التراكمية"""
        try:
            trade_time = datetime.now()
            trade_id = f"{symbol}_{trade_time.strftime('%Y%m%d_%H%M%S')}"
            
            if signal == 'BUY':
                # فتح صفقة شراء
                trade = {
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'action': 'BUY',
                    'amount': amount,
                    'entry_price': price,
                    'timestamp': trade_time,
                    'status': 'OPEN',
                    'type': 'LONG'
                }
                
                if demo_mode:
                    self.balance -= amount
                
                self.positions[symbol] = trade
                logger.info(f"فتح صفقة شراء: {amount} على {symbol} بالسعر {price}")
                
            elif signal == 'SELL' and symbol in self.positions:
                # إغلاق صفقة شراء
                entry_trade = self.positions[symbol]
                quantity = entry_trade['amount'] / entry_trade['entry_price']
                profit = (price - entry_trade['entry_price']) * quantity
                
                # ✅ المرابحة التراكمية - إضافة الربح للرصيد
                if demo_mode:
                    self.balance += entry_trade['amount'] + profit
                
                self.cumulative_profit += profit
                
                # تحديث إحصائيات الفوز/الخسارة
                if profit > 0:
                    self.win_count += 1
                else:
                    self.loss_count += 1
                
                trade = {
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'action': 'SELL',
                    'amount': amount,
                    'entry_price': entry_trade['entry_price'],
                    'exit_price': price,
                    'profit': profit,
                    'cumulative_profit': self.cumulative_profit,
                    'timestamp': trade_time,
                    'status': 'CLOSED',
                    'type': 'CLOSE_LONG'
                }
                
                # إغلاق المركز
                del self.positions[symbol]
                logger.info(f"إغلاق صفقة: ربح {profit:.2f} | رصيد جديد: {self.balance:.2f}")
                
            else:
                trade = {
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'action': 'HOLD',
                    'timestamp': trade_time,
                    'status': 'CANCELLED'
                }
            
            self.trade_history.append(trade)
            return trade
            
        except Exception as e:
            logger.error(f"خطأ في تنفيذ الصفقة: {e}")
            return None

    def run_bot_cycle(self, symbol, timeframe, demo_mode=True):
        """تشغيل دورة واحدة للبوت"""
        try:
            # جلب البيانات
            df = self.get_historical_data(symbol, timeframe)
            if df is None:
                return {'error': 'فشل جلب البيانات'}
            
            # حساب المؤشرات
            df = self.calculate_indicators(df)
            
            # توليد الإشارة
            signal = self.generate_signal(df)
            current_price = float(df['close'].iloc[-1])
            
            # إذا كانت هناك إشارة، نفذ الصفقة
            if signal in ['BUY', 'SELL']:
                amount, quantity = self.calculate_position_size(current_price)
                
                if amount > 0:
                    trade = self.execute_trade(symbol, signal, amount, current_price, demo_mode)
                    
                    return {
                        'signal': signal,
                        'price': current_price,
                        'amount': amount,
                        'trade': trade,
                        'timestamp': datetime.now()
                    }
            
            return {
                'signal': 'HOLD',
                'price': current_price,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"خطأ في تشغيل البوت: {e}")
            return {'error': str(e)}
