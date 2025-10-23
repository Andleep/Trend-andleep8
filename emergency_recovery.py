#!/usr/bin/env python3
import json, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('recovery')

def recover_from_emergency():
    try:
        with open('emergency_state.json','r') as f:
            data = json.load(f)
        logger.info('Recovered emergency state timestamp=%s balance=%s', data.get('ts'), data.get('balance'))
        # For safety, we just log; manual review recommended.
        with open('recovery_log.json','w') as out:
            json.dump({'recovered_at': datetime.utcnow().isoformat(), 'source': data}, out, indent=2)
        logger.info('Recovery log saved to recovery_log.json')
    except FileNotFoundError:
        logger.info('No emergency_state.json found')
    except Exception as e:
        logger.exception('Recovery failed: %s', e)

if __name__=='__main__':
    recover_from_emergency()
