
from gui.gui_app import KillSwitchApp

def launch_gui(engines):
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