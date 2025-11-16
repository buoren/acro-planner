"""
React Native app interface for non-admin users.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/app", tags=["app"])


@router.get("")
async def app_interface(request: Request):
    """Serve the React Native web app for non-admin users"""
    try:
        # Serve the main index.html file
        app_path = Path("static/app/index.html")
        if not app_path.exists():
            raise HTTPException(status_code=404, detail="App interface not found")
        
        # Read the HTML file
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Return with appropriate CSP for React Native app
        return HTMLResponse(
            content=content,
            headers={
                "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:;"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load app interface: {str(e)}")


@router.get("/{file_path:path}")
async def app_static_files(file_path: str):
    """Serve static files for the React Native app"""
    try:
        # Security: prevent directory traversal
        if '..' in file_path:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Construct the full path
        full_path = Path("static/app") / file_path
        
        # Check if file exists and is within the app directory
        if not full_path.exists() or not str(full_path.resolve()).startswith(str(Path("static/app").resolve())):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine the correct media type based on file extension
        media_type = None
        if file_path.endswith('.js'):
            media_type = 'application/javascript'
        elif file_path.endswith('.css'):
            media_type = 'text/css'
        elif file_path.endswith('.html'):
            media_type = 'text/html'
        elif file_path.endswith('.json'):
            media_type = 'application/json'
        elif file_path.endswith('.png'):
            media_type = 'image/png'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            media_type = 'image/jpeg'
        elif file_path.endswith('.ico'):
            media_type = 'image/x-icon'
        elif file_path.endswith('.ttf'):
            media_type = 'font/ttf'
        elif file_path.endswith('.woff'):
            media_type = 'font/woff'
        elif file_path.endswith('.woff2'):
            media_type = 'font/woff2'
        
        # Return the file with correct media type
        return FileResponse(full_path, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")