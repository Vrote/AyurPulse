# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.prediction_routes import router
from app.db.mongodb import db

# Create uploads folder if it doesn't exist
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="AyurPulse Skin Detection API",
    version="1.0",
    description="API for skin disease detection using deep learning"
)

# CORS settings (allow all origins for now; restrict in production as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Replace "*" with allowed frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api", tags=["Prediction"])

# Root endpoint
@app.get("/", tags=["Health"])
def home():
    return {"message": "AyurPulse API is running"}

# Health check endpoint
@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

@app.get("/test-db")
def test_db():
    try:
        collections = db.list_collection_names()
        return {
            "message": "MongoDB connected successfully",
            "collections": collections
        }
    except Exception as e:
        return {"error": str(e)}