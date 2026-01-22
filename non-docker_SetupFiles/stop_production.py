import os
import time
from pathlib import Path
import psutil

# --- Configuration & Paths ---
ROOT_DIR = Path(__file__).parent.resolve()
if (ROOT_DIR / "production_build").exists():
    ROOT_DIR = ROOT_DIR / "production_build"

LOG_DIR = ROOT_DIR / "logs"

def stop_process(name):
    pid_file = LOG_DIR / f"{name}.pid"
    
    if not pid_file.exists():
        print(f"ℹ️  No PID file found for {name}. It might not be running.")
        return

    try:
        pid = int(pid_file.read_text().strip())
        
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            print(f"Stopping {name} (PID: {pid})...")
            
            # 1. Try a gentle termination
            proc.terminate()
            
            # Wait up to 3 seconds for it to exit
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                # 2. Force kill if still alive
                print(f"⚠️  {name} did not exit gracefully, force killing...")
                proc.kill()
            
            print(f"✅ {name.capitalize()} stopped")
        else:
            print(f"ℹ️  Process {pid} for {name} is already gone.")
            
    except (ValueError, psutil.NoSuchProcess):
        print(f"ℹ️  {name.capitalize()} process not found.")
    except Exception as e:
        print(f"❌ Error stopping {name}: {e}")
    finally:
        # Always remove the PID file
        if pid_file.exists():
            pid_file.unlink()

def main():
    print("Stopping Pixera Countdowns...\n")
    
    # Stop services
    stop_process("backend")
    stop_process("frontend")
    
    print("\n✅ All services stopped")

if __name__ == "__main__":
    main()