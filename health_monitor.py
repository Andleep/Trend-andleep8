#!/usr/bin/env python3
import psutil, logging, time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('health_monitor')

def check_system_health():
    s = {'ts': datetime.utcnow().isoformat(), 'cpu': psutil.cpu_percent(), 'mem': psutil.virtual_memory().percent, 'disk': psutil.disk_usage('/').percent}
    alerts = []
    if s['cpu']>80: alerts.append('cpu_high')
    if s['mem']>85: alerts.append('mem_high')
    if s['disk']>90: alerts.append('disk_high')
    if alerts:
        logger.warning('System alerts: %s', alerts)
    else:
        logger.info('System OK: cpu=%s mem=%s disk=%s', s['cpu'], s['mem'], s['disk'])
    return s

if __name__=='__main__':
    while True:
        check_system_health()
        time.sleep(60)
