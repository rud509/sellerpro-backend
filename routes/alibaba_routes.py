"""Routes Alibaba"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.database_service import save_negotiation, get_negotiations, update_negotiation
router = APIRouter()

class NegotiationModel(BaseModel):
    product_name: str
    supplier_name: str
    supplier_url: Optional[str] = None
    target_price: float
    quantity: int
    notes: Optional[str] = None

@router.get("/negotiations")
async def list_negotiations(status: Optional[str] = None):
    try:
        data = await get_negotiations(status=status)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/negotiations")
async def create_negotiation(neg: NegotiationModel):
    try:
        saved = await save_negotiation(neg.dict())
        return {"success": True, "data": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/negotiations/{neg_id}")
async def update_neg(neg_id: str, update: dict):
    try:
        updated = await update_negotiation(neg_id, update)
        return {"success": True, "data": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
