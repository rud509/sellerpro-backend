"""
Service Supabase - Base de données
Gère toutes les opérations de base de données
"""

from supabase import create_client, Client
import os
from datetime import datetime
from typing import Dict, List, Optional

def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

# ==================== PRODUITS ====================

async def save_product(product_data: Dict) -> Dict:
    """Sauvegarder ou mettre à jour un produit"""
    supabase = get_supabase()
    result = supabase.table("products").upsert(
        {**product_data, "updated_at": datetime.now().isoformat()},
        on_conflict="asin"
    ).execute()
    return result.data[0] if result.data else {}

async def get_products(limit: int = 50) -> List[Dict]:
    """Récupérer tous les produits"""
    supabase = get_supabase()
    result = supabase.table("products").select("*").order("updated_at", desc=True).limit(limit).execute()
    return result.data

async def get_product_by_asin(asin: str) -> Optional[Dict]:
    """Récupérer un produit par ASIN"""
    supabase = get_supabase()
    result = supabase.table("products").select("*").eq("asin", asin).execute()
    return result.data[0] if result.data else None

# ==================== HISTORIQUE PRIX (KEEPA CLONE) ====================

async def save_price_history(asin: str, price_data: Dict) -> Dict:
    """Sauvegarder l'historique des prix"""
    supabase = get_supabase()
    result = supabase.table("price_history").insert({
        "asin": asin,
        "price": price_data.get("price"),
        "buy_box_price": price_data.get("buy_box_price"),
        "bsr": price_data.get("bsr"),
        "review_count": price_data.get("review_count"),
        "rating": price_data.get("rating"),
        "recorded_at": datetime.now().isoformat()
    }).execute()
    return result.data[0] if result.data else {}

async def get_price_history(asin: str, days: int = 90) -> List[Dict]:
    """Récupérer l'historique des prix (graphique Keepa)"""
    supabase = get_supabase()
    from datetime import timedelta
    since = (datetime.now() - timedelta(days=days)).isoformat()
    result = (supabase.table("price_history")
              .select("*")
              .eq("asin", asin)
              .gte("recorded_at", since)
              .order("recorded_at")
              .execute())
    return result.data

# ==================== VENTES ====================

async def save_sale(sale_data: Dict) -> Dict:
    """Sauvegarder une vente"""
    supabase = get_supabase()
    result = supabase.table("sales").upsert(
        {**sale_data, "created_at": datetime.now().isoformat()},
        on_conflict="order_id"
    ).execute()
    return result.data[0] if result.data else {}

async def get_sales(days: int = 30, asin: str = None) -> List[Dict]:
    """Récupérer les ventes"""
    supabase = get_supabase()
    from datetime import timedelta
    since = (datetime.now() - timedelta(days=days)).isoformat()
    query = supabase.table("sales").select("*").gte("created_at", since)
    if asin:
        query = query.eq("asin", asin)
    result = query.order("created_at", desc=True).execute()
    return result.data

# ==================== CONCURRENTS ====================

async def save_competitor(competitor_data: Dict) -> Dict:
    """Sauvegarder un concurrent"""
    supabase = get_supabase()
    result = supabase.table("competitors").upsert(
        {**competitor_data, "updated_at": datetime.now().isoformat()},
        on_conflict="asin"
    ).execute()
    return result.data[0] if result.data else {}

async def get_competitors(my_asin: str = None) -> List[Dict]:
    """Récupérer les concurrents"""
    supabase = get_supabase()
    query = supabase.table("competitors").select("*")
    if my_asin:
        query = query.eq("competing_with_asin", my_asin)
    result = query.order("updated_at", desc=True).execute()
    return result.data

# ==================== NOTIFICATIONS ====================

async def save_notification(notif_data: Dict) -> Dict:
    """Sauvegarder une notification"""
    supabase = get_supabase()
    result = supabase.table("notifications").insert({
        **notif_data,
        "created_at": datetime.now().isoformat(),
        "read": False
    }).execute()
    return result.data[0] if result.data else {}

async def get_notifications(limit: int = 50, unread_only: bool = False) -> List[Dict]:
    """Récupérer les notifications"""
    supabase = get_supabase()
    query = supabase.table("notifications").select("*")
    if unread_only:
        query = query.eq("read", False)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data

async def mark_notification_read(notif_id: str) -> bool:
    """Marquer une notification comme lue"""
    supabase = get_supabase()
    supabase.table("notifications").update({"read": True}).eq("id", notif_id).execute()
    return True

# ==================== ALIBABA / NÉGOCIATIONS ====================

async def save_negotiation(negotiation_data: Dict) -> Dict:
    """Sauvegarder une négociation Alibaba"""
    supabase = get_supabase()
    result = supabase.table("negotiations").insert({
        **negotiation_data,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }).execute()
    return result.data[0] if result.data else {}

async def get_negotiations(status: str = None) -> List[Dict]:
    """Récupérer les négociations"""
    supabase = get_supabase()
    query = supabase.table("negotiations").select("*")
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return result.data

async def update_negotiation(negotiation_id: str, update_data: Dict) -> Dict:
    """Mettre à jour une négociation"""
    supabase = get_supabase()
    result = (supabase.table("negotiations")
              .update({**update_data, "updated_at": datetime.now().isoformat()})
              .eq("id", negotiation_id)
              .execute())
    return result.data[0] if result.data else {}

# ==================== CHAT HISTORY ====================

async def save_chat_message(message_data: Dict) -> Dict:
    """Sauvegarder un message de chat"""
    supabase = get_supabase()
    result = supabase.table("chat_history").insert({
        **message_data,
        "created_at": datetime.now().isoformat()
    }).execute()
    return result.data[0] if result.data else {}

async def get_chat_history(session_id: str, limit: int = 50) -> List[Dict]:
    """Récupérer l'historique du chat"""
    supabase = get_supabase()
    result = (supabase.table("chat_history")
              .select("*")
              .eq("session_id", session_id)
              .order("created_at")
              .limit(limit)
              .execute())
    return result.data

# ==================== ANALYTICS ====================

async def save_daily_snapshot(snapshot_data: Dict) -> Dict:
    """Sauvegarder un snapshot quotidien"""
    supabase = get_supabase()
    result = supabase.table("daily_snapshots").upsert(
        {**snapshot_data, "date": datetime.now().date().isoformat()},
        on_conflict="date"
    ).execute()
    return result.data[0] if result.data else {}

async def get_analytics_history(days: int = 30) -> List[Dict]:
    """Récupérer l'historique analytics"""
    supabase = get_supabase()
    from datetime import timedelta
    since = (datetime.now() - timedelta(days=days)).date().isoformat()
    result = (supabase.table("daily_snapshots")
              .select("*")
              .gte("date", since)
              .order("date")
              .execute())
    return result.data
async def get_chat_history():
    try:
        supabase = get_supabase()
        result = supabase.table("chat_history")\
            .select("session_id, role, content, created_at")\
            .order("created_at", desc=True)\
            .execute()
        
        sessions = {}
        for row in result.data:
            sid = row["session_id"]
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "last_message": row["content"],
                    "last_message_at": row["created_at"],
                    "message_count": 0
                }
            sessions[sid]["message_count"] += 1
        
        return list(sessions.values())
    except Exception as e:
        raise Exception(f"Erreur historique: {str(e)}")
