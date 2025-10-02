# main.py
"""
TradeBot - Flask dashboard + backtester
- Fetches klines from Binance (public REST)
- Backtest engine (EMA crossover + RSI + money management/risk-per-trade)
- Web UI to run backtests (1 month / 6 months) and show results
"""
import os
import time
import csv
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
import requests
import pandas as pd

# ---------- Config (can override by ENV) ----------
SYMBOL_DEFAULT = os.getenv("SYMBOL", "ETHUSDT")
INTERVAL_DEFAULT = os.getenv("INTERVAL", "1m")   # change to "1h" if you prefer
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "10.0"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))  # 2%
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.01"))    # 1%
EMA_FAST = int(os.getenv("EMA_FAST", "8"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "21"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
VOLUME_MULTIPLIER = float(os.getenv("VOLUME_MULTIPLIER", "1.0"))

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
KL_LIMIT = int(os.getenv("KL_LIMIT", "1000"))

DEBUG_LOG = "bot_debug.log"
TRADE_LOG = "trades.csv"

app = Flask(__name__, template_folder="templates", static_folder="static")

# ---------- Helpers ----------
def debug(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def fetch_klines(symbol, interval="1m", limit=KL_LIMIT):
    """Fetch klines list of lists from Binance public API."""
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    headers = {"User-Agent":"TradeBot/1.0"}
    r = requests.get(BINANCE_KLINES, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    # convert to DataFrame of dicts
    rows = []
    for k in data:
        rows.append({
            "time": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5])
        })
    return rows

# ---------- Indicators (pandas used for convenience) ----------
def prepare_indicators(df):
    df = df.copy()
    df["close"] = df["close"].astype(float)
    df["ema_fast"] = df["close"].ewm(span=EMA_FAST, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=EMA_SLOW, adjust=False).mean()
    delta = df["close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    ma_down = down.ewm(alpha=1/RSI_PERIOD, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-12)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["avg_vol20"] = df["volume"].rolling(window=20, min_periods=1).mean()
    return df

# ---------- Backtest engine ----------
def run_backtest(candles, initial_balance=INITIAL_BALANCE,
                 risk_per_trade=RISK_PER_TRADE, stop_loss_pct=STOP_LOSS_PCT):
    """
    candles: list of dicts with keys time,open,high,low,close,volume
    returns stats and trade list (with compounding)
    """
    df = pd.DataFrame(candles)
    df = prepare_indicators(df)
    balance = float(initial_balance)
    position = None  # dict: entry, qty, stop
    trade_log = []
    wins = 0
    losses = 0

    for i in range(len(df)):
        # use closed candles: require lookback, so skip early rows
        if i < max(EMA_SLOW, RSI_PERIOD) + 2:
            continue
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # signal detection on last closed candle
        cross_up = (prev["ema_fast"] <= prev["ema_slow"]) and (row["ema_fast"] > row["ema_slow"])
        cross_down = (prev["ema_fast"] >= prev["ema_slow"]) and (row["ema_fast"] < row["ema_slow"])

        vol_ok = row["volume"] > (row["avg_vol20"] * VOLUME_MULTIPLIER)
        rsi_ok = (row["rsi"] > 25) and (row["rsi"] < 75)

        price = row["close"]

        # ENTER
        if position is None:
            if cross_up and vol_ok and rsi_ok:
                # position sizing: risk_per_trade fraction of equity
                risk_amount = balance * risk_per_trade
                if stop_loss_pct <= 0:
                    qty = balance / price
                else:
                    qty = risk_amount / (price * stop_loss_pct)
                qty = max(qty, 1e-8)
                stop_price = price * (1 - stop_loss_pct)
                position = {"symbol": None, "entry": price, "qty": qty, "stop": stop_price, "entry_idx": i}
                debug(f"ENTER @ {price:.6f} qty={qty:.8f} bal={balance:.6f}")
        else:
            # CHECK STOP LOSS first
            if row["low"] <= position["stop"]:
                exit_price = position["stop"]
                proceeds = position["qty"] * exit_price
                profit = proceeds - (position["qty"] * position["entry"])
                balance = proceeds
                trade_log.append({"time": int(row["time"]), "side":"SELL", "entry":position["entry"], "exit":exit_price, "profit":profit, "balance_after":balance, "reason":"SL"})
                if profit >= 0: wins += 1
                else: losses += 1
                debug(f"EXIT SL @ {exit_price:.6f} profit={profit:.6f} newbal={balance:.6f}")
                position = None
                continue
            # exit on cross down
            if cross_down:
                exit_price = price
                proceeds = position["qty"] * exit_price
                profit = proceeds - (position["qty"] * position["entry"])
                balance = proceeds
                trade_log.append({"time": int(row["time"]), "side":"SELL", "entry":position["entry"], "exit":exit_price, "profit":profit, "balance_after":balance, "reason":"X"})
                if profit >= 0: wins += 1
                else: losses += 1
                debug(f"EXIT X @ {exit_price:.6f} profit={profit:.6f} newbal={balance:.6f}")
                position = None
                continue

    stats = {
        "initial_balance": initial_balance,
        "final_balance": round(balance, 8),
        "profit_usd": round(balance - initial_balance, 8),
        "trades": len(trade_log),
        "wins": wins,
        "losses": losses,
        "win_rate": round((wins / (wins+losses) * 100) if (wins+losses)>0 else 0, 2)
    }
    return stats, trade_log

# ---------- Flask routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/candles")
def api_candles():
    symbol = request.args.get("symbol", SYMBOL_DEFAULT)
    limit = int(request.args.get("limit", 500))
    try:
        data = fetch_klines(symbol, interval=INTERVAL_DEFAULT, limit=limit)
        return jsonify({"symbol": symbol, "candles": data})
    except Exception as e:
        debug(f"api/candles error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/backtest", methods=["POST"])
def api_backtest():
    """
    POST form-data or JSON:
      - symbol (optional)
      - months (1 or 6)
      - initial_balance (optional)
      - risk_per_trade (optional)
      - stop_loss_pct (optional)
      - interval (optional)
    """
    data = request.form.to_dict() or request.json or {}
    symbol = data.get("symbol", SYMBOL_DEFAULT)
    months = int(data.get("months", 1))
    initial = float(data.get("initial_balance", INITIAL_BALANCE))
    risk = float(data.get("risk_per_trade", RISK_PER_TRADE))
    stop = float(data.get("stop_loss_pct", STOP_LOSS_PCT))
    interval = data.get("interval", INTERVAL_DEFAULT)

    # compute time range for months
    end = datetime.utcnow()
    start = end - timedelta(days=30*months)

    # Binance can only return up to 1000 candles per request. We'll request pages.
    all_candles = []
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    while True:
        params = {"symbol": symbol, "interval": interval, "limit": 1000, "startTime": start_ms}
        r = requests.get(BINANCE_KLINES, params=params, timeout=20)
        if r.status_code != 200:
            debug(f"binance fetch error {r.status_code} {r.text[:200]}")
            return jsonify({"error": f"binance fetch error {r.status_code}"}), 500
        part = r.json()
        if not part:
            break
        for k in part:
            all_candles.append({"time": int(k[0]), "open":float(k[1]), "high":float(k[2]), "low":float(k[3]), "close":float(k[4]), "volume":float(k[5])})
        if len(part) < 1000:
            break
        # advance start to last candle + 1ms
        start_ms = part[-1][0] + 1
        if start_ms >= end_ms:
            break
        time.sleep(0.2)

    if not all_candles:
        return jsonify({"error":"no candles retrieved"}), 500

    # run backtest (use passed risk/stop)
    old_risk = globals().get("RISK_PER_TRADE")
    old_stop = globals().get("STOP_LOSS_PCT")
    try:
        globals()["RISK_PER_TRADE"] = risk
        globals()["STOP_LOSS_PCT"] = stop
        stats, trades = run_backtest(all_candles, initial_balance=initial, risk_per_trade=risk, stop_loss_pct=stop)
    finally:
        globals()["RISK_PER_TRADE"] = old_risk
        globals()["STOP_LOSS_PCT"] = old_stop

    return jsonify({"stats": stats, "trades": trades})

@app.route("/download_trades")
def download_trades():
    try:
        return send_file(TRADE_LOG, as_attachment=True)
    except Exception:
        return jsonify({"error":"no trades yet"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8000")))
