# NPM Scripts Guide

Quick reference for running LeadFlux using npm scripts.

## Prerequisites

Install dependencies first:
```bash
npm install
cd frontend && npm install
cd ..
```

Or use the convenience script:
```bash
npm run install:all
```

## Available Scripts

### Development

#### `npm run dev`
Runs both backend and frontend in development mode with hot-reload.

```bash
npm run dev
```

**What it does:**
- Starts FastAPI backend on http://localhost:8002
- Starts Next.js frontend on http://localhost:3000
- Both servers auto-reload on file changes

---

#### `npm run dev:backend`
Runs only the backend server.

```bash
npm run dev:backend
```

**Access:**
- API: http://localhost:8002
- API Docs: http://localhost:8002/docs

---

#### `npm run dev:frontend`
Runs only the frontend server.

```bash
npm run dev:frontend
```

**Access:**
- Frontend: http://localhost:3000

---

### Production

#### `npm run start`
Runs both servers in production mode (no hot-reload).

```bash
npm run start
```

**Note:** Requires building the frontend first:
```bash
npm run build
npm run start
```

---

#### `npm run start:backend`
Runs only the backend in production mode.

```bash
npm run start:backend
```

---

#### `npm run start:frontend`
Runs only the frontend in production mode.

```bash
npm run start:frontend
```

---

### Build

#### `npm run build`
Builds the frontend for production.

```bash
npm run build
```

---

### Installation

#### `npm run install:all`
Installs all dependencies (root + frontend).

```bash
npm run install:all
```

---

#### `npm run install:backend`
Installs Python backend dependencies.

```bash
npm run install:backend
```

**Note:** Requires Python and pip. Creates/uses virtual environment if available.

---

#### `npm run install:frontend`
Installs frontend dependencies.

```bash
npm run install:frontend
```

---

## Quick Start

### First Time Setup
```bash
# Install all dependencies
npm run install:all

# Or separately:
npm run install:backend
npm run install:frontend
```

### Daily Development
```bash
# Start both servers
npm run dev
```

### Run Only One Server
```bash
# Backend only
npm run dev:backend

# Frontend only (in another terminal)
npm run dev:frontend
```

---

## Troubleshooting

### "concurrently" not found
Install root dependencies:
```bash
npm install
```

### Python not found
Make sure Python 3.8+ is installed and in your PATH:
```bash
python --version
```

### Port already in use
Change ports in the scripts or stop the process using the port:
```bash
# Windows
netstat -ano | findstr :8002
taskkill /PID <PID> /F
```

### Virtual Environment
If using a virtual environment, activate it first:
```bash
# Windows
.\venv\Scripts\Activate.ps1

# Then run
npm run dev:backend
```

Or modify the script to activate automatically:
```json
"dev:backend": ".\\venv\\Scripts\\Activate.ps1 && python -m uvicorn app.api.server:app --reload"
```

---

## Script Details

### Root package.json Scripts

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `concurrently "npm run dev:backend" "npm run dev:frontend"` | Run both servers |
| `dev:backend` | `python -m uvicorn app.api.server:app --reload` | Backend dev server |
| `dev:frontend` | `cd frontend && npm run dev` | Frontend dev server |
| `start` | `concurrently "npm run start:backend" "npm run start:frontend"` | Run both in production |
| `build` | `cd frontend && npm run build` | Build frontend |
| `install:all` | Install root + frontend deps | Install everything |

---

## Environment Variables

### Backend (.env)
Create `.env` in project root:
```env
GOOGLE_PLACES_API_KEY=your_key
GOOGLE_SEARCH_API_KEY=your_key
GOOGLE_SEARCH_CX=your_cx
BING_SEARCH_API_KEY=your_key
GROQ_API_KEY=your_key
```

### Frontend (.env.local)
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8002
```

---

## Notes

- **Development mode** (`npm run dev`): Hot-reload enabled, runs both servers
- **Production mode** (`npm run start`): No hot-reload, optimized builds
- Use `Ctrl+C` to stop servers
- Backend runs on **port 8002**
- Frontend runs on **port 3000**
- `concurrently` runs both commands in parallel and shows output from both

