import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.api import (
    auth_router,
    uploads_router,
    transactions_router,
    budgets_router,
    dashboard_router,
    insights_router,
    forecast_router,
    advisor_router,
    accounts_router,
    system_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("finance_agent")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Deterministic Multi-Agent Personal Finance Intelligence Engine & Grounded Conversational Advisor",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https?://.*" if settings.ENVIRONMENT == "production" or os.getenv("VERCEL") else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API Routers (direct mount)
api_routers = [
    auth_router,
    uploads_router,
    transactions_router,
    budgets_router,
    dashboard_router,
    insights_router,
    forecast_router,
    advisor_router,
    accounts_router,
    system_router,
]

for router in api_routers:
    app.include_router(router)
    # Also support /api prefix for reverse proxies, dev proxies, and Vercel services rewrites
    app.include_router(router, prefix="/api")

@app.on_event("startup")
def on_startup():
    logger.info("Starting up Personal Finance Agent API...")
    try:
        # Auto-create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized.")
        
        # Auto-seed demo environment if empty
        from app.bootstrap import seed_database
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Startup bootstrap exception: {e}", exc_info=True)

@app.get("/")
@app.get("/api")
@app.get("/api/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "RUNNING",
        "docs": "/docs",
        "health": "/health/ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
