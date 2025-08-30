#!/usr/bin/env python3
"""
Smart Supply Chain API Server
Run this script to start the FastAPI server
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def main():
    try:
        import uvicorn
        from main import app
        
        # Get configuration from environment
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", 8000))
        
        print(f"🚀 Starting Smart Supply Chain API...")
        print(f"📍 Server will be available at http://{host}:{port}")
        print(f"📚 API Documentation at http://{host}:{port}/docs")
        print(f"🔄 ReDoc Documentation at http://{host}:{port}/redoc")
        
        # Check if MongoDB connection is configured
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("⚠  Warning: MONGO_URI not found in environment variables")
            print("   Make sure to create a .env file with MongoDB configuration")
        
        # Run the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=True,  # Enable auto-reload during development
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__== "__main__":
    main()