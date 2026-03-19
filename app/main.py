from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import settings
from app.routes.prediction_routes import router as prediction_router
from app.routes.auth_routes import router as auth_router
from app.routes.plan_routes import router as plan_router
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.db.mongodb import connect_db, disconnect_db


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AyurPulse — AI-powered skin condition detection + Ayurvedic treatment.\n\n"
            "**Feature 1:** Upload image → AI detects skin condition → saved to your history\n"
            "**Feature 2:** Register / Login / Logout with JWT auth\n"
            "**Feature 3:** Fill profile form → get personalized 7-day Ayurvedic plan\n"
            "**Feature 4:** Tick daily tasks + rate your skin → track 7-day progress\n\n"
            "**How to use protected endpoints:**\n"
            "1. Login via `/api/v1/auth/login` → copy `access_token`\n"
            "2. Click **Authorize** → paste token → Authorize → Close\n"
            "3. All protected endpoints now work automatically."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Swagger Bearer token ───────────────────────────────────────────────────
    # Only these routes work WITHOUT login
    PUBLIC_ROUTES = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/health",
        "/api/v1/plan/conditions",
        "/",
    }

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema.setdefault("components", {})
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Paste your access_token from /login. Do NOT include 'Bearer' prefix."
            }
        }
        for path, methods in schema.get("paths", {}).items():
            if path not in PUBLIC_ROUTES:
                for method in methods.values():
                    method["security"] = [{"BearerAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router)
    app.include_router(prediction_router)
    app.include_router(plan_router)

    # ── Root ──────────────────────────────────────────────────────────────────
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "app":     settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status":  "running",
            "docs":    "http://127.0.0.1:8000/docs",
            "endpoints": {
                "register":          "POST /api/v1/auth/register",
                "login":             "POST /api/v1/auth/login",
                "logout":            "POST /api/v1/auth/logout",
                "refresh":           "POST /api/v1/auth/refresh",
                "me":                "GET  /api/v1/auth/me",
                "predict":           "POST /api/v1/predict",
                "predict_history":   "GET  /api/v1/predict/history",
                "health":            "GET  /api/v1/health",
                "plan_generate":     "POST /api/v1/plan/generate",
                "plan_my_plan":      "GET  /api/v1/plan/my-plan",
                "plan_checkin":      "POST /api/v1/plan/checkin",
                "plan_progress":     "GET  /api/v1/plan/progress/{plan_id}",
                "plan_conditions":   "GET  /api/v1/plan/conditions",
            }
        }

    # ── Startup / Shutdown ────────────────────────────────────────────────────
    @app.on_event("startup")
    async def startup():
        await connect_db()
        print(f"[AyurPulse] Server running → http://127.0.0.1:8000/docs")

    @app.on_event("shutdown")
    async def shutdown():
        await disconnect_db()

    return app


app = create_app()