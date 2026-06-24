"""Routes Notifications"""
from fastapi import APIRouter, HTTPException
from services.database_service import get_notifications, mark_notification_read
router = APIRouter()

@router.get("/")
async def list_notifications(unread_only: bool = False, limit: int = 50):
    try:
        notifs = await get_notifications(limit=limit, unread_only=unread_only)
        return {"success": True, "data": notifs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notif_id}/read")
async def read_notification(notif_id: str):
    try:
        await mark_notification_read(notif_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
