from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .core.config import settings
from .core.logging import logger
from .core.dependencies import get_db
from .api import auth, taxpayer

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(taxpayer.router, prefix="/api/v1/taxpayer", tags=["Taxpayer Profile"])

@app.get("/api/v1/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error(f"Health check DB error: {str(e)}")
        # If DB is down, return 503 Service Unavailable
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up MaaV Solutions Phase-1 API...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MaaV Solutions Phase-1 API...")
