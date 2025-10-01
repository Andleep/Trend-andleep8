# TradeBot - Render demo (No-pandas version)

This package is a ready-to-deploy version of the trading bot that **does not require pandas**.
It uses only `requests` and pure Python to compute simple EMA and RSI, so it avoids heavy build steps.

Files:
- main.py : bot code (no pandas)
- requirements.txt : minimal dependencies
- runtime.txt : forces Python 3.11 on Render
- .env.example : environment variables example
- README.md : this file

Deployment:
1. Create a new GitHub repo and upload these files.
2. On Render, create **New Web Service** → connect to repo → branch `main`.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn main:app --bind 0.0.0.0:$PORT`
5. Add Environment Variables in Render dashboard (from .env.example).
6. Clear build cache & deploy.
7. Open `https://<your-service>.onrender.com/status`
