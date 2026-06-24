"""Routes Concurrents"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.database_service import save_competitor, get_competitors
from services.amazon_service import amazon_api
router = APIRouter()

class CompetitorModel(BaseModel):
    asin: str
    name: str
    competing_with_asin: Optional[str] = None
    notes: Optional[str] = None

@router.get("/")
async def list_competitors(my_asin: Optional[str] = None):
    try:
        data = await get_competitors(my_asin=my_asin)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def add_competitor(comp: CompetitorModel):
    try:
        # Récupérer les données Amazon du concurrent
        try:
            pricing = await amazon_api.get_buy_box_price(comp.asin)
            bsr = await amazon_api.get_sales_rank(comp.asin)
            comp_data = {
                **comp.dict(),
                "last_price": pricing.get("buy_box_price"),
                "buy_box_price": pricing.get("buy_box_price"),
                "bsr": bsr[0].get("rank") if bsr else None
            }
        except:
            comp_data = comp.dict()
        
        saved = await save_competitor(comp_data)
        return {"success": True, "data": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{asin}/live")
async def get_competitor_live(asin: str):
    try:
        pricing = await amazon_api.get_competitive_pricing([asin])
        buy_box = await amazon_api.get_buy_box_price(asin)
        bsr = await amazon_api.get_sales_rank(asin)
        return {"success": True, "data": {
            "asin": asin,
            "competitive_pricing": pricing,
            "buy_box": buy_box,
            "bsr": bsr
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
