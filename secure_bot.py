#!/usr/bin/env python3
# secure_bot.py - secured trading bot (testnet-ready skeleton)
import os, time, json, sqlite3, math, logging, threading, requests
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
except Exception:
    Client = None
    BinanceAPIException = Exception

# Basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('secure_bot')

class SecureTradingBot:
    def __init__(self, test_mode=True, db_path='bot_state.db'):
        self.test_mode = test_mode
        self.initial_capital = float(os.getenv('INITIAL_CAPITAL', 50))
        self.current_balance = self.initial_capital
        self.trades = []
        self.open_positions = []
        self.session_start = datetime.utcnow()
        self.last_health_check = datetime.utcnow()
        self.is_running = True
        self.lock = threading.Lock()
        # load config
        cfg_path = 'config.json'
        if os.path.exists(cfg_path):
            with open(cfg_path,'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}
        # sqlite persistence
        self.db_path = db_path
        self._init_db()
        # setup client
        self.client = None
        self._setup_client()
        # health thread
        self.health_thread = threading.Thread(target=self._health_monitor, daemon=True)
        self.health_thread.start()
        logger.info('SecureTradingBot initialized (test_mode=%s)', self.test_mode)

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS trades(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, symbol TEXT, size REAL, pnl REAL, fees REAL, success INTEGER,
            balance_before REAL, balance_after REAL, meta TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS emergency_states(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, state_json TEXT)''')
        self.conn.commit()

    def _setup_client(self):
        if Client and not self.test_mode and os.getenv('BINANCE_API_KEY'):
            try:
                self.client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'), testnet=False)
                logger.info('Connected to Binance (live mode)')
            except Exception as e:
                logger.error('Binance client setup failed: %s', e)
                self.client = None
        elif Client and self.test_mode:
            # prepare testnet client if keys present and testnet requested (user must set API URL in env for python-binance)
            try:
                api_key = os.getenv('BINANCE_API_KEY')
                api_secret = os.getenv('BINANCE_SECRET_KEY')
                if api_key and api_secret:
                    self.client = Client(api_key, api_secret, testnet=True)
                    logger.info('Binance testnet client configured (if supported by library)')
                else:
                    self.client = None
                    logger.info('Test mode: no Binance client (simulated)')
            except Exception as e:
                logger.warning('Testnet client init issue: %s', e)
                self.client = None
        else:
            self.client = None

    # ---------- Health & emergency ----------
    def _health_monitor(self):
        interval = int(self.config.get('monitoring',{}).get('health_check_interval',30))
        while self.is_running:
            try:
                now = datetime.utcnow()
                if (now - self.last_health_check).total_seconds() > interval:
                    ok = self._check_connection_health()
                    if not ok:
                        logger.critical('Connection health failed -> activating emergency mode')
                        self.activate_emergency_mode()
                    self.last_health_check = now
                time.sleep(5)
            except Exception as e:
                logger.exception('Health monitor error: %s', e)
                time.sleep(10)

    def _check_connection_health(self) -> bool:
        # check internet
        try:
            r = requests.get('https://www.google.com', timeout=5)
            if r.status_code != 200:
                return False
        except Exception:
            return False
        # check binance server time if client exists
        if self.client:
            try:
                self.client.get_server_time()
            except Exception:
                return False
        return True

    def activate_emergency_mode(self):
        logger.critical('*** EMERGENCY MODE ACTIVATED ***')
        try:
            # save state
            self._save_emergency_state({'note':'activated'})
            # attempt safe close (simulate if test_mode)
            self.safe_close_all_positions(simulate=self.test_mode)
            # send alert
            self._send_telegram('Emergency mode activated - bot closed positions (simulated=%s)' % self.test_mode)
        except Exception as e:
            logger.exception('activate_emergency_mode failed: %s', e)

    def _save_emergency_state(self, state:Dict):
        try:
            state_doc = {
                'ts': datetime.utcnow().isoformat(),
                'balance': self.current_balance,
                'open_positions': self.open_positions,
                'trades_last': self.trades[-10:]
            }
            with self.lock:
                cur = self.conn.cursor()
                cur.execute('INSERT INTO emergency_states(ts,state_json) VALUES(?,?)', (state_doc['ts'], json.dumps(state_doc)))
                self.conn.commit()
            with open('emergency_state.json','w') as f:
                json.dump(state_doc, f, indent=2)
            logger.info('Emergency state saved')
        except Exception as e:
            logger.exception('save emergency state failed: %s', e)

    def _send_telegram(self, text:str):
        token = os.getenv('TG_BOT_TOKEN')
        chat = os.getenv('TG_CHAT_ID')
        if not token or not chat:
            logger.debug('Telegram not configured')
            return
        try:
            url = f'https://api.telegram.org/bot{token}/sendMessage'
            requests.post(url, json={'chat_id':chat,'text':text}, timeout=5)
        except Exception as e:
            logger.warning('Telegram send failed: %s', e)

    # ---------- Execution helpers ----------
    def safe_close_all_positions(self, simulate=True):
        logger.info('safe_close_all_positions called (simulate=%s)', simulate)
        try:
            if self.client and not simulate:
                # cancel open orders first
                try:
                    orders = self.client.get_open_orders()
                    for o in orders:
                        try:
                            self.client.cancel_order(symbol=o['symbol'], orderId=o['orderId'])
                        except Exception as e:
                            logger.warning('cancel_order failed: %s', e)
                except Exception as e:
                    logger.warning('get_open_orders failed: %s', e)
                # close positions (spot): check balances and create market order to flatten base assets
                # This is simplified and must be adapted for futures.
                info = self.client.get_account()
                balances = info.get('balances',[])
                for b in balances:
                    free = float(b.get('free',0) or 0)
                    asset = b.get('asset')
                    if free and asset and asset != 'USDT':
                        symbol = asset + 'USDT'
                        try:
                            # find price for notional check
                            price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
                            qty = self._adjust_qty_to_step(symbol, free, price)
                            if qty and qty>0:
                                side = 'SELL'
                                self.client.create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                                logger.info('Closed %s %s', qty, symbol)
                        except Exception as e:
                            logger.debug('close asset %s failed: %s', asset, e)
            else:
                # simulate closing in test mode: mark open positions closed
                with self.lock:
                    for p in self.open_positions:
                        p['open'] = False
                    self.open_positions = []
                logger.info('Simulated closing all positions (test mode)')
        except Exception as e:
            logger.exception('safe_close_all_positions error: %s', e)

    def _adjust_qty_to_step(self, symbol, qty, price):
        # safe adjustment using exchange info (if available)
        try:
            if not self.client:
                # round down to 8 decimals
                return float(Decimal(qty).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN))
            info = self.client.get_symbol_info(symbol)
            if not info:
                return float(qty)
            filters = {f['filterType']: f for f in info['filters']}
            step = Decimal(filters['LOT_SIZE']['stepSize'])
            min_qty = Decimal(filters['LOT_SIZE']['minQty'])
            min_notional = Decimal(filters.get('MIN_NOTIONAL',{}).get('minNotional', '0'))
            qty_dec = Decimal(qty)
            qty_adj = (qty_dec // step) * step
            if qty_adj < min_qty:
                return None
            if min_notional and (qty_adj * Decimal(price) < Decimal(min_notional)):
                return None
            return float(qty_adj)
        except Exception as e:
            logger.debug('adjust_qty_to_step failed: %s', e)
            try:
                return float(Decimal(qty).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN))
            except:
                return float(qty)

    def execute_with_retry(self, symbol, size, signal_data, max_retries=3):
        for attempt in range(max_retries):
            try:
                if self.test_mode or not self.client:
                    return self._simulate_trade(symbol, size, signal_data)
                else:
                    return self._execute_real_trade(symbol, size, signal_data)
            except Exception as e:
                logger.warning('execute attempt %s failed: %s', attempt+1, e)
                time.sleep(2**attempt)
        logger.error('All execute attempts failed for %s', symbol)
        return None

    def _simulate_trade(self, symbol, size, signal_data):
        # deterministic option: seed from timestamp if provided
        seed = int(signal_data.get('seed', time.time())) % 2**32
        import random
        random.seed(seed)
        success = random.random() < 0.85
        if success:
            profit_pct = random.uniform(0.008, 0.02)
            pnl = size * profit_pct
        else:
            loss_pct = random.uniform(0.003, 0.008)
            pnl = -size * loss_pct
        fees = size * 0.002
        net = pnl - fees
        with self.lock:
            before = self.current_balance
            after = before + net
            self.current_balance = after
            trade = {'ts': datetime.utcnow().isoformat(), 'symbol':symbol, 'size':size, 'pnl':net, 'fees':fees, 'success':1 if net>0 else 0, 'balance_before':before, 'balance_after':after}
            self._record_trade(trade)
        logger.info('Simulated trade %s pnl=%s new_balance=%s', symbol, net, self.current_balance)
        return trade

    def _record_trade(self, trade):
        try:
            cur = self.conn.cursor()
            cur.execute('INSERT INTO trades(ts,symbol,size,pnl,fees,success,balance_before,balance_after,meta) VALUES(?,?,?,?,?,?,?,?,?)',
                        (trade['ts'], trade['symbol'], trade['size'], trade['pnl'], trade['fees'], trade['success'], trade['balance_before'], trade['balance_after'], json.dumps({})))
            self.conn.commit()
            self.trades.append(trade)
        except Exception as e:
            logger.exception('record trade failed: %s', e)

    # ---------- Market loop helpers (placeholders) ----------
    def get_market_data(self, symbol):
        # placeholder: implement data fetch (OHLCV) using client or external source
        # returns a small dict used by analyze_market_signal()
        return {'symbol':symbol, 'price': self._get_price(symbol), 'momentum':1.0, 'volume':1000, 'seed': int(time.time())%1000}

    def _get_price(self, symbol):
        try:
            if self.client:
                tick = self.client.get_symbol_ticker(symbol=symbol)
                return float(tick['price'])
        except Exception:
            pass
        return 100.0  # fallback dummy price for simulation

    def analyze_market_signal(self, market_data):
        # placeholder simple signal generator using moving average / momentum in real implementation
        # returns {'strength': float between -1 and 1, 'price': current price, ...}
        price = market_data['price']
        # simple randomish signal based on time seed
        strength = (int(time.time()) % 100) / 100.0
        if strength > 0.6:
            return {'strength': strength, 'price': price, 'volume': market_data.get('volume',0), 'momentum': market_data.get('momentum',0), 'seed': market_data.get('seed')}
        return None

    # ---------- Run loop ----------
    def run(self, duration_hours=24):
        logger.info('Starting main run loop for %s hours', duration_hours)
        end_time = time.time() + duration_hours*3600
        try:
            while self.is_running and time.time() < end_time:
                for symbol in self.config.get('pairs', []):
                    if not self.is_running:
                        break
                    try:
                        with self.lock:
                            # safety quick check
                            if not self._safety_checks_quick(): 
                                continue
                        market = self.get_market_data(symbol)
                        sig = self.analyze_market_signal(market)
                        if sig:
                            # compute safe size (very simple: base risk * balance)
                            base_risk = self.config.get('risk_config',{}).get(symbol, 0.03)
                            max_by_balance = self.current_balance * base_risk
                            size = max_by_balance
                            # adjust qty to step
                            price = sig['price']
                            qty = self._adjust_qty_to_step(symbol, size/price if price>0 else size, price)
                            if not qty:
                                logger.debug('Qty too small or invalid for %s', symbol)
                                continue
                            # execute
                            trade = self.execute_with_retry(symbol, qty*price, sig)
                    except Exception as e:
                        logger.exception('symbol loop error: %s', e)
                # periodic save
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info('KeyboardInterrupt received, shutting down')
            self.activate_emergency_mode()
        finally:
            self._save_state_on_exit()
            logger.info('Run finished, final balance: %s', self.current_balance)

    def _safety_checks_quick(self):
        # check daily PnL
        try:
            cur_daily = self._daily_pnl()
            if cur_daily < - self.config.get('safety_limits',{}).get('max_daily_loss',0.05) * self.initial_capital:
                logger.warning('Daily loss limit exceeded, suspending trading')
                return False
            # exposure check
            total_exposure = sum([p.get('notional',0) for p in self.open_positions])
            max_exp = self.current_balance * self.config.get('safety_limits',{}).get('max_total_exposure',0.3)
            if total_exposure >= max_exp:
                logger.warning('Total exposure limit reached')
                return False
            return True
        except Exception as e:
            logger.exception('_safety_checks_quick failed: %s', e)
            return False

    def _daily_pnl(self):
        today = datetime.utcnow().date().isoformat()
        cur = self.conn.cursor()
        cur.execute("SELECT SUM(pnl) FROM trades WHERE ts LIKE ?", (today+'%',))
        row = cur.fetchone()
        return row[0] if row and row[0] else 0.0

    def _save_state_on_exit(self):
        try:
            state = {'ts': datetime.utcnow().isoformat(), 'balance': self.current_balance, 'trades': len(self.trades)}
            with open('final_state.json','w') as f:
                json.dump(state, f, indent=2)
            logger.info('Saved final state')
        except Exception as e:
            logger.exception('save state on exit failed: %s', e)

if __name__ == '__main__':
    test_mode = os.getenv('USE_TESTNET','true').lower() in ('1','true','yes')
    bot = SecureTradingBot(test_mode=test_mode)
    hours = int(os.getenv('RUN_HOURS','24'))
    bot.run(duration_hours=hours)
