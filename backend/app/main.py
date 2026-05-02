from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .core.config import settings
from .core.logging import logger
from .core.dependencies import get_db
from .core.exception_handlers import register_exception_handlers
from .api import auth, taxpayer, business, financials, compliance, itr, filing, consent

app_configs = {}
if settings.APP_ENV in ["staging", "production"]:
    app_configs["openapi_url"] = None # Blinds Swagger UI & Redoc
    app_configs["docs_url"] = None
    app_configs["redoc_url"] = None

app = FastAPI(
    title=settings.PROJECT_NAME,
    **app_configs
)

# Register CORS Middleware EARLY as the outermost boundary
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=[],
    max_age=600,
)

register_exception_handlers(app)

app.include_router(auth, prefix="/api/v1/auth", tags=["auth"])
app.include_router(taxpayer, prefix="/api/v1/taxpayer", tags=["Taxpayer Profile"])
app.include_router(business, prefix="/api/v1/business", tags=["Business Profile"])
app.include_router(financials, prefix="/api/v1/financial", tags=["Financial Ledger"])
app.include_router(compliance, prefix="/api/v1/compliance", tags=["Compliance Engine"])
app.include_router(itr, prefix="/api/v1/itr", tags=["ITR Determination"])
app.include_router(filing, prefix="/api/v1/filing", tags=["Filing Case Workflow"])
app.include_router(consent, prefix="/api/v1/consent", tags=["CA Assignment & Consent"])

@app.get("/api/v1/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint. Uninformative in production.
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        
        # Obfuscate output if deployed
        if settings.APP_ENV in ["staging", "production"]:
            return {"status": "ok"}
            
        return {"status": "ok", "db": "connected"}
        
    except Exception as e:
        logger.error(f"Health check DB error: {str(e)}")
        # If DB is down, return 503 Service Unavailable blind footprint
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable" if settings.APP_ENV in ["staging", "production"] else f"Database connection failed: {e}"
        )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up MaaV Solutions Phase-1 API...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MaaV Solutions Phase-1 API...")
