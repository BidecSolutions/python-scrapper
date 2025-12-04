"""
Replit entry point for FastAPI application
This file is required by Replit to run the application
"""
import uvicorn
import os
import signal
import sys

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print("\nShutting down server...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get port from environment variable (Replit provides this)
    port = int(os.environ.get("PORT", 8000))
    
    try:
        # Run the FastAPI app
        uvicorn.run(
            "app.api.server:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # Disable reload in production
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)

