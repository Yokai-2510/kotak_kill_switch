import json
import sys
from pathlib import Path

def load_registry():
    """
    Reads credentials.json and returns a list of User IDs (keys).
    """
    root_dir = Path(__file__).parent.parent
    creds_path = root_dir / "source" / "credentials.json"
    
    if not creds_path.exists():
        print(f"CRITICAL: Credentials file not found at {creds_path}")
        sys.exit(1)
        
    try:
        with open(creds_path, 'r') as f:
            data = json.load(f)
            return list(data.keys())
    except Exception as e:
        print(f"CRITICAL: Failed to load registry: {e}")
        sys.exit(1)