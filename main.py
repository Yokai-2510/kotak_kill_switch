import sys
from utils.startup import load_registry
from services.engine import TradeEngine
from gui.gui import launch_gui


def main():

    print("\n=== SYSTEM STARTUP ===")
    
    
    user_ids = load_registry()
    if not user_ids:
        print("CRITICAL: No users found.")
        sys.exit(1)        


    # 1. Initialize Engines (Idle Mode)
    engines = [TradeEngine(uid) for uid in user_ids]     
    print(f">>> Initialized {len(engines)} Engines.")


    # 2. Launch GUI
    launch_gui(engines)


if __name__ == "__main__":
    main()
