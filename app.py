import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
import random

# إعداد الصفحة
st.set_page_config(
    page_title="بوت التداول الذكي - النسخة التجريبية",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 بوت التداول الذكي - النسخة التجريبية")
st.markdown("""
**هذه نسخة تجريبية تعمل بدون اتصال بـ Binance**
- 🤖 محاكاة الذكاء الاصطناعي
- 💰 نظام ربح تراكمي
- 📊 رسوم بيانية حية
- ⚡ تشغيل فوري
""")

# حالة التطبيق
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.balance = 1000.0
    st.session_state.initial_balance = 1000.0
    st.session_state.trades = []
    st.session_state.bot_running = False
    st.session_state.demo_prices = {
        "BTCUSDT": 45000.0,
        "ETHUSDT": 2500.0,
        "ADAUSDT": 0.45
    }

# محاكاة بيانات السوق
def generate_market_data(symbol):
    current_price = st.session_state.demo_prices[symbol]
    # تغيير عشوائي بسيط في السعر
    change_percent = random.uniform(-0.5, 0.5)
    new_price = current_price * (1 + change_percent / 100)
    st.session_state.demo_prices[symbol] = new_price
    return new_price

# محاكاة إشارة التداول
def generate_trading_signal(symbol):
    signal_types = ['BUY', 'SELL', 'HOLD']
    weights = [0.4, 0.4, 0.2]  # زيادة احتمالية التداول
    signal = random.choices(signal_types, weights=weights)[0]
    
    # جعل الإشارات أكثر واقعية
    if len(st.session_state.trades) > 0:
        last_trade = st.session_state.trades[-1]
        if last_trade['signal'] == 'BUY':
            signal = random.choices(['SELL', 'HOLD'], weights=[0.7, 0.3])[0]
        elif last_trade['signal'] == 'SELL':
            signal = random.choices(['BUY', 'HOLD'], weights=[0.7, 0.3])[0]
    
    return signal

# تنفيذ صفقة وهمية
def execute_demo_trade(symbol, signal, current_price):
    risk_percent = 0.02  # مخاطرة 2%
    risk_amount = st.session_state.balance * risk_percent
    
    if risk_amount < 10:  # الحد الأدنى
        return None
    
    if signal == 'BUY':
        # في الواقع، هنا سنشتري
        quantity = risk_amount / current_price
        trade = {
            'id': len(st.session_state.trades) + 1,
            'timestamp': datetime.now(),
            'symbol': symbol,
            'signal': signal,
            'entry_price': current_price,
            'amount': risk_amount,
            'quantity': quantity,
            'status': 'OPEN',
            'type': 'LONG'
        }
        st.session_state.balance -= risk_amount
        return trade
    
    elif signal == 'SELL' and st.session_state.trades:
        # البحث عن صفقة مفتوحة للإغلاق
        open_trades = [t for t in st.session_state.trades if t.get('status') == 'OPEN']
        if open_trades:
            entry_trade = open_trades[-1]
            quantity = entry_trade['quantity']
            profit = (current_price - entry_trade['entry_price']) * quantity
            
            trade = {
                'id': len(st.session_state.trades) + 1,
                'timestamp': datetime.now(),
                'symbol': symbol,
                'signal': signal,
                'entry_price': entry_trade['entry_price'],
                'exit_price': current_price,
                'amount': entry_trade['amount'],
                'profit': profit,
                'status': 'CLOSED',
                'type': 'CLOSE_LONG'
            }
            
            # ✅ نظام الربح التراكمي - إضافة الربح للرصيد
            st.session_state.balance += entry_trade['amount'] + profit
            
            # تحديث الصفقة المفتوحة
            entry_trade['status'] = 'CLOSED'
            entry_trade['exit_price'] = current_price
            entry_trade['profit'] = profit
            
            return trade
    
    return None

# محاكاة دورة البوت
def run_bot_cycle(symbol):
    current_price = generate_market_data(symbol)
    signal = generate_trading_signal(symbol)
    
    if signal in ['BUY', 'SELL']:
        trade = execute_demo_trade(symbol, signal, current_price)
        if trade:
            st.session_state.trades.append(trade)
    
    return {
        'symbol': symbol,
        'price': current_price,
        'signal': signal,
        'timestamp': datetime.now(),
        'balance': st.session_state.balance
    }

# الواجهة
st.sidebar.header("⚙️ إعدادات البوت")

# إعدادات التداول
symbol = st.sidebar.selectbox("اختر الزوج:", ["BTCUSDT", "ETHUSDT", "ADAUSDT"])
initial_balance = st.sidebar.number_input("رأس المال الابتدائي ($):", 10.0, 10000.0, 1000.0)

if st.sidebar.button("🔄 تعيين رأس المال"):
    st.session_state.balance = initial_balance
    st.session_state.initial_balance = initial_balance
    st.session_state.trades = []
    st.success("تم تعيين رأس المال بنجاح!")

# الأقسام الرئيسية
tab1, tab2, tab3 = st.tabs(["🏠 لوحة التحكم", "🤖 تشغيل البوت", "📊 الإحصائيات"])

with tab1:
    st.header("🏠 لوحة التحكم الرئيسية")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("الرصيد الحالي", f"${st.session_state.balance:.2f}")
        profit = st.session_state.balance - st.session_state.initial_balance
        st.metric("الربح الإجمالي", f"${profit:.2f}")
    
    with col2:
        total_trades = len(st.session_state.trades)
        winning_trades = len([t for t in st.session_state.trades if t.get('profit', 0) > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        st.metric("معدل الفوز", f"{win_rate:.1f}%")
        st.metric("إجمالي الصفقات", total_trades)
    
    with col3:
        current_price = st.session_state.demo_prices[symbol]
        st.metric(f"سعر {symbol}", f"${current_price:.2f}")
        st.metric("حالة البوت", "🟢 يعمل" if st.session_state.bot_running else "🔴 متوقف")
    
    with col4:
        if st.session_state.trades:
            last_trade = st.session_state.trades[-1]
            st.metric("آخر إشارة", last_trade.get('signal', 'N/A'))
            st.metric("الأرباح المغلقة", f"${sum(t.get('profit', 0) for t in st.session_state.trades):.2f}")

    # الرسم البياني
    st.subheader("📈 منحنى رأس المال التراكمي")
    
    if st.session_state.trades:
        # إنشاء منحنى الأسهم
        equity_data = []
        balance = st.session_state.initial_balance
        dates = []
        
        for trade in st.session_state.trades:
            if trade.get('status') == 'CLOSED' and 'profit' in trade:
                balance += trade['profit']
                equity_data.append(balance)
                dates.append(trade['timestamp'])
        
        if equity_data:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=equity_data,
                mode='lines+markers',
                name='رأس المال',
                line=dict(color='#00ff88', width=4),
                marker=dict(size=6)
            ))
            
            # خط رأس المال الأولي
            fig.add_hline(y=st.session_state.initial_balance, line_dash="dash", 
                         line_color="red", annotation_text="رأس المال الابتدائي")
            
            fig.update_layout(
                title="تطور رأس المال مع نظام المرابحة التراكمية",
                xaxis_title="الوقت",
                yaxis_title="رأس المال ($)",
                height=500,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("🤖 التحكم في البوت")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("تشغيل البوت")
        
        col1_1, col1_2, col1_3 = st.columns(3)
        
        with col1_1:
            if st.button("▶️ بدء التشغيل التلقائي", type="primary", use_container_width=True):
                st.session_state.bot_running = True
                st.success("🚀 البوت يعمل الآن! يجري الصفقات تلقائياً")
        
        with col1_2:
            if st.button("⏸️ إيقاف مؤقت", use_container_width=True):
                st.session_state.bot_running = False
                st.warning("⏸️ البوت متوقف مؤقتاً")
        
        with col1_3:
            if st.button("⏹️ إيقاف كلي", use_container_width=True):
                st.session_state.bot_running = False
                st.session_state.trades = []
                st.session_state.balance = st.session_state.initial_balance
                st.error("⏹️ تم إيقاف البوت ومسح السجل")
        
        # تشغيل دورة واحدة
        if st.button("🔄 تشغيل دورة تجريبية", use_container_width=True):
            result = run_bot_cycle(symbol)
            if result['signal'] != 'HOLD':
                st.success(f"✅ تم تنفيذ صفقة: {result['signal']} على {result['symbol']}")
                st.info(f"💵 السعر: ${result['price']:.2f} | 💰 الرصيد: ${result['balance']:.2f}")
            else:
                st.info("ℹ️ لا توجد إشارة تداول مناسبة حالياً")
    
    with col2:
        st.subheader("الإشارات الحية")
        
        # مؤشرات فنية وهمية
        indicators = {
            'المؤشر': ['RSI', 'المتجه', 'الزخم', 'التقلب', 'التصنيف'],
            'القيمة': [f"{random.randint(30, 70)}", 
                      f"{random.randint(-20, 20)}", 
                      f"{random.randint(-15, 15)}",
                      f"{random.randint(10, 30)}%",
                      random.choice(['قوي', 'متوسط', 'ضعيف'])],
            'الإشارة': [random.choice(['🟢', '🔴', '🟡']) for _ in range(5)]
        }
        
        st.dataframe(pd.DataFrame(indicators), use_container_width=True)
        
        # مؤشر الثقة
        confidence = random.randint(60, 95)
        st.progress(confidence/100, text=f"ثقة الخوارزمية: {confidence}%")

with tab3:
    st.header("📊 تحليل الأداء التفصيلي")
    
    if st.session_state.trades:
        # تحليل الصفقات
        closed_trades = [t for t in st.session_state.trades if t.get('status') == 'CLOSED']
        
        if closed_trades:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("سجل الصفقات المفصل")
                trades_df = pd.DataFrame(closed_trades[-10:])  # آخر 10 صفقات
                
                if not trades_df.empty:
                    # تنسيق الأعمدة
                    display_df = trades_df[['timestamp', 'symbol', 'signal', 'entry_price', 'exit_price', 'profit', 'amount']].copy()
                    display_df['profit'] = display_df['profit'].apply(lambda x: f"${x:.2f}")
                    display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}")
                    display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:.2f}")
                    display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:.2f}")
                    
                    st.dataframe(display_df, use_container_width=True)
            
            with col2:
                st.subheader("إحصائيات الأداء")
                
                total_profit = sum(t.get('profit', 0) for t in closed_trades)
                avg_profit = total_profit / len(closed_trades) if closed_trades else 0
                winning_trades = [t for t in closed_trades if t.get('profit', 0) > 0]
                win_rate = len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
                
                st.metric("متوسط الربح/صفقة", f"${avg_profit:.2f}")
                st.metric("معدل الفوز", f"{win_rate:.1f}%")
                st.metric("أعلى ربح", f"${max([t.get('profit', 0) for t in closed_trades]):.2f}" if closed_trades else "$0.00")
                st.metric("أدنى ربح", f"${min([t.get('profit', 0) for t in closed_trades]):.2f}" if closed_trades else "$0.00")
        
        else:
            st.info("⏳ لا توجد صفقات مغلقة حتى الآن")
    else:
        st.warning("🔍 لم يتم تنفيذ أي صفقات بعد. قم بتشغيل البوت أولاً.")

# التشغيل التلقائي
if st.session_state.bot_running:
    st.write("---")
    st.write("🔄 **جاري التشغيل التلقائي...** (يتحقق كل 5 ثوانٍ)")
    
    # محاكاة التشغيل التلقائي
    if 'last_auto_run' not in st.session_state:
        st.session_state.last_auto_run = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_auto_run > 5:  # كل 5 ثواني
        result = run_bot_cycle(symbol)
        st.session_state.last_auto_run = current_time
        
        # عرض آخر نشاط
        if result['signal'] != 'HOLD':
            st.success(f"🔄 تم تنفيذ صفقة تلقائية: {result['signal']} | الرصيد: ${result['balance']:.2f}")

# التذييل
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p><b>بوت التداول الذكي - النسخة التجريبية</b></p>
        <p>🚀 يعمل بنظام المرابحة التراكمية | ⚠️ هذه نسخة تجريبية</p>
        <p>💡 ملاحظة: هذا تطبيق محاكاة ولا يتصل بمنصات تداول حقيقية</p>
    </div>
    """,
    unsafe_allow_html=True
)
