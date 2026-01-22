import os
import sys
import subprocess
import platform
import time
from pathlib import Path
import psutil
import build_production


# --- Configuration & Paths ---
ROOT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = ROOT_DIR / "production_build"
if (ROOT_DIR / "production_build").exists() == False:
    try:
        build_production.main()
    except Exception as e:
        print(f"❌ Build failed: {e}")
        print("Update aborted to prevent broken deployment.")
        sys.exit(1)    

BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
LOG_DIR = ROOT_DIR / "logs"

# Environment Variables with Defaults
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "3000")
PIXERA_HOST = os.getenv("PIXERA_HOST", "192.168.68.76")
PIXERA_PORT = os.getenv("PIXERA_PORT", "4023")

def is_running(pid_file):
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            if psutil.pid_exists(pid):
                return pid
        except (ValueError, ProcessLookupError):
            return None
    return None

def main():
    # Ensure logs directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Check if already running
    for service in ["backend", "frontend"]:
        pid = is_running(LOG_DIR / f"{service}.pid")
        if pid:
            print(f"⚠️  {service.capitalize()} is already running (PID: {pid})")
            print(f"   Stop it first before restarting.")
            sys.exit(1)

    # 2. Setup Virtual Environment
    print("--- Setting up Python virtual environment ---")
    venv_dir = BACKEND_DIR / "venv"
    python_exe = venv_dir / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")
    
    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # 3. Install Dependencies
    print("--- Installing backend dependencies ---")
    subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(BACKEND_DIR / "requirements.txt")], check=True)

    # 4. Start Backend
    print(f"\nStarting FastAPI backend on port {BACKEND_PORT}...")
    backend_log = open(LOG_DIR / "backend.log", "a")
    
    # Setup environment for the subprocess
    env = os.environ.copy()
    env["PIXERA_HOST"] = PIXERA_HOST
    env["PIXERA_PORT"] = PIXERA_PORT

    backend_proc = subprocess.Popen(
        [str(python_exe), "-m", "uvicorn", "backend.main:app", 
         "--host", "0.0.0.0", "--port", BACKEND_PORT, "--workers", "1"],
        cwd=str(ROOT_DIR),
        stdout=backend_log,
        stderr=backend_log,
        env=env,
        start_new_session=True # Equivalent to nohup
    )
    (LOG_DIR / "backend.pid").write_text(str(backend_proc.pid))
    print(f"✅ Backend started (PID: {backend_proc.pid})")

    # 5. Start Frontend
    print(f"\nStarting frontend server on port {FRONTEND_PORT}...")
    frontend_log = open(LOG_DIR / "frontend.log", "a")
    
    # Use npx serve (works on both if Node is installed)
    try:
        shell_cmd = f"npx --yes serve -s . -l {FRONTEND_PORT}"
        frontend_proc = subprocess.Popen(
            shell_cmd,
            cwd=str(FRONTEND_DIR),
            stdout=frontend_log,
            stderr=frontend_log,
            shell=True,
            start_new_session=True
        )
        (LOG_DIR / "frontend.pid").write_text(str(frontend_proc.pid))
        print(f"✅ Frontend started (PID: {frontend_proc.pid})")
    except Exception as e:
        print(f"⚠️  Could not start frontend: {e}")

    print("\n" + "="*40)
    print("✅ Pixera Countdowns started!")
    print("="*40)
    print(f"Backend:  http://localhost:{BACKEND_PORT}")
    print(f"Frontend: http://localhost:{FRONTEND_PORT}")
    print(f"Logs:     {LOG_DIR}")

if __name__ == "__main__":
    main()