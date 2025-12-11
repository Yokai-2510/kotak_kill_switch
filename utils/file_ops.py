import json
from pathlib import Path
from datetime import datetime

def update_kill_history_disk(user_id, verified):
    """
    Updates config.json with the kill event timestamp and lock status.
    """
    try:
        root = Path(__file__).parent.parent
        path = root / "source" / "config.json"
        
        # 1. Read
        with open(path, 'r') as f:
            data = json.load(f)
            
        # 2. Update
        if user_id in data:
            today_str = datetime.now().strftime("%Y-%m-%d")
            ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            data[user_id]['kill_history'] = {
                "locked_date": today_str if verified else None,
                "timestamp": ts_str,
                "verified": verified
            }
            
            # 3. Write
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
                
    except Exception as e:
        print(f"Critical Disk Error in file_ops: {e}")