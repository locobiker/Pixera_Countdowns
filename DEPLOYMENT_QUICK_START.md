# Quick Deployment Guide

## Build and Package

```bash
# Option 1: Just build
./build_production.sh

# Option 2: Build and create tarball
./package_for_deployment.sh
```

## Deploy to Production

### Step 1: Copy to Server
```bash
# If you built locally:
scp -r production_build/ user@server:/opt/pixera-countdowns/

# If you created a package:
scp pixera-countdowns-*.tar.gz user@server:/opt/
```

### Step 2: On Production Server
```bash
# If using directory:
cd /opt/pixera-countdowns
./start_production.sh

# If using tarball:
cd /opt
tar -xzf pixera-countdowns-*.tar.gz
cd production_build
./start_production.sh
```

## Update Application

```bash
# On production server:
cd /opt/pixera-countdowns
./update_production.sh
```

Or manually:
1. Stop: `./stop_production.sh`
2. Replace files
3. Start: `./start_production.sh`

## Configuration

Edit these before starting:
- **Pixera IP**: Set `PIXERA_HOST` environment variable or edit `backend/main.py`
- **Ports**: Set `BACKEND_PORT` and `FRONTEND_PORT` environment variables

## Access

- Frontend: http://your-server-ip:3000
- Backend API: http://your-server-ip:8000

## Troubleshooting

- **Check logs**: `tail -f logs/backend.log` or `tail -f logs/frontend.log`
- **Check if running**: `ps -p $(cat logs/backend.pid)`
- **Stop everything**: `./stop_production.sh`

For detailed information, see `README_DEPLOYMENT.md`

