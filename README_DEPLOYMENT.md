# Pixera Countdowns - Production Deployment Guide

This guide explains how to package, deploy, and update the Pixera Countdowns application in production.

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** and **npm** (for frontend build and optional serving)
- **Bash** (for deployment scripts)

## Quick Start

### 1. Build for Production

Run the build script to create a production package:

```bash
./build_production.sh
```

This will:
- Build the React frontend for production
- Copy backend code
- Create a `production_build/` directory with everything needed

### 2. Deploy to Production Server

Copy the `production_build/` directory to your production server:

```bash
# Example: Copy to remote server
scp -r production_build/ user@production-server:/opt/pixera-countdowns/

# Or use rsync
rsync -av production_build/ user@production-server:/opt/pixera-countdowns/
```

### 3. Start on Production Server

On the production server:

```bash
cd /opt/pixera-countdowns
chmod +x start_production.sh
./start_production.sh
```

The script will:
- Set up Python virtual environment
- Install backend dependencies
- Start the FastAPI backend
- Start the frontend server (if Node.js is available)

## Configuration

### Environment Variables

You can configure the application using environment variables:

```bash
# Pixera connection settings
export PIXERA_HOST=192.168.68.72
export PIXERA_PORT=4023

# Server ports
export BACKEND_PORT=8000
export FRONTEND_PORT=3000
```

Or edit `start_production.sh` to set default values.

### Backend Configuration

Edit `backend/main.py` to change:
- `PIXERA_HOST` - IP address of Pixera device
- `PIXERA_PORT` - Port for Pixera communication (default: 4023)

## Updating the Application

### Option 1: Using Update Script (Recommended)

1. Build a new version:
   ```bash
   ./build_production.sh
   ```

2. Copy the updated `production_build/` to your server

3. On the production server, run:
   ```bash
   ./update_production.sh
   ```

This will:
- Stop running services
- Update dependencies if needed
- Rebuild frontend if needed
- Restart services

### Option 2: Manual Update

1. Stop the application:
   ```bash
   ./stop_production.sh
   ```

2. Replace files in `backend/` and `frontend/` directories

3. Update dependencies:
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   
   cd ../frontend
   npm install
   npm run build
   ```

4. Start again:
   ```bash
   ./start_production.sh
   ```

## Managing the Application

### Start
```bash
./start_production.sh
```

### Stop
```bash
./stop_production.sh
```

### Check Status
```bash
# Check if backend is running
ps -p $(cat logs/backend.pid)

# Check if frontend is running
ps -p $(cat logs/frontend.pid)
```

### View Logs
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log
```

## Production Considerations

### Using a Reverse Proxy (Recommended)

For production, consider using nginx or Apache as a reverse proxy:

**nginx example:**
```nginx
server {
    listen 80;
    server_name pixera-countdowns.example.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Running as a Service

Create a systemd service file (`/etc/systemd/system/pixera-countdowns.service`):

```ini
[Unit]
Description=Pixera Countdowns Application
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/pixera-countdowns
ExecStart=/opt/pixera-countdowns/start_production.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable pixera-countdowns
sudo systemctl start pixera-countdowns
sudo systemctl status pixera-countdowns
```

### Firewall Configuration

Ensure ports are open:
```bash
# Backend
sudo ufw allow 8000/tcp

# Frontend
sudo ufw allow 3000/tcp
```

## Troubleshooting

### Backend won't start
- Check Python version: `python3 --version` (needs 3.8+)
- Check virtual environment: `ls backend/venv/`
- Check logs: `tail -f logs/backend.log`
- Verify Pixera connection settings in `backend/main.py`

### Frontend won't start
- Check Node.js: `node --version` (needs 16+)
- Install serve: `npm install -g serve`
- Or use your own web server to serve the `frontend/` directory
- Check logs: `tail -f logs/frontend.log`

### Port already in use
- Find process using port: `lsof -i :8000` or `lsof -i :3000`
- Kill the process or change ports in `start_production.sh`

### WebSocket connection issues
- Ensure backend is running on the correct port
- Check firewall settings
- Verify CORS settings in `backend/main.py`

## File Structure

```
production_build/
├── backend/              # FastAPI backend
│   ├── main.py          # Main application
│   ├── requirements.txt # Python dependencies
│   └── venv/            # Python virtual environment (created on first run)
├── frontend/             # Built React frontend
│   └── [built files]    # Static files from vite build
├── logs/                # Application logs
│   ├── backend.log
│   ├── frontend.log
│   ├── backend.pid
│   └── frontend.pid
├── start_production.sh  # Start script
├── stop_production.sh   # Stop script
├── update_production.sh # Update script
└── VERSION             # Build version
```

## Support

For issues or questions, check the logs first:
- Backend: `logs/backend.log`
- Frontend: `logs/frontend.log`

