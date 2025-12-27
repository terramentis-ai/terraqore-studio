from fastapi import FastAPI
import uvicorn
from core.frontend_api import setup_frontend_api
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file (force reload)
load_dotenv(override=True)

def create_app() -> FastAPI:
    app = FastAPI(title="Flynt Studio Backend")
    
    # Enable CORS for frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount the frontend API routes
    setup_frontend_api(app)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("backend_main:app", host="0.0.0.0", port=8000, reload=True)
