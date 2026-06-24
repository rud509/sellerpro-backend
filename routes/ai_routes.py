"""
Routes IA Claude
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.ai_service import (
    chat_with_ai, analyze_account, analyze_product,
    generate_alibaba_negotiation, predict_stock_needs,
    research_product_opportunity, analyze_competitor, generate_weekly_report
)
from services.amazon_service import amazon_api
from services.database_service import save_chat_message, get_chat_history

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: str
    include_amazon_data: bool = False

class ProductResearchRequest(BaseModel):
    keyword: str
    category: Optional[str] = None

class NegotiationRequest(BaseModel):
    product_name: str
    target_price: float
    quantity: int
    supplier_name: str
    negotiation_stage: str = "initial"
    previous_offer: Optional[float] = None
    language: str = "english"

class CompetitorAnalysisRequest(BaseModel):
    asin: str
    competitor_name: Optional[str] = None


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        context_data = None
        if request.include_amazon_data:
            try:
                sales = await amazon_api.get_sales_summary(days_back=30)
                inventory = await amazon_api.get_low_stock_items(threshold=20)
                context_data = {
                    "sales_summary": sales,
                    "low_stock_items": inventory[:5]
                }
            except:
                pass

        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        response = await chat_with_ai(messages, context_data)

        # Sauvegarder dans l'historique
        last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
        if last_user_msg:
            await save_chat_message({
                "session_id": request.session_id,
                "role": "user",
                "content": last_user_msg["content"]
            })
        await save_chat_message({
            "session_id": request.session_id,
            "role": "assistant",
            "content": response
        })

        return {"success": True, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    try:
        history = await get_chat_history(session_id, limit)
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/account")
async def analyze_my_account(days: int = 30):
    try:
        sales = await amazon_api.get_sales_summary(days_back=days)
        inventory = await amazon_api.get_low_stock_items(threshold=20)
        orders = await amazon_api.get_orders(days_back=days)

        account_data = {
            "sales_summary": sales,
            "low_stock_items": inventory,
            "recent_orders_count": len(orders.get("payload", {}).get("Orders", [])),
            "period_days": days
        }

        analysis = await analyze_account(account_data)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/product/{asin}")
async def analyze_my_product(asin: str):
    try:
        product = await amazon_api.get_catalog_item(asin)
        pricing = await amazon_api.get_buy_box_price(asin)
        bsr = await amazon_api.get_sales_rank(asin)
        competitive = await amazon_api.get_competitive_pricing([asin])

        product_data = {
            "asin": asin,
            "catalog": product,
            "buy_box": pricing,
            "bsr": bsr,
            "competitive_pricing": competitive
        }

        analysis = await analyze_product(product_data)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/product")
async def research_product(request: ProductResearchRequest):
    try:
        research = await research_product_opportunity(request.keyword, request.category)
        return {"success": True, "data": research}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/negotiate/alibaba")
async def negotiate_alibaba(request: NegotiationRequest):
    try:
        message = await generate_alibaba_negotiation(
            product_name=request.product_name,
            target_price=request.target_price,
            quantity=request.quantity,
            supplier_name=request.supplier_name,
            negotiation_stage=request.negotiation_stage,
            previous_offer=request.previous_offer,
            language=request.language
        )
        return {"success": True, "data": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/competitor")
async def analyze_competitor_route(request: CompetitorAnalysisRequest):
    try:
        product = await amazon_api.get_catalog_item(request.asin)
        pricing = await amazon_api.get_buy_box_price(request.asin)
        bsr = await amazon_api.get_sales_rank(request.asin)

        competitor_data = {
            "asin": request.asin,
            "name": request.competitor_name or "Concurrent",
            "catalog": product,
            "pricing": pricing,
            "bsr": bsr
        }

        analysis = await analyze_competitor(competitor_data)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/stock")
async def predict_stock():
    try:
        inventory = await amazon_api.get_inventory()
        sales_data = await amazon_api.get_sales_summary(days_back=30)

        inventory_list = inventory.get("payload", {}).get("inventorySummaries", [])
        simplified = [
            {
                "asin": item.get("asin"),
                "sku": item.get("sellerSku"),
                "name": item.get("productName", ""),
                "quantity": item.get("inventoryDetails", {}).get("fulfillableQuantity", 0)
            }
            for item in inventory_list
        ]

        predictions = await predict_stock_needs(simplified, sales_data)
        return {"success": True, "data": predictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/weekly")
async def weekly_report():
    try:
        sales = await amazon_api.get_sales_summary(days_back=7)
        inventory_alerts = await amazon_api.get_low_stock_items(threshold=20)
        orders = await amazon_api.get_orders(days_back=7)

        account_data = {
            "sales": sales,
            "inventory_alerts": inventory_alerts,
            "orders_count": len(orders.get("payload", {}).get("Orders", [])),
            "period": "7 derniers jours"
        }

        report = await generate_weekly_report(account_data)
        return {"success": True, "data": {"report": report}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
