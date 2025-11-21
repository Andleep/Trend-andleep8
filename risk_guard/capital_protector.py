import numpy as np
from datetime import datetime, timedelta

class CapitalProtector:
    def __init__(self, initial_balance):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.daily_stats = {}
        self.risk_limits = {
            'max_daily_loss': 0.03,  # 3% خسارة يومية كحد أقصى
            'max_trade_loss': 0.015,  # 1.5% خسارة للصفقة
            'max_portfolio_risk': 0.25,  # 25% مخاطرة للمحفظة
            'max_consecutive_losses': 3,
            'daily_trade_limit': 20,
            'cooldown_after_loss': 2  # دورات تبريد بعد خسارتين متتاليتين
        }
        self.trade_history = []
        self.consecutive_losses = 0
        self.cooldown_mode = False
        self.cooldown_cycles = 0
    
    def approve_trade(self, symbol, direction, position_size, stop_loss, take_profit):
        """الموافقة على الصفقة بعد فحص المخاطر"""
        risk_check = {
            'approved': True,
            'risk_score': 0.0,
            'max_loss': 0.0,
            'warnings': [],
            'adjustments': {}
        }
        
        # 1. فحص وضع التبريد
        if self.cooldown_mode:
            risk_check['approved'] = False
            risk_check['warnings'].append("نظام التبريد نشط - انتظر قبل التداول")
            return risk_check
        
        # 2. حساب الخسارة المحتملة
        potential_loss = self.calculate_potential_loss(position_size, stop_loss, direction)
        risk_check['max_loss'] = potential_loss
        
        # 3. فحص الخسارة اليومية
        daily_loss_check = self.check_daily_loss_limits(potential_loss)
        if not daily_loss_check['approved']:
            risk_check['approved'] = False
            risk_check['warnings'].extend(daily_loss_check['warnings'])
        
        # 4. فحص حجم المركز
        position_size_check = self.check_position_size(position_size)
        if not position_size_check['approved']:
            risk_check['approved'] = False
            risk_check['warnings'].extend(position_size_check['warnings'])
        
        # 5. فحص الخسائر المتتالية
        consecutive_losses_check = self.check_consecutive_losses()
        if not consecutive_losses_check['approved']:
            risk_check['approved'] = False
            risk_check['warnings'].extend(consecutive_losses_check['warnings'])
        
        # 6. حساب درجة المخاطرة النهائية
        risk_check['risk_score'] = self.calculate_risk_score(
            potential_loss, position_size, direction
        )
        
        # إذا كانت درجة المخاطرة عالية جداً
        if risk_check['risk_score'] > 0.8:
            risk_check['approved'] = False
            risk_check['warnings'].append("درجة المخاطرة عالية جداً")
        
        return risk_check
    
    def calculate_potential_loss(self, position_size, stop_loss, direction):
        """حساب الخسارة المحتملة"""
        # في التطبيق الحقيقي، نحسب بناءً على المسافة إلى وقف الخسارة
        # هنا نستخدم نسبة ثابتة مبسطة
        return position_size * 0.02  # افتراض 2% خسارة محتملة
    
    def check_daily_loss_limits(self, potential_loss):
        """فحص حدود الخسارة اليومية"""
        today = datetime.now().date()
        today_str = today.isoformat()
        
        if today_str not in self.daily_stats:
            self.daily_stats[today_str] = {
                'trades_count': 0,
                'total_volume': 0,
                'net_profit': 0,
                'total_loss': 0
            }
        
        daily_data = self.daily_stats[today_str]
        check = {'approved': True, 'warnings': []}
        
        # فحص عدد الصفقات اليومية
        if daily_data['trades_count'] >= self.risk_limits['daily_trade_limit']:
            check['approved'] = False
            check['warnings'].append("تم الوصول للحد اليومي للصفقات")
        
        # فحص الخسارة اليومية
        max_daily_loss = self.current_balance * self.risk_limits['max_daily_loss']
        if daily_data['net_profit'] + potential_loss < -max_daily_loss:
            check['approved'] = False
            check['warnings'].append("ستتجاوز الصفقة الحد الأقصى للخسارة اليومية")
        
        return check
    
    def check_position_size(self, position_size):
        """فحص حجم المركز"""
        check = {'approved': True, 'warnings': []}
        
        # فحص نسبة المركز من الرصيد
        position_ratio = position_size / self.current_balance
        
        if position_ratio > 0.15:  # 15% حد أقصى
            check['approved'] = False
            check['warnings'].append("حجم المركز يتجاوز الحد المسموح")
        
        elif position_ratio > 0.1:  # 10% تحذير
            check['warnings'].append("حجم المركز مرتفع نسبياً")
        
        return check
    
    def check_consecutive_losses(self):
        """فحص الخسائر المتتالية"""
        check = {'approved': True, 'warnings': []}
        
        if self.consecutive_losses >= self.risk_limits['max_consecutive_losses']:
            check['approved'] = False
            check['warnings'].append(f"تم الوصول لـ {self.consecutive_losses} خسائر متتالية")
            self.activate_cooldown()
        
        elif self.consecutive_losses >= 2:
            check['warnings'].append(f"تحذير: {self.consecutive_losses} خسائر متتالية")
        
        return check
    
    def calculate_risk_score(self, potential_loss, position_size, direction):
        """حساب درجة المخاطرة"""
        score = 0.0
        
        # عامل حجم المركز
        position_ratio = position_size / self.current_balance
        score += min(position_ratio / 0.15, 1.0) * 0.4
        
        # عامل الخسائر المتتالية
        consecutive_penalty = min(self.consecutive_losses / 3, 1.0) * 0.3
        score += consecutive_penalty
        
        # عامل الخسارة اليومية
        today = datetime.now().date().isoformat()
        if today in self.daily_stats:
            daily_loss_ratio = abs(self.daily_stats[today]['net_profit']) / (self.current_balance * 0.03)
            score += min(daily_loss_ratio, 1.0) * 0.3
        
        return min(score, 1.0)
    
    def update_after_trade(self, symbol, direction, amount, profit):
        """تحديث البيانات بعد الصفقة"""
        today = datetime.now().date()
        today_str = today.isoformat()
        
        if today_str not in self.daily_stats:
            self.daily_stats[today_str] = {
                'trades_count': 0,
                'total_volume': 0,
                'net_profit': 0,
                'total_loss': 0
            }
        
        daily_data = self.daily_stats[today_str]
        daily_data['trades_count'] += 1
        daily_data['total_volume'] += amount
        daily_data['net_profit'] += profit
        
        if profit < 0:
            daily_data['total_loss'] += abs(profit)
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            self.cooldown_mode = False
            self.cooldown_cycles = 0
        
        # تحديث الرصيد
        self.current_balance += profit
        
        # تسجيل الصفقة
        trade_record = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'direction': direction,
            'amount': amount,
            'profit': profit,
            'consecutive_losses': self.consecutive_losses
        }
        self.trade_history.append(trade_record)
        
        # تفعيل التبريد إذا لزم الأمر
        if self.consecutive_losses >= 2:
            self.activate_cooldown()
    
    def activate_cooldown(self):
        """تفعيل نظام التبريد"""
        self.cooldown_mode = True
        self.cooldown_cycles = self.risk_limits['cooldown_after_loss']
        print(f"🛑 نظام التبريد مفعل لمدة {self.cooldown_cycles} دورات")
    
    def update_cooldown(self):
        """تحديث حالة التبريد"""
        if self.cooldown_mode and self.cooldown_cycles > 0:
            self.cooldown_cycles -= 1
            if self.cooldown_cycles == 0:
                self.cooldown_mode = False
                print("✅ نظام التبريد انتهى - العودة للتداول الطبيعي")
    
    def update_balance(self, new_balance):
        """تحديث رصيد الحساب"""
        self.current_balance = new_balance
    
    def get_protection_status(self):
        """الحصول على حالة الحماية"""
        today = datetime.now().date().isoformat()
        daily_data = self.daily_stats.get(today, {})
        
        return {
            'current_balance': self.current_balance,
            'daily_trades': daily_data.get('trades_count', 0),
            'daily_profit': daily_data.get('net_profit', 0),
            'consecutive_losses': self.consecutive_losses,
            'cooldown_active': self.cooldown_mode,
            'cooldown_cycles_left': self.cooldown_cycles,
            'risk_level': self.calculate_risk_level()
        }
    
    def calculate_risk_level(self):
        """حساب مستوى المخاطرة الحالي"""
        if self.cooldown_mode:
            return "HIGH"
        elif self.consecutive_losses >= 2:
            return "MEDIUM_HIGH"
        elif self.consecutive_losses == 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_trading_recommendation(self):
        """الحصول على توصيات التداول"""
        status = self.get_protection_status()
        
        if status['risk_level'] == "HIGH":
            return {
                'action': 'STOP_TRADING',
                'message': 'توقف عن التداول - مخاطرة عالية',
                'suggested_position_size': 0.0
            }
        elif status['risk_level'] == "MEDIUM_HIGH":
            return {
                'action': 'REDUCE_SIZE',
                'message': 'قلل أحجام المراكز - مخاطرة متوسطة/عالية',
                'suggested_position_size': 0.02  # 2% فقط
            }
        elif status['risk_level'] == "MEDIUM":
            return {
                'action': 'CAUTION',
                'message': 'توخ الحذر - مخاطرة متوسطة',
                'suggested_position_size': 0.05  # 5%
            }
        else:
            return {
                'action': 'NORMAL',
                'message': 'التداول الطبيعي - مخاطرة منخفضة',
                'suggested_position_size': 0.08  # 8%
            }
