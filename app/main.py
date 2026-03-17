# app/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routes.prediction_routes import router as prediction_router
from app.routes.auth_routes import router as auth_router

# Database
from app.db.mongodb import db


# Create uploads folder if it doesn't exist
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Initialize FastAPI app
app = FastAPI(
    title="AyurPulse Skin Detection API",
    version="1.0",
    description="AI-powered dermatology and Ayurvedic recommendation system"
)


# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠ Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- ROUTES ---------------- #

# Prediction API
app.include_router(
    prediction_router,
    prefix="/api",
    tags=["Prediction"]
)

# Authentication API
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)


# ---------------- HEALTH ENDPOINTS ---------------- #

@app.get("/", tags=["Health"])
def home():
    return {"message": "AyurPulse API is running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


@app.get("/test-db", tags=["Database"])
def test_db():
    try:
        collections = db.list_collection_names()

        return {
            "message": "MongoDB connected successfully",
            "collections": collections
        }

    except Exception as e:
        return {"error": str(e)}