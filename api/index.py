"""
Vercel serverless function entry point for FastAPI
This file is required by Vercel to run Python serverless functions
"""
from app.api.server import app

# Try Vercel's native ASGI support first
# Vercel Python runtime supports ASGI apps directly in newer versions
# If this doesn't work, we'll need to ensure mangum is installed
try:
    from mangum import Mangum
    # Use Mangum if available (for better compatibility)
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Fallback to direct app export (may work with newer Vercel runtime)
    # Note: This might not work on all Vercel plans
    handler = app

# Also export app directly for compatibility
__all__ = ["app", "handler"]

