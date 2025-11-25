"""
Replit entry point for FastAPI application
This file is required by Replit to run the application
"""
import uvicorn
import os

if __name__ == "__main__":
    # Get port from environment variable (Replit provides this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the FastAPI app
    uvicorn.run(
        "app.api.server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
    )

