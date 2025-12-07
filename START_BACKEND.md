# How to Start the Backend (Python FastAPI)

## Prerequisites
Make sure you have:
- Python 3.8+ installed
- All dependencies installed: `pip install -r requirements.txt`
- `.env` file configured with `DATABASE_URL`

## Start the Backend Server

### Option 1: Using main.py (Recommended)
```bash
cd python-scrapper
python main.py
```

The server will start on: **http://localhost:8000**

### Option 2: Using Uvicorn directly
```bash
cd python-scrapper
uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using the PORT environment variable
```bash
cd python-scrapper
set PORT=8002
python main.py
```

## Verify Backend is Running

1. Open browser: http://localhost:8000/docs
2. You should see the FastAPI Swagger documentation
3. Or test: http://localhost:8000/health

## Default Ports
- **Port 8000**: Default backend port
- **Port 8002**: Alternative port (if set in environment)

## Stop the Server
Press `Ctrl + C` in the terminal

