import os
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# --- Configuration & Paths ---
ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "pixera_backend"
FRONTEND_DIR = ROOT_DIR / "pixera_frontend"
BUILD_DIR = ROOT_DIR / "production_build"

def run_command(command, cwd=None):
    """Helper to run shell commands and exit on error."""
    try:
        subprocess.run(command, cwd=cwd, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}")
        exit(1)

def main():
    print("=========================================")
    print("Building Pixera Countdowns for Production")
    print("=========================================")

    # 1. Clean previous build
    if BUILD_DIR.exists():
        print("Cleaning previous build...")
        shutil.rmtree(BUILD_DIR)
    
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "logs").mkdir(exist_ok=True)

    # 2. Build Frontend
    print("\n--- Building frontend ---")
    if not (FRONTEND_DIR / "node_modules").exists():
        print("Installing frontend dependencies...")
        run_command("npm install", cwd=FRONTEND_DIR)

    print("Running production build...")
    run_command("npm run build", cwd=FRONTEND_DIR)

    # Copy frontend build (usually in /dist)
    dist_dir = FRONTEND_DIR / "dist"
    if dist_dir.exists():
        print("Copying frontend build...")
        shutil.copytree(dist_dir, BUILD_DIR / "frontend")
    else:
        print("⚠️ Warning: dist folder not found in frontend!")

    # 3. Copy Backend
    print("\n--- Copying backend ---")
    backend_dest = BUILD_DIR / "backend"
    
    # We use a custom ignore function to mimic rsync --exclude
    def ignore_files(dir, files):
        return [f for f in files if f in [
            '__pycache__', 'venv', '.git', '.env', '.gitignore'
        ] or f.endswith(('.pyc', '.pyo', '.log'))]

    shutil.copytree(BACKEND_DIR, backend_dest, ignore=ignore_files)

    # 4. Copy configuration and helper scripts
    print("\n--- Copying configuration files ---")
    files_to_copy = [
        "start_pixera.py", 
        "stop_pixera.py", 
        "README_DEPLOYMENT.md",
        "DEPLOYMENT_QUICK_START.md"
    ]

    for filename in files_to_copy:
        src = ROOT_DIR / filename
        if src.exists():
            shutil.copy2(src, BUILD_DIR / filename)
        else:
            print(f"ℹ️  Skipping {filename} (not found)")

    # 5. Create a version file
    version_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    (BUILD_DIR / "VERSION").write_text(version_str)

    print("\n" + "="*41)
    print("✅ Build complete!")
    print(f"Production build is in: {BUILD_DIR}")
    print("="*41)
    print(f"\nNext steps:\n1. Review the build in: {BUILD_DIR}")
    print(f"2. Copy {BUILD_DIR.name} to your production server")
    print(f"3. Run 'python start_pixera.py' on the server\n")

if __name__ == "__main__":
    main()