from fastapi import FastAPI
from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Microservicio Community Service: usuarios, clubes, membresías y autenticación.",
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
