"""
Vercel serverless function entry point for FastAPI
This file is required by Vercel to run Python serverless functions
"""
from mangum import Mangum
from app.api.server import app

# Wrap FastAPI app with Mangum for serverless compatibility
# Mangum converts ASGI to the format expected by serverless platforms
handler = Mangum(app, lifespan="off")

# Also export app directly for compatibility
__all__ = ["app", "handler"]

