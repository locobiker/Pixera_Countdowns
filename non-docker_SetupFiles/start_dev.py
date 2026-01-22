import os
import sys
import subprocess
import platform
import time
import signal
from pathlib import Path

# --- Configuration ---
ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "pixera_backend"
FRONTEND_DIR = ROOT_DIR / "pixera_frontend"
LOG_DIR = ROOT_DIR / "logs"

BACKEND_PORT = "8000"
FRONTEND_PORT = "3000"

# --- UI Helpers ---
def log_info(msg): print(f"\033[0;32m[INFO]\033[0m {msg}")
def log_warn(msg): print(f"\033[1;33m[WARN]\033[0m {msg}")
def log_err(msg):  print(f"\033[0;31m[ERROR]\033[0m {msg}")

def main():
    LOG_DIR.mkdir(exist_ok=True)
    
    # 1. Platform Detection
    current_os = platform.system()
    log_info(f"Detected platform: {current_os}")

    # 2. Virtual Environment Setup
    # Check production_build first, then dev venv
    venv_dir = ROOT_DIR / "production_build" / "backend" / "venv"
    if not venv_dir.exists():
        venv_dir = BACKEND_DIR / "venv"

    if not venv_dir.exists():
        log_warn("No virtualenv found. Creating development venv...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Determine Python executable inside venv
    python_exe = venv_dir / ("Scripts/python.exe" if current_os == "Windows" else "bin/python")

    # 3. Install/Update Dependencies
    log_info("Updating Python dependencies...")
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(BACKEND_DIR / "requirements.txt")], check=True)

    # 4. Start Backend (with --reload)
    log_info(f"Starting FastAPI backend on port {BACKEND_PORT} (Hot Reloading)...")
    backend_log = open(LOG_DIR / "backend.log", "w")
    
    # Using 'uvicorn.main' as a module via the venv python
    backend_proc = subprocess.Popen(
        [str(python_exe), "-m", "uvicorn", "pixera_backend.main:app", 
         "--host", "0.0.0.0", "--port", BACKEND_PORT, "--reload"],
        cwd=str(ROOT_DIR),
        stdout=backend_log,
        stderr=backend_log
    )

    # 5. Start Frontend (npm run dev)
    if not (FRONTEND_DIR / "node_modules").exists():
        log_warn("First run: installing Node dependencies...")
        subprocess.run("npm install", cwd=str(FRONTEND_DIR), shell=True)

    log_info(f"Starting Node frontend on port {FRONTEND_PORT} (Vite/Dev)...")
    frontend_log = open(LOG_DIR / "frontend.log", "w")
    
    frontend_proc = subprocess.Popen(
        "npm run dev",
        cwd=str(FRONTEND_DIR),
        stdout=frontend_log,
        stderr=frontend_log,
        shell=True
    )

    log_info("✅ Pixera Dev Environment Started!")
    log_info(f"Backend: http://localhost:{BACKEND_PORT}")
    log_info(f"Frontend: http://localhost:{FRONTEND_PORT}")
    log_info("Press Ctrl+C to stop both services.")

    # 6. Keep script alive and handle shutdown
    try:
        while True:
            time.sleep(1)
            # Optional: check if processes died unexpectedly
            if backend_proc.poll() is not None:
                log_err("Backend process died unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                log_err("Frontend process died unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n")
        log_warn("Shutting down Pixera services...")
    finally:
        # Kill both processes
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_log.close()
        frontend_log.close()
        log_info("Services stopped.")

if __name__ == "__main__":
    main()