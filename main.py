import sys
from utils.startup import load_registry
from services.engine import TradeEngine
from gui.gui_app import KillSwitchApp


def main():

    print("\n=== SYSTEM STARTUP (Dynamic Architecture) ===")
    
    user_ids = load_registry()
    if not user_ids:
        print("CRITICAL: No users found.")
        sys.exit(1)
        
    # 1. Initialize Engines (Idle Mode)
    engines = [TradeEngine(uid) for uid in user_ids]     
    print(f">>> Initialized {len(engines)} Engines.")

    # 2. Launch GUI
    # The GUI now acts as the controller.
    print(f"\n>>> Launching GUI...")
    try:
        app = KillSwitchApp(engines)
        app.mainloop()
    except KeyboardInterrupt:
        print("\nUser Exit.")
    except Exception as e:
        print(f"\nCRITICAL CRASH : {e}")
    finally:
        print("\n=== SHUTDOWN ===")
        for engine in engines:
            engine.stop_session()
        print("Done.")


if __name__ == "__main__":
    main()