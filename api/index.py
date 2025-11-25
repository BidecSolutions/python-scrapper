"""
Vercel serverless function entry point for FastAPI
This file is required by Vercel to run Python serverless functions
"""
from app.api.server import app

# Vercel supports ASGI apps directly
# Export the FastAPI app as the handler
# Vercel will automatically wrap it for serverless execution
handler = app

# Also export app directly for compatibility
__all__ = ["app", "handler"]

