# PowerShell Scripts Guide

Quick reference for running the LeadFlux application on Windows.

## Available Scripts

### 1. `start-backend.ps1`
Starts the FastAPI backend server on port 8002.

**Usage:**
```powershell
.\start-backend.ps1
```

**Features:**
- Automatically activates virtual environment if found
- Checks for Python installation
- Installs uvicorn if missing
- Starts server with auto-reload enabled

**Access:**
- API: http://localhost:8002
- API Docs: http://localhost:8002/docs

---

### 2. `start-frontend.ps1`
Starts the Next.js frontend server on port 3000.

**Usage:**
```powershell
.\start-frontend.ps1
```

**Features:**
- Checks for Node.js and npm
- Installs dependencies if `node_modules` is missing
- Creates `.env.local` with default settings if missing
- Starts development server with hot reload

**Access:**
- Frontend: http://localhost:3000

---

### 3. `start-all.ps1`
Starts both backend and frontend servers in separate windows.

**Usage:**
```powershell
.\start-all.ps1
```

**Features:**
- Opens two PowerShell windows (one for each server)
- Waits 3 seconds between starting servers
- Shows helpful information about server URLs

**Note:** Close the individual windows to stop each server.

---

### 4. `stop-all.ps1`
Stops all running servers and cleans up processes.

**Usage:**
```powershell
.\stop-all.ps1
```

**Features:**
- Stops processes on ports 8002, 3000, 3001
- Kills Node.js processes
- Kills Python server processes

---

## Quick Start

### Option 1: Start Everything at Once
```powershell
.\start-all.ps1
```

### Option 2: Start Separately
```powershell
# Terminal 1 - Backend
.\start-backend.ps1

# Terminal 2 - Frontend
.\start-frontend.ps1
```

### Option 3: Manual Start
```powershell
# Backend
cd .
python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8002 --reload

# Frontend (in another terminal)
cd frontend
npm run dev
```

---

## Troubleshooting

### "Execution Policy" Error
If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use
If a port is already in use:
```powershell
# Stop all servers
.\stop-all.ps1

# Or manually kill processes on specific ports
netstat -ano | findstr :8002
taskkill /PID <PID> /F
```

### Python Not Found
Make sure Python is in your PATH:
```powershell
# Check Python
python --version

# If not found, add Python to PATH or use full path
C:\Python312\python.exe -m uvicorn app.api.server:app --reload
```

### Node.js Not Found
Install Node.js from https://nodejs.org/ (version 18+ recommended)

### Virtual Environment Issues
Create a new virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Environment Setup

### Backend (.env)
Create a `.env` file in the project root:
```env
GOOGLE_PLACES_API_KEY=your_key_here
GOOGLE_SEARCH_API_KEY=your_key_here
GOOGLE_SEARCH_CX=your_cx_here
BING_SEARCH_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
OPENCAGE_API_KEY=your_key_here
```

### Frontend (.env.local)
The `start-frontend.ps1` script automatically creates `.env.local` with:
```env
NEXT_PUBLIC_API_URL=http://localhost:8002
```

---

## Development Workflow

1. **First Time Setup:**
   ```powershell
   # Install backend dependencies
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

2. **Daily Development:**
   ```powershell
   # Start both servers
   .\start-all.ps1
   ```

3. **Stop Servers:**
   ```powershell
   .\stop-all.ps1
   ```

---

## Notes

- Backend runs on **port 8002**
- Frontend runs on **port 3000**
- Both servers support hot-reload (auto-restart on file changes)
- Use `Ctrl+C` in the terminal to stop individual servers
- Use `stop-all.ps1` to clean up all processes

