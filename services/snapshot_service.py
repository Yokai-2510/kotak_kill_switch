import time
import json
import os
from pathlib import Path

def safe_serialize(obj):
    try:
        if obj is None: return None
        if isinstance(obj, (int, float, bool, str)): return obj
        return str(obj)
    except:
        return "<Unserializable>"

def run_snapshot_service(universal_data):
    log = universal_data['sys']['log']
    user_id = universal_data['user_id']
    
    # Check config for interval, default to 30 seconds if missing
    log_conf = universal_data['sys']['config'].get('logging', {})
    interval = log_conf.get('snapshot_interval', 30)
    
    root_dir = Path(__file__).parent.parent
    file_path = root_dir / "logs" / f"{user_id}_snapshot.json"
    
    log.info(f"Service Started. Interval: {interval}s", tags=["SVC", "SNAP"])
    
    while universal_data['signals']['system_active']:
        try:
            # 1. Capture State (Shallow Copy)
            with universal_data['sys']['lock']:
                raw_state = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "user_id": user_id,
                    "status": universal_data.get('status', {}),
                    "risk": universal_data['risk'],
                    "signals": universal_data['signals'],
                    # Market data can be huge, maybe summary only? Keeping full for now.
                    "market": {
                        "positions_count": len(universal_data['market']['positions']),
                        "orders_count": len(universal_data['market']['orders']),
                        "mtm": universal_data['risk']['mtm_current']
                    },
                    "sys": {
                        "config_active": universal_data['sys']['config'].get('account_active'),
                        "api_connected": bool(universal_data['sys']['api'])
                    }
                }

            # 2. Atomic Write
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(raw_state, f, indent=2, default=safe_serialize)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, file_path)
                
        except Exception as e:
            log.warning(f"Snapshot Failed: {e}", tags=["SNAP"])
            
        # Sleep for the configured interval
        time.sleep(interval)

    log.info("Service Stopped.", tags=["SVC", "SNAP"])