"""
Routes Amazon SP-API
"""
from fastapi import APIRouter, HTTPException, Query
from services.amazon_service import amazon_api
from services.database_service import save_sale, get_sales
from typing import Optional, List

router = APIRouter()

@router.get("/orders")
async def get_orders(days: int = 7, status: Optional[str] = None):
    try:
        orders = await amazon_api.get_orders(days_back=days, status=status)
        return {"success": True, "data": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    try:
        order = await amazon_api.get_order_details(order_id)
        items = await amazon_api.get_order_items(order_id)
        return {"success": True, "order": order, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory")
async def get_inventory():
    try:
        inventory = await amazon_api.get_inventory()
        return {"success": True, "data": inventory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/low-stock")
async def get_low_stock(threshold: int = 15):
    try:
        items = await amazon_api.get_low_stock_items(threshold=threshold)
        return {"success": True, "data": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{asin}")
async def get_product(asin: str):
    try:
        product = await amazon_api.get_catalog_item(asin)
        pricing = await amazon_api.get_buy_box_price(asin)
        ranks = await amazon_api.get_sales_rank(asin)
        return {"success": True, "product": product, "pricing": pricing, "bsr": ranks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/search")
async def search_products(keywords: str, category: Optional[str] = None):
    try:
        results = await amazon_api.search_catalog(keywords, category)
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing/{asin}/buybox")
async def get_buybox(asin: str):
    try:
        data = await amazon_api.get_buy_box_price(asin)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing/competitive")
async def get_competitive_pricing(asins: str):
    try:
        asin_list = [a.strip() for a in asins.split(",")]
        data = await amazon_api.get_competitive_pricing(asin_list)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/summary")
async def get_finances(days: int = 30):
    try:
        data = await amazon_api.get_sales_summary(days_back=days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/finances/events")
async def get_financial_events(days: int = 30):
    try:
        data = await amazon_api.get_financial_events(days_back=days)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
