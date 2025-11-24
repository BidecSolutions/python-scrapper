"""Chrome extension download and installation API routes"""
import os
import zipfile
import io
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import Response, FileResponse

router = APIRouter()

EXTENSION_DIR = Path("chrome-extension")


@router.get("/extension/download")
def download_extension():
    """
    Download Chrome extension as a zip file
    
    Packages the chrome-extension directory into a zip file for easy installation
    """
    if not EXTENSION_DIR.exists():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="Chrome extension not found. Please ensure chrome-extension/ directory exists."
        )
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add all files from chrome-extension directory
        for root, dirs, files in os.walk(EXTENSION_DIR):
            # Skip hidden files and directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                # Use relative path for zip
                arcname = file_path.relative_to(EXTENSION_DIR.parent)
                zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=leadflux-email-finder-extension.zip"
        }
    )


@router.get("/extension/manifest")
def get_extension_manifest():
    """Get extension manifest.json for verification"""
    manifest_path = EXTENSION_DIR / "manifest.json"
    
    if not manifest_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Extension manifest not found")
    
    import json
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    return manifest

