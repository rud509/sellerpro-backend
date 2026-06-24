"""Routes Analytics"""
from fastapi import APIRouter, HTTPException
from services.database_service import get_analytics_history, save_daily_snapshot
from services.amazon_service import amazon_api
router = APIRouter()

@router.get("/history")
async def analytics_history(days: int = 30):
    try:
        data = await get_analytics_history(days=days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pnl")
async def profit_and_loss(days: int = 30):
    try:
        summary = await amazon_api.get_sales_summary(days_back=days)
        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fba-calculator")
async def fba_calculator(
    selling_price: float,
    cost_price: float,
    weight_lbs: float = 1.0,
    category: str = "standard"
):
    """Calculateur FBA - calcule la marge nette"""
    try:
        # Frais Amazon FBA approximatifs
        referral_fee = selling_price * 0.15  # 15% frais de référencement
        
        # Frais fulfillment FBA par taille/poids
        if weight_lbs <= 1:
            fulfillment_fee = 3.22
        elif weight_lbs <= 2:
            fulfillment_fee = 4.56
        elif weight_lbs <= 3:
            fulfillment_fee = 5.42
        else:
            fulfillment_fee = 5.42 + ((weight_lbs - 3) * 0.38)

        storage_fee = 0.75  # estimation mensuelle
        total_fees = referral_fee + fulfillment_fee + storage_fee
        gross_profit = selling_price - cost_price - total_fees
        margin_percent = (gross_profit / selling_price) * 100
        roi = (gross_profit / cost_price) * 100

        return {
            "success": True,
            "data": {
                "selling_price": selling_price,
                "cost_price": cost_price,
                "referral_fee": round(referral_fee, 2),
                "fulfillment_fee": round(fulfillment_fee, 2),
                "storage_fee": round(storage_fee, 2),
                "total_fees": round(total_fees, 2),
                "gross_profit": round(gross_profit, 2),
                "margin_percent": round(margin_percent, 1),
                "roi_percent": round(roi, 1),
                "break_even_price": round(cost_price + total_fees, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
