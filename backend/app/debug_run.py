"""
Debug runner for VS Code development.
Start the FastAPI server directly from VS Code for debugging.
"""

import uvicorn
from pathlib import Path
import sys

# Add project root to path for analytics imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("🚀 Starting FastAPI in debug mode...")
    print("📍 Available at: http://127.0.0.1:8000")
    print("📚 API docs at: http://127.0.0.1:8000/docs")
    print("🔧 Debug mode: Enabled")
    
    uvicorn.run(
        "backend.app.main:app",  # Import string format for reload
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )