import sys
import subprocess
import time
from pathlib import Path

# Import the logic from our previous scripts (assumes they are in the same folder)
import stop_production
import build_production

# --- Configuration ---
ROOT_DIR = Path(__file__).parent.resolve()
START_SCRIPT = ROOT_DIR / "start_production.py"

def main():
    print("=========================================")
    print("🔄 Updating Pixera Countdowns")
    print("=========================================")

    # 1. Stop services using our existing logic
    # This handles the PID checks and force-kills across OSs
    print("\nStep 1: Shutting down services...")
    stop_production.main()

    # 2. Run the build process
    # This cleans the production_build folder and recompiles everything
    print("\nStep 2: Performing clean re-build...")
    try:
        build_production.main()
    except Exception as e:
        print(f"❌ Build failed: {e}")
        print("Update aborted to prevent broken deployment.")
        sys.exit(1)

    # 3. Restart the services
    print("\nStep 3: Restarting services...")
    if START_SCRIPT.exists():
        # We run this as a separate process so it can detach properly
        try:
            # sys.executable ensures we use the same python version running this script
            subprocess.Popen([sys.executable, str(START_SCRIPT)], 
                             cwd=str(ROOT_DIR),
                             start_new_session=True)
            print("✅ Start command issued.")
        except Exception as e:
            print(f"❌ Failed to restart services: {e}")
            sys.exit(1)
    else:
        print(f"❌ Error: {START_SCRIPT.name} not found. Could not restart.")

    print("\n" + "="*41)
    print("✅ Update complete!")
    print("=========================================")

if __name__ == "__main__":
    main()