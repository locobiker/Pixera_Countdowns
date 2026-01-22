import shutil
import os
from pathlib import Path

# --- Configuration ---
ROOT_DIR = Path(__file__).parent.resolve()

def remove_path(path: Path):
    """Safely removes a file or directory tree."""
    if not path.exists():
        return
    
    try:
        if path.is_file() or path.is_symlink():
            path.unlink()
            print(f"  Removed file: {path.relative_to(ROOT_DIR)}")
        elif path.is_dir():
            shutil.rmtree(path)
            print(f"  Removed dir:  {path.relative_to(ROOT_DIR)}")
    except Exception as e:
        print(f"  ⚠️  Could not remove {path.name}: {e}")

def main():
    print("=========================================")
    print("Cleaning up Pixera Countdowns project")
    print("=========================================")

    # 1. Remove Python Cache & Compiled files
    print("\nCleaning Python artifacts...")
    # rglob = recursive glob
    for p in ROOT_DIR.rglob("__pycache__"):
        remove_path(p)
    
    for ext in ["*.pyc", "*.pyo", "*.pyd"]:
        for p in ROOT_DIR.rglob(ext):
            remove_path(p)

    # 2. Remove Virtual Environments
    print("\nCleaning virtual environments...")
    remove_path(ROOT_DIR / "venv")
    remove_path(ROOT_DIR / "pixera_backend" / "venv")

    # 3. Remove Node/Frontend artifacts
    print("\nCleaning Node.js artifacts...")
    remove_path(ROOT_DIR / "pixera_frontend" / "node_modules")
    remove_path(ROOT_DIR / "pixera_frontend" / "dist")

    # 4. Remove Build Artifacts
    print("\nCleaning production build folder...")
    remove_path(ROOT_DIR / "production_build")

    # 5. Clean Logs (but keep directory)
    print("\nCleaning log files...")
    log_dir = ROOT_DIR / "logs"
    if log_dir.exists():
        for log_file in log_dir.glob("*"):
            if log_file.suffix in [".log", ".pid"] or "log" in log_file.name:
                remove_path(log_file)
        # Re-create .gitkeep to keep folder in version control
        (log_dir / ".gitkeep").touch()

    # 6. Specific Unused Files
    print("\nRemoving specific unused/deprecated files...")
    unused_files = [
        ROOT_DIR / "pixera_frontend" / "server.js",
        ROOT_DIR / "pixera_frontend" / "public",
        ROOT_DIR / "pixera_frontend" / "postcss.config.cjs",
        ROOT_DIR / "pixera_frontend" / "tailwind.config.cjs",
    ]
    
    # Handle the root package-lock check
    root_lock = ROOT_DIR / "package-lock.json"
    if root_lock.exists() and not (ROOT_DIR / "package.json").exists():
        unused_files.append(root_lock)

    for f in unused_files:
        remove_path(f)

    print("\n" + "="*41)
    print("✅ Cleanup complete!")
    print("=========================================")

if __name__ == "__main__":
    main()