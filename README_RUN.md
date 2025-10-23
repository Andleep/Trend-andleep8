Secure Trading Bot - README (Testnet & Render)
=============================================

This package contains a secured trading bot skeleton ready for Testnet and Render deployment.
It includes safety features: health check, emergency close, sqlite persistence, Telegram alerts,
symbol filters (minQty/stepSize/minNotional), and basic orderbook-aware sizing.

IMPORTANT: This is a framework. Test extensively on Testnet before any real funds.

Files:
- secure_bot.py        : Main secured bot (testnet-ready, sqlite logging, safety)
- emergency_recovery.py: Recovery helper
- health_monitor.py    : System health monitor (optional)
- run_secure.py        : Helper to start monitoring + bot
- config.json          : Default config (edit before running)
- Dockerfile           : For Render deployment
- requirements.txt     : Python deps
- README_RUN.md        : This file

Quick start (local):
1) Create venv and install deps:
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt

2) Edit .env (create file) and set:
   INITIAL_CAPITAL=50
   USE_TESTNET=true
   BINANCE_API_KEY=your_testnet_key_or_empty
   BINANCE_SECRET_KEY=your_testnet_secret_or_empty
   TG_BOT_TOKEN=optional_telegram_token
   TG_CHAT_ID=optional_chat_id

3) Run safe mode locally:
   python run_secure.py

Notes for Render:
- Use the Dockerfile included. Set env vars on Render dashboard.
- Set health check to /health endpoint (port 8080).
- Start command: python secure_bot.py
