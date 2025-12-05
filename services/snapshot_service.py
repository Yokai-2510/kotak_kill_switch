import time
import json
import os
from pathlib import Path

def safe_serialize(obj):
    """
    Defensive serializer. If an object (like a broken API client)
    fails conversion to string, return a placeholder instead of crashing.
    """
    try:
        if obj is None: return None
        if isinstance(obj, (int, float, bool, str)): return obj
        return str(obj)
    except:
        return "<Unserializable Object>"

def run_snapshot_service(universal_data):
    """
    Dumps the COMPLETE state to JSON.
    Uses safe_serialize to prevent crashes on corrupted objects.
    """
    log = universal_data['sys']['log']
    user_id = universal_data['user_id']
    
    root_dir = Path(__file__).parent.parent
    file_path = root_dir / "logs" / f"{user_id}_snapshot.json"
    
    log.info("Snapshot Service Started.", tags=["SVC", "SNAP"])
    
    while True:
        if not universal_data['signals']['system_active']:
            break
            
        try:
            with universal_data['sys']['lock']:
                # Shallow copy main keys
                # We do NOT deepcopy because that triggers __deepcopy__ on Locks/Sockets which fails
                raw_state = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "user_id": universal_data['user_id'],
                    "status": universal_data.get('status', {}),
                    "risk": universal_data['risk'],
                    "signals": universal_data['signals'],
                    "market": universal_data['market'],
                    "sys": {
                        "config": universal_data['sys']['config'],
                        "creds": universal_data['sys']['creds'],
                        "api_status": "Connected" if universal_data['sys']['api'] else "Disconnected"
                    }
                }

            # Atomic Write
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(raw_state, f, indent=2, default=safe_serialize)
                f.flush()
                os.fsync(f.fileno())
                
            os.replace(temp_path, file_path)
                
        except Exception as e:
            # Log error but keep running
            log.error(f"Snapshot Error: {e}", tags=["SNAP"])
            
        time.sleep(1.0)

    log.info("Snapshot Service Stopped.", tags=["SVC", "SNAP"])