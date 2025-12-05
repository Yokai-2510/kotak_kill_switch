#   main.py
#   KOTAK KILL SWITCH - MULTI-ACCOUNT ORCHESTRATOR


import sys
import time
from utils.startup import load_registry
from services.engine import TradeEngine
from gui.gui_app import KillSwitchApp


def main():

    # ====================  1. INITIALIZATION  ====================
    print("\n=== SYSTEM STARTUP ===")
    
    user_ids = load_registry()
    if not user_ids:
        print("CRITICAL: No users found in registry.")
        sys.exit(1)
        
    engines = [TradeEngine(uid) for uid in user_ids]
    print(f">>> Initialized {len(engines)} Engines.")


    # ====================  2. AUTHENTICATION  ====================
    print("\n>>> Authenticating Clients...")
    for engine in engines:
        engine.authenticate()


   # ====================  3. PRE-FLIGHT CHECKS  ====================
    print("\n>>> Running System Checks...")
    for engine in engines:
        engine.run_preflight_check()

 
    # ====================  4. START SERVICES  ====================
    print("\n>>> Starting Background Threads...")
    for engine in engines:
        engine.start_services()

 
   # ====================  5. LAUNCH GUI  ====================
    print(f"\n>>> System Active. Launching GUI for {len(engines)} accounts...")
    
    try:
        app = KillSwitchApp(engines)
        app.mainloop()
            
    except KeyboardInterrupt:
        print("\nUser Interrupted via Terminal.")
    except Exception as e:
        print(f"\nCRITICAL GUI CRASH: {e}")
    finally:
        print("\n=== SYSTEM SHUTDOWN INITIATED ===")
        print("Stopping all engines...")
        for engine in engines:
            engine.stop()
        print("Goodbye.")


if __name__ == "__main__":
    main()