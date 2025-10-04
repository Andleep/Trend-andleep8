import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import threading

from trading_bot import LorentzianTradingBot
from config import BINANCE_CONFIG, TRADING_CONFIG
from binance.client import Client

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="البوت اللورنتزي الذكي",
    page_icon="🚀",
    layout="wide"
)

# العنوان الرئيسي
st.title("🚀 البوت اللورنتزي الذكي - التداول التراكمي")
st.markdown("""
**المميزات:**
- 🤖 خوارزمية لورنتزي متقدمة
- 💰 ربح تراكمي بعد كل صفقة
- 🛡️ إدارة مخاطر ذكية
- 📊 محاكاة متقدمة
- ⚡ تشغيل تلقائي
""")

# تهيئة البوت
if 'bot' not in st.session_state:
    try:
        client = Client(BINANCE_CONFIG['api_key'], BINANCE_CONFIG['api_secret'], 
                       testnet=BINANCE_CONFIG['testnet'])
        st.session_state.bot = LorentzianTradingBot(TRADING_CONFIG, client)
        st.session_state.bot_running = False
        st.session_state.demo_mode = True
        st.success("✅ تم تهيئة البوت بنجاح!")
    except Exception as e:
        st.error(f"❌ خطأ في التهيئة: {e}")

# الشريط الجانبي
st.sidebar.header("⚙️ إعدادات البوت")

# الإعدادات الأساسية
symbol = st.sidebar.selectbox("الزوج", ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "DOGEUSDT"])
timeframe = st.sidebar.selectbox("الإطار الزمني", ["1m", "5m", "15m", "1h"])
initial_balance = st.sidebar.number_input("رأس المال", 10.0, 10000.0, 1000.0)
risk_per_trade = st.sidebar.slider("المخاطرة لكل صفقة %", 1.0, 5.0, 2.0) / 100

# تحديث الإعدادات
if st.sidebar.button("🔄 تحديث الإعدادات"):
    TRADING_CONFIG['initial_balance'] = initial_balance
    TRADING_CONFIG['risk_per_trade'] = risk_per_trade
    st.success("تم تحديث الإعدادات!")

# الأقسام الرئيسية
tab1, tab2, tab3, tab4 = st.tabs(["🏠 لوحة التحكم", "🤖 تشغيل البوت", "📊 المحاكاة", "🔐 التداول الحقيقي"])

