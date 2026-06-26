"""
SellerPro - Backend Principal (FastAPI)
Amazon US Seller App avec IA Claude
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="SellerPro API",
    description="Backend pour l'application Amazon Seller avec IA",
    version="1.0.0"
)

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import des routes
from routes.amazon_routes import router as amazon_router
from routes.ai_routes import router as ai_router
from routes.products_routes import router as products_router
from routes.notifications_routes import router as notifications_router
from routes.alibaba_routes import router as alibaba_router
from routes.analytics_routes import router as analytics_router
from routes.competitor_routes import router as competitor_router

app.include_router(amazon_router, prefix="/api/amazon", tags=["Amazon SP-API"])
app.include_router(ai_router, prefix="/api/ai", tags=["IA Claude"])
app.include_router(products_router, prefix="/api/products", tags=["Produits"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(alibaba_router, prefix="/api/alibaba", tags=["Alibaba"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(competitor_router, prefix="/api/competitors", tags=["Concurrents"])

@app.get("/")
async def root():
    return {
        "status": "✅ SellerPro API en ligne",
        "version": "1.0.0",
        "message": "Backend Amazon Seller avec IA Claude"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SellerPro Backend"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
