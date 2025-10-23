#!/usr/bin/env python3
import subprocess, sys, os, time
from datetime import datetime

def setup_secure_environment():
    print('Setting up secure environment...')
    for d in ['logs','backups','recovery','monitoring']:
        os.makedirs(d, exist_ok=True)
    print('Folders created')

def check_prereqs():
    try:
        import binance, pandas, numpy, requests
        return True
    except ImportError as e:
        print('Missing module:', e)
        return False

def start_health_monitor():
    p = subprocess.Popen([sys.executable, 'health_monitor.py'])
    print('Started health_monitor (pid=%s)'%p.pid)
    return p

def main():
    if not check_prereqs():
        print('Please install requirements: pip install -r requirements.txt')
        return
    setup_secure_environment()
    p = start_health_monitor()
    print('Starting secure bot...')
    try:
        subprocess.run([sys.executable, 'secure_bot.py'], check=True)
    finally:
        if p:
            p.terminate()

if __name__=='__main__':
    main()
