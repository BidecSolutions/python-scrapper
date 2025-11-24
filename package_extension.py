"""Script to package Chrome extension as a zip file"""
import zipfile
import os
from pathlib import Path

EXTENSION_DIR = Path("chrome-extension")
OUTPUT_FILE = "leadflux-email-finder-extension.zip"

def package_extension():
    """Package the chrome-extension directory into a zip file"""
    if not EXTENSION_DIR.exists():
        print(f"Error: {EXTENSION_DIR} directory not found")
        return False
    
    print(f"Packaging extension from {EXTENSION_DIR}...")
    
    with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(EXTENSION_DIR):
            # Skip hidden files and directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = Path(root) / file
                # Use relative path for zip (chrome-extension/file)
                arcname = file_path.relative_to(EXTENSION_DIR.parent)
                zip_file.write(file_path, arcname)
                print(f"  Added: {arcname}")
    
    print(f"\n✅ Extension packaged successfully: {OUTPUT_FILE}")
    print(f"   Size: {os.path.getsize(OUTPUT_FILE) / 1024:.2f} KB")
    return True

if __name__ == "__main__":
    package_extension()