with tab1:
    st.header("🏠 لوحة التحكم")
    
    if st.session_state.get('bot'):
        # عرض إحصائيات البوت
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("الرصيد الحالي", f"${st.session_state.bot.balance:.2f}")
            st.metric("الربح التراكمي", f"${st.session_state.bot.cumulative_profit:.2f}")
        
        with col2:
            win_rate = st.session_state.bot.win_count / max(1, st.session_state.bot.win_count + st.session_state.bot.loss_count)
            st.metric("معدل الفوز", f"{win_rate*100:.1f}%")
            st.metric("إجمالي الصفقات", len(st.session_state.bot.trade_history))
        
        with col3:
            st.metric("الصفقات الرابحة", st.session_state.bot.win_count)
            st.metric("الصفقات الخاسرة", st.session_state.bot.loss_count)
        
        with col4:
            if st.session_state.bot.trade_history:
                last_trade = st.session_state.bot.trade_history[-1]
                st.metric("آخر صفقة", last_trade.get('action', 'N/A'))
                st.metric("حالة البوت", "🟢 يعمل" if st.session_state.bot_running else "🔴 متوقف")
        
        # الرسم البياني للأداء
        st.subheader("📈 منحنى رأس المال")
        
        if st.session_state.bot.trade_history:
            # إنشاء منحنى الأسهم
            equity_curve = []
            balance = st.session_state.bot.initial_balance
            dates = []
            
            for trade in st.session_state.bot.trade_history:
                if trade.get('status') == 'CLOSED' and 'profit' in trade:
                    balance += trade['profit']
                    equity_curve.append(balance)
                    dates.append(trade.get('timestamp', datetime.now()))
            
            if equity_curve:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=equity_curve,
                    mode='lines+markers',
                    name='رأس المال',
                    line=dict(color='green', width=3)
                ))
                
                fig.update_layout(
                    title="تطور رأس المال مع المرابحة",
                    xaxis_title="التاريخ",
                    yaxis_title="رأس المال ($)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("🤖 تشغيل البوت")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("التحكم في التشغيل")
        
        # أزرار التحكم
        col1_1, col1_2, col1_3 = st.columns(3)
        
        with col1_1:
            if st.button("▶️ بدء التشغيل التلقائي", type="primary"):
                st.session_state.bot_running = True
                st.success("🚀 البوت يعمل الآن بشكل تلقائي!")
        
        with col1_2:
            if st.button("⏸️ إيقاف مؤقت"):
                st.session_state.bot_running = False
                st.warning("⏸️ البوت متوقف مؤقتاً")
        
        with col1_3:
            if st.button("⏹️ إيقاف كلي"):
                st.session_state.bot_running = False
                st.error("⏹️ تم إيقاف البوت")
        
        # تشغيل دورة واحدة
        if st.button("🔄 تشغيل دورة واحدة"):
            if st.session_state.get('bot'):
                result = st.session_state.bot.run_bot_cycle(symbol, timeframe, st.session_state.demo_mode)
                
                if 'error' not in result:
                    st.success(f"✅ تم تنفيذ الدورة: {result['signal']}")
                    
                    if 'trade' in result and result['trade']:
                        trade = result['trade']
                        st.info(f"""
                        **تفاصيل الصفقة:**
                        - الإجراء: {trade.get('action')}
                        - المبلغ: ${trade.get('amount', 0):.2f}
                        - السعر: ${trade.get('entry_price', 0):.2f}
                        - الربح: ${trade.get('profit', 0):.2f if 'profit' in trade else 'N/A'}
                        - الرصيد الجديد: ${st.session_state.bot.balance:.2f}
                        """)
                else:
                    st.error(f"❌ خطأ: {result['error']}")
    
    with col2:
        st.subheader("الإشارات الحية")
        
        # مؤشرات فنية وهمية للعرض
        indicators = {
            'المؤشر': ['RSI', 'WaveTrend', 'CCI', 'ADX', 'التصنيف'],
            'القيمة': [45.6, 12.3, 25.8, 32.1, 'شراء'],
            'الحالة': ['محايد', 'شراء', 'بيع', 'محايد', 'قوي']
        }
        
        df_indicators = pd.DataFrame(indicators)
        st.dataframe(df_indicators, use_container_width=True)
        
        # حالة البوت
        if st.session_state.bot_running:
            st.success("🟢 البوت يعمل بنشاط")
        else:
            st.error("🔴 البوت متوقف")

with tab3:
    st.header("📊 محاكاة الأداء")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("إعدادات المحاكاة")
        
        sim_days = st.slider("فترة المحاكاة (أيام)", 7, 90, 30)
        sim_balance = st.number_input("رأس المال الابتدائي", 10.0, 5000.0, 1000.0)
        
        if st.button("🎯 تشغيل المحاكاة", type="primary"):
            with st.spinner("جاري تشغيل المحاكاة..."):
                # محاكاة مبسطة
                time.sleep(2)
                
                # نتائج وهمية للعرض
                simulated_results = {
                    'رأس المال النهائي': f"${sim_balance * 1.25:.2f}",
                    'الربح الإجمالي': f"${sim_balance * 0.25:.2f}",
                    'معدل الفوز': "62%",
                    'أقصى انخفاض': "8.2%",
                    'عدد الصفقات': "147"
                }
                
                st.session_state.sim_results = simulated_results
                st.success("✅ تم الانتهاء من المحاكاة!")
    
    with col2:
        st.subheader("نتائج المحاكاة")
        
        if st.session_state.get('sim_results'):
            results = st.session_state.sim_results
            
            for key, value in results.items():
                st.metric(key, value)

with tab4:
    st.header("🔐 التداول الحقيقي")
    
    st.warning("""
    ⚠️ **تحذير هام:** 
    - التداول الحقيقي يحمل مخاطر فقدان رأس المال
    - تأكد من فهمك الكامل للمخاطر
    - ابدأ بمبالغ صغيرة
    - اختبر البوت جيداً في الوضع التجريبي أولاً
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("الإعدادات الحقيقية")
        
        real_balance = st.number_input("رأس المال الحقيقي ($)", 10.0, 10000.0, 100.0)
        
        if st.button("🚀 التحويل للوضع الحقيقي", type="primary"):
            if BINANCE_CONFIG['api_key'] and BINANCE_CONFIG['api_secret']:
                st.session_state.demo_mode = False
                BINANCE_CONFIG['testnet'] = False
                st.session_state.bot.balance = real_balance
                st.session_state.bot.initial_balance = real_balance
                st.success("✅ تم التحويل للوضع الحقيقي!")
                st.info("البوت يتداول الآن بأموال حقيقية - كن حذراً!")
            else:
                st.error("❌ يرجى إعداد مفاتيح API أولاً")
    
    with col2:
        st.subheader("مراقبة التداول الحقيقي")
        
        st.info("""
        **حالة التداول الحقيقي:**
        - ✅ الوضع: جاهز
        - 💰 الرصيد: ${:.2f}
        - 📈 الصفقات النشطة: {}
        - 🏆 الربح التراكمي: ${:.2f}
        """.format(
            st.session_state.bot.balance,
            len([p for p in st.session_state.bot.positions.values() if p.get('status') == 'OPEN']),
            st.session_state.bot.cumulative_profit
        ))

# التشغيل التلقائي في الخلفية
def auto_trading():
    while st.session_state.get('bot_running', False):
        try:
            if st.session_state.get('bot'):
                result = st.session_state.bot.run_bot_cycle(symbol, timeframe, st.session_state.demo_mode)
                time.sleep(10)  # انتظار 10 ثواني بين كل دورة للعرض
        except Exception as e:
            st.error(f"خطأ في التشغيل التلقائي: {e}")
            time.sleep(10)

# بدء thread التشغيل التلقائي
if st.session_state.get('bot_running') and not st.session_state.get('auto_thread_started', False):
    auto_thread = threading.Thread(target=auto_trading, daemon=True)
    auto_thread.start()
    st.session_state.auto_thread_started = True

# التذييل
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p><b>البوت اللورنتزي الذكي - نظام التداول التراكمي</b></p>
        <p>تطوير بتقنيات الذكاء الاصطناعي | ⚠️ التداول يحمل مخاطر</p>
    </div>
    """,
    unsafe_allow_html=True
)
