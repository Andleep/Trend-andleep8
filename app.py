import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import numpy as np

# إعداد الصفحة
st.set_page_config(
    page_title="البوت اللورنتزي الذكي - الإصدار النهائي",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# العنوان الرئيسي مع تنسيق محسن
st.title("🚀 البوت اللورنتزي الذكي - نظام الربح التراكمي")
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;'>
<h3 style='color: white; margin: 0;'>✨ نظام تداول ذكي بربح تراكمي فوري</h3>
<p style='margin: 10px 0 0 0;'>كل ربح يضاف تلقائياً إلى رأس المال للصفقة التالية</p>
</div>
""", unsafe_allow_html=True)

# تهيئة حالة الجلسة
def initialize_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.balance = 1000.0
        st.session_state.initial_balance = 1000.0
        st.session_state.trades = []
        st.session_state.bot_running = False
        st.session_state.last_update = datetime.now()
        st.session_state.performance_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'max_balance': 1000.0,
            'min_balance': 1000.0
        }
        # بيانات محاكاة واقعية
        st.session_state.market_data = {
            "BTCUSDT": {"price": 45000.0, "volatility": 2.5},
            "ETHUSDT": {"price": 2500.0, "volatility": 3.0},
            "ADAUSDT": {"price": 0.45, "volatility": 4.0},
            "BNBUSDT": {"price": 320.0, "volatility": 2.8}
        }

initialize_session_state()

# محاكاة بيانات السوق المحسنة
def simulate_market_movement(symbol):
    data = st.session_state.market_data[symbol]
    volatility = data["volatility"]
    current_price = data["price"]
    
    # تغيير واقعي في السعر مع اتجاهات عشوائية
    change_percent = random.normalvariate(0, volatility) / 100
    new_price = current_price * (1 + change_percent)
    
    # منع الأسعار من أن تكون غير واقعية
    new_price = max(new_price, current_price * 0.5)  # لا تقل عن 50%
    new_price = min(new_price, current_price * 1.5)  # لا تزيد عن 150%
    
    st.session_state.market_data[symbol]["price"] = round(new_price, 2)
    return new_price

# خوارزمية تداول ذكية محسنة
def generate_intelligent_signal(symbol):
    current_price = st.session_state.market_data[symbol]["price"]
    
    if len(st.session_state.trades) < 5:
        # في البداية، تكون الإشارات أكثر تحفظاً
        signals = ['BUY', 'SELL', 'HOLD']
        weights = [0.3, 0.3, 0.4]
        return random.choices(signals, weights=weights)[0]
    
    # تحليل الأداء السابق
    recent_trades = st.session_state.trades[-10:]  # آخر 10 صفقات
    if recent_trades:
        winning_trades = [t for t in recent_trades if t.get('profit', 0) > 0]
        win_rate = len(winning_trades) / len(recent_trades)
        
        # تعديل الاستراتيجية بناءً على معدل الفوز
        if win_rate > 0.6:
            # إذا كان الأداء جيداً، كن أكثر جرأة
            signals = ['BUY', 'SELL', 'HOLD']
            weights = [0.4, 0.4, 0.2]
        elif win_rate < 0.4:
            # إذا كان الأداء ضعيفاً، كن أكثر حذراً
            signals = ['BUY', 'SELL', 'HOLD']
            weights = [0.2, 0.2, 0.6]
        else:
            # أداء متوسط
            signals = ['BUY', 'SELL', 'HOLD']
            weights = [0.35, 0.35, 0.3]
    else:
        signals = ['BUY', 'SELL', 'HOLD']
        weights = [0.33, 0.33, 0.34]
    
    return random.choices(signals, weights=weights)[0]

# نظام إدارة المخاطر المحسن
def calculate_position_size(symbol, signal):
    current_price = st.session_state.market_data[symbol]["price"]
    base_risk = 0.02  # مخاطرة أساسية 2%
    
    # تعديل المخاطرة بناءً على حجم الرصيد
    if st.session_state.balance > 5000:
        base_risk = 0.015  # مخاطرة أقل للرصيد الكبير
    elif st.session_state.balance < 200:
        base_risk = 0.03   # مخاطرة أعلى للرصيد الصغير
    
    risk_amount = st.session_state.balance * base_risk
    min_trade = 10.0  # الحد الأدنى للتداول
    
    if risk_amount < min_trade:
        return 0, 0
    
    quantity = risk_amount / current_price
    return risk_amount, quantity

# تنفيذ الصفقة مع نظام الربح التراكمي
def execute_trade(symbol, signal):
    current_price = simulate_market_movement(symbol)
    amount, quantity = calculate_position_size(symbol, signal)
    
    if amount == 0:
        return None
    
    trade_time = datetime.now()
    trade_id = f"{symbol}_{trade_time.strftime('%Y%m%d_%H%M%S')}"
    
    if signal == 'BUY':
        trade = {
            'trade_id': trade_id,
            'timestamp': trade_time,
            'symbol': symbol,
            'action': 'BUY',
            'entry_price': current_price,
            'amount': amount,
            'quantity': quantity,
            'status': 'OPEN',
            'type': 'LONG'
        }
        st.session_state.balance -= amount
        st.session_state.trades.append(trade)
        return trade
    
    elif signal == 'SELL':
        # البحث عن صفقة مفتوحة للإغلاق
        open_trades = [t for t in st.session_state.trades if t.get('status') == 'OPEN' and t.get('symbol') == symbol]
        if open_trades:
            entry_trade = open_trades[-1]
            entry_price = entry_trade['entry_price']
            entry_quantity = entry_trade['quantity']
            
            # حساب الربح/الخسارة
            profit = (current_price - entry_price) * entry_quantity
            
            trade = {
                'trade_id': trade_id,
                'timestamp': trade_time,
                'symbol': symbol,
                'action': 'SELL',
                'entry_price': entry_price,
                'exit_price': current_price,
                'amount': entry_trade['amount'],
                'quantity': entry_quantity,
                'profit': profit,
                'status': 'CLOSED',
                'type': 'CLOSE_LONG'
            }
            
            # ✅ نظام الربح التراكمي - إضافة الربح للرصيد فوراً
            st.session_state.balance += entry_trade['amount'] + profit
            
            # تحديث الإحصائيات
            st.session_state.performance_stats['total_trades'] += 1
            st.session_state.performance_stats['total_profit'] += profit
            if profit > 0:
                st.session_state.performance_stats['winning_trades'] += 1
            else:
                st.session_state.performance_stats['losing_trades'] += 1
            
            # تحديث أعلى/أقل رصيد
            st.session_state.performance_stats['max_balance'] = max(
                st.session_state.performance_stats['max_balance'], 
                st.session_state.balance
            )
            st.session_state.performance_stats['min_balance'] = min(
                st.session_state.performance_stats['min_balance'], 
                st.session_state.balance
            )
            
            # تحديث حالة الصفقة المفتوحة
            entry_trade['status'] = 'CLOSED'
            entry_trade['exit_price'] = current_price
            entry_trade['profit'] = profit
            
            st.session_state.trades.append(trade)
            return trade
    
    return None

# دورة تشغيل البوت
def run_bot_cycle(symbol):
    signal = generate_intelligent_signal(symbol)
    
    if signal in ['BUY', 'SELL']:
        trade = execute_trade(symbol, signal)
        if trade:
            return {
                'symbol': symbol,
                'signal': signal,
                'price': st.session_state.market_data[symbol]["price"],
                'trade': trade,
                'balance': st.session_state.balance,
                'timestamp': datetime.now()
            }
    
    return {
        'symbol': symbol,
        'signal': 'HOLD',
        'price': st.session_state.market_data[symbol]["price"],
        'balance': st.session_state.balance,
        'timestamp': datetime.now()
    }

# واجهة المستخدم المحسنة
st.sidebar.header("⚙️ إعدادات البوت المتقدمة")

# إعدادات التداول
selected_symbol = st.sidebar.selectbox(
    "اختر زوج التداول:",
    ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT"],
    index=0
)

# إدارة الرصيد
st.sidebar.subheader("إدارة الرصيد")
new_balance = st.sidebar.number_input(
    "تعيين رأس المال الجديد ($):",
    min_value=10.0,
    max_value=100000.0,
    value=float(st.session_state.balance),
    step=100.0
)

if st.sidebar.button("💾 حفظ الرصيد الجديد"):
    st.session_state.balance = new_balance
    st.session_state.initial_balance = new_balance
    st.session_state.performance_stats['max_balance'] = new_balance
    st.session_state.performance_stats['min_balance'] = new_balance
    st.sidebar.success("تم تحديث الرصيد بنجاح!")

if st.sidebar.button("🔄 إعادة التعيين"):
    st.session_state.balance = 1000.0
    st.session_state.initial_balance = 1000.0
    st.session_state.trades = []
    st.session_state.performance_stats = {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'total_profit': 0.0,
        'max_balance': 1000.0,
        'min_balance': 1000.0
    }
    st.sidebar.success("تم إعادة التعيين بنجاح!")

# التنقل بين الصفحات
tabs = st.tabs(["🏠 اللوحة الرئيسية", "📊 أداء البوت", "💼 إدارة المحفظة", "⚙️ الإعدادات"])

with tabs[0]:
    st.header("📊 اللوحة الرئيسية - المراقبة الحية")
    
    # بطاقات الأداء
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        profit_loss = st.session_state.balance - st.session_state.initial_balance
        profit_color = "green" if profit_loss >= 0 else "red"
        st.metric(
            "الرصيد الحالي", 
            f"${st.session_state.balance:,.2f}",
            f"{profit_loss:+.2f}" if profit_loss != 0 else "0.00"
        )
    
    with col2:
        total_trades = st.session_state.performance_stats['total_trades']
        win_rate = (st.session_state.performance_stats['winning_trades'] / total_trades * 100) if total_trades > 0 else 0
        st.metric("معدل الفوز", f"{win_rate:.1f}%", f"{total_trades} صفقات")
    
    with col3:
        current_price = st.session_state.market_data[selected_symbol]["price"]
        st.metric(f"سعر {selected_symbol}", f"${current_price:,.2f}")
    
    with col4:
        bot_status = "🟢 نشط" if st.session_state.bot_running else "🔴 متوقف"
        st.metric("حالة البوت", bot_status)
    
    # الرسم البياني التفاعلي
    st.subheader("📈 منحنى نمو رأس المال التراكمي")
    
    if st.session_state.trades:
        closed_trades = [t for t in st.session_state.trades if t.get('status') == 'CLOSED']
        if closed_trades:
            # بناء منحنى الأسهم
            equity_data = []
            balance = st.session_state.initial_balance
            dates = []
            
            for trade in closed_trades:
                if 'profit' in trade:
                    balance += trade['profit']
                    equity_data.append(balance)
                    dates.append(trade['timestamp'])
            
            fig = go.Figure()
            
            # منحنى رأس المال
            fig.add_trace(go.Scatter(
                x=dates,
                y=equity_data,
                mode='lines+markers',
                name='رأس المال التراكمي',
                line=dict(color='#00D4AA', width=4),
                marker=dict(size=6, color='#007AFF')
            ))
            
            # خط رأس المال الأولي
            fig.add_hline(
                y=st.session_state.initial_balance,
                line_dash="dash",
                line_color="red",
                annotation_text="رأس المال الابتدائي"
            )
            
            fig.update_layout(
                title="تطور رأس المال مع نظام المرابحة التراكمية",
                xaxis_title="الوقت",
                yaxis_title="رأس المال ($)",
                height=500,
                template="plotly_white",
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⏳ لا توجد صفقات مغلقة حتى الآن. قم بتشغيل البوت لبدء التداول.")
    else:
        st.info("🎯 البوت جاهز للبدء! استخدم الأزرار أدناه لبدء التداول.")

with tabs[1]:
    st.header("📈 تحليل أداء البوت")
    
    if st.session_state.performance_stats['total_trades'] > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("إحصائيات الأداء التفصيلية")
            
            stats = st.session_state.performance_stats
            total_profit = stats['total_profit']
            win_rate = (stats['winning_trades'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
            max_drawdown = ((stats['max_balance'] - stats['min_balance']) / stats['max_balance'] * 100) if stats['max_balance'] > 0 else 0
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("إجمالي الأرباح", f"${total_profit:,.2f}")
                st.metric("أعلى رصيد", f"${stats['max_balance']:,.2f}")
            
            with metric_col2:
                st.metric("معدل الفوز", f"{win_rate:.1f}%")
                st.metric("أدنى رصيد", f"${stats['min_balance']:,.2f}")
            
            with metric_col3:
                st.metric("أقصى انخفاض", f"{max_drawdown:.1f}%")
                st.metric("متوسط ربح/صفقة", f"${(total_profit/stats['total_trades']):.2f}" if stats['total_trades'] > 0 else "$0.00")
        
        with col2:
            st.subheader("توزيع الصفقات")
            labels = ['رابحة', 'خاسرة']
            values = [stats['winning_trades'], stats['losing_trades']]
            
            if any(values):
                fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
                fig_pie.update_layout(height=300)
                st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("📊 لا توجد بيانات أداء حتى الآن. ابدأ التداول لتظهر الإحصائيات هنا.")

with tabs[2]:
    st.header("💼 إدارة المحفظة والصفقات")
    
    # سجل الصفقات
    if st.session_state.trades:
        st.subheader("سجل الصفقات المفصل")
        
        # تصفية الصفقات المغلقة للعرض
        closed_trades = [t for t in st.session_state.trades if t.get('status') == 'CLOSED']
        
        if closed_trades:
            # تحضير البيانات للعرض
            display_data = []
            for trade in closed_trades[-20:]:  # آخر 20 صفقة
                display_data.append({
                    'الوقت': trade['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    'الزوج': trade['symbol'],
                    'الإجراء': trade['action'],
                    'سعر الدخول': f"${trade['entry_price']:,.2f}",
                    'سعر الخروج': f"${trade.get('exit_price', 0):,.2f}",
                    'الربح': f"${trade.get('profit', 0):,.2f}",
                    'الحالة': '🟢' if trade.get('profit', 0) > 0 else '🔴'
                })
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("💼 لا توجد صفقات مغلقة حتى الآن.")
    else:
        st.info("💼 سجل الصفقات فارغ. ابدأ التداول لملء السجل.")

with tabs[3]:
    st.header("⚙️ إعدادات البوت المتقدمة")
    
    st.subheader("التحكم في التشغيل")
    control_col1, control_col2, control_col3 = st.columns(3)
    
    with control_col1:
        if st.button("▶️ بدء التشغيل التلقائي", type="primary", use_container_width=True):
            st.session_state.bot_running = True
            st.success("🚀 البوت يعمل الآن! يجري الصفقات تلقائياً كل 10 ثوانٍ")
    
    with control_col2:
        if st.button("🔄 دورة واحدة", use_container_width=True):
            result = run_bot_cycle(selected_symbol)
            if result['signal'] != 'HOLD':
                st.success(f"✅ تم تنفيذ صفقة {result['signal']} على {result['symbol']}")
                st.info(f"💰 السعر: ${result['price']:,.2f} | الرصيد: ${result['balance']:,.2f}")
            else:
                st.info("ℹ️ لا توجد إشارة تداول مناسبة حالياً")
    
    with control_col3:
        if st.button("⏸️ إيقاف البوت", use_container_width=True):
            st.session_state.bot_running = False
            st.warning("⏸️ البوت متوقف حالياً")
    
    st.subheader("معلومات السوق الحية")
    for symbol, data in st.session_state.market_data.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**{symbol}**")
        with col2:
            st.write(f"${data['price']:,.2f}")

# التشغيل التلقائي في الخلفية
if st.session_state.bot_running:
    current_time = datetime.now()
    if (current_time - st.session_state.last_update).seconds >= 10:  # كل 10 ثوانٍ
        result = run_bot_cycle(selected_symbol)
        st.session_state.last_update = current_time
        
        # عرض تحديث سريع
        if result['signal'] != 'HOLD':
            st.rerun()

# التذييل المحسن
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
    <h3 style='color: white; margin: 0;'>البوت اللورنتزي الذكي - الإصدار النهائي</h3>
    <p style='margin: 10px 0 0 0;'>نظام تداول بربح تراكمي • إدارة مخاطر ذكية • واجهة احترافية</p>
    <p style='margin: 5px 0 0 0;'>⚠️ تذكر: هذا تطبيق محاكاة لأغراض تعليمية</p>
    </div>
    """,
    unsafe_allow_html=True
)
