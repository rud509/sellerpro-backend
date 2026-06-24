"""Routes Produits"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.database_service import save_product, get_products, get_product_by_asin
from services.database_service import save_price_history, get_price_history

router = APIRouter()

class ProductModel(BaseModel):
    asin: str
    name: str
    sku: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    target_stock: Optional[int] = 100
    notes: Optional[str] = None

@router.get("/")
async def list_products():
    try:
        products = await get_products()
        return {"success": True, "data": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_product(product: ProductModel):
    try:
        saved = await save_product(product.dict())
        return {"success": True, "data": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{asin}")
async def get_product(asin: str):
    try:
        product = await get_product_by_asin(asin)
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        return {"success": True, "data": product}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{asin}/price-history")
async def price_history(asin: str, days: int = 90):
    try:
        history = await get_price_history(asin, days)
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{asin}/price-history")
async def add_price_history(asin: str, price_data: dict):
    try:
        saved = await save_price_history(asin, price_data)
        return {"success": True, "data": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
