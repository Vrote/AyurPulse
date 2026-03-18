import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,   # auto-restart when you edit code (dev mode)
        log_level="info"
    )