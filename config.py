import os

# إعدادات Binance API
BINANCE_CONFIG = {
    'api_key': os.getenv('BINANCE_API_KEY', ''),
    'api_secret': os.getenv('BINANCE_API_SECRET', ''),
    'testnet': os.getenv('TESTNET', 'true').lower() == 'true'
}

# إعدادات التداول
TRADING_CONFIG = {
    'initial_balance': float(os.getenv('INITIAL_BALANCE', '1000.0')),
    'risk_per_trade': float(os.getenv('RISK_PER_TRADE', '0.02')),
    'max_trade_amount': 100.0,
    'min_trade_amount': 10.0
}

# إعدادات الخوارزمية
ALGORITHM_CONFIG = {
    'rsi_period': 14,
    'wt_fast': 10,
    'wt_slow': 21,
    'cci_period': 20,
    'adx_period': 14
}
