"""
Service de Notifications Push (Expo)
Envoie des notifications en temps réel sur le téléphone
"""

import httpx
import os
from typing import List, Dict, Optional
from services.database_service import save_notification, get_notifications

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

class NotificationService:

    async def send_push_notification(
        self,
        expo_token: str,
        title: str,
        body: str,
        data: Dict = None,
        sound: str = "default",
        badge: int = None
    ) -> Dict:
        """Envoyer une notification push via Expo"""
        payload = {
            "to": expo_token,
            "title": title,
            "body": body,
            "sound": sound,
            "data": data or {},
            "priority": "high"
        }
        if badge is not None:
            payload["badge"] = badge

        async with httpx.AsyncClient() as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.getenv('EXPO_ACCESS_TOKEN', '')}"
                }
            )

        return response.json()

    async def notify_new_sale(self, expo_token: str, order_data: Dict):
        """🛒 Notification d'une nouvelle vente"""
        product_name = order_data.get("product_name", "Produit")
        amount = order_data.get("amount", 0)
        quantity = order_data.get("quantity", 1)

        title = "🛒 Nouvelle Vente !"
        body = f"{product_name} x{quantity} — ${amount:.2f}"

        await self.send_push_notification(expo_token, title, body, {
            "type": "new_sale",
            "order_id": order_data.get("order_id"),
            "screen": "Orders"
        })

        await save_notification({
            "type": "sale",
            "title": title,
            "message": body,
            "data": order_data,
            "priority": "normal"
        })

    async def notify_low_stock(self, expo_token: str, product: Dict):
        """⚠️ Notification de stock bas"""
        name = product.get("name", "Produit")
        qty = product.get("quantity", 0)
        level = product.get("alert_level", "warning")

        if level == "critical":
            title = "🚨 STOCK CRITIQUE !"
            body = f"{name} — Il ne reste que {qty} unité(s) !"
        else:
            title = "⚠️ Stock Bas"
            body = f"{name} — {qty} unités restantes. Commandez maintenant !"

        await self.send_push_notification(expo_token, title, body, {
            "type": "low_stock",
            "asin": product.get("asin"),
            "quantity": qty,
            "screen": "Inventory"
        })

        await save_notification({
            "type": "low_stock",
            "title": title,
            "message": body,
            "data": product,
            "priority": "high" if level == "critical" else "normal"
        })

    async def notify_competitor_out_of_stock(self, expo_token: str, competitor: Dict):
        """🎯 Notification : concurrent en rupture de stock"""
        name = competitor.get("name", "Un concurrent")
        asin = competitor.get("asin", "")

        title = "🎯 Opportunité ! Concurrent en rupture !"
        body = f"{name} est OUT OF STOCK ! C'est le moment d'augmenter ton prix ou tes PPC."

        await self.send_push_notification(expo_token, title, body, {
            "type": "competitor_oos",
            "asin": asin,
            "screen": "Competitors"
        })

        await save_notification({
            "type": "competitor_oos",
            "title": title,
            "message": body,
            "data": competitor,
            "priority": "high"
        })

    async def notify_price_change(self, expo_token: str, product: Dict, old_price: float, new_price: float):
        """💲 Notification de changement de prix (le tien ou concurrent)"""
        change = ((new_price - old_price) / old_price) * 100
        direction = "📈 hausse" if new_price > old_price else "📉 baisse"

        title = f"💲 Changement de Prix"
        body = f"{product.get('name', 'Produit')} : {direction} de {abs(change):.1f}% (${old_price:.2f} → ${new_price:.2f})"

        await self.send_push_notification(expo_token, title, body, {
            "type": "price_change",
            "asin": product.get("asin"),
            "old_price": old_price,
            "new_price": new_price,
            "screen": "Products"
        })

        await save_notification({
            "type": "price_change",
            "title": title,
            "message": body,
            "data": {**product, "old_price": old_price, "new_price": new_price},
            "priority": "normal"
        })

    async def notify_return(self, expo_token: str, return_data: Dict):
        """↩️ Notification d'un retour"""
        product_name = return_data.get("product_name", "Produit")
        reason = return_data.get("reason", "Raison inconnue")

        title = "↩️ Retour Client"
        body = f"{product_name} — {reason}"

        await self.send_push_notification(expo_token, title, body, {
            "type": "return",
            "order_id": return_data.get("order_id"),
            "screen": "Orders"
        })

        await save_notification({
            "type": "return",
            "title": title,
            "message": body,
            "data": return_data,
            "priority": "normal"
        })

    async def notify_reorder_needed(self, expo_token: str, product: Dict, days_until_oos: int):
        """📦 Notification : il faut commander maintenant"""
        name = product.get("name", "Produit")

        title = "📦 Commandez Maintenant !"
        body = f"{name} — Rupture estimée dans {days_until_oos} jours. Commandez chez votre fournisseur !"

        await self.send_push_notification(expo_token, title, body, {
            "type": "reorder",
            "asin": product.get("asin"),
            "days_until_oos": days_until_oos,
            "screen": "Inventory"
        })

        await save_notification({
            "type": "reorder",
            "title": title,
            "message": body,
            "data": product,
            "priority": "high"
        })

    async def notify_buy_box_lost(self, expo_token: str, product: Dict):
        """🏆 Notification : perte de la Buy Box"""
        name = product.get("name", "Produit")

        title = "🏆 Buy Box Perdue !"
        body = f"{name} — Tu n'as plus la Buy Box. Vérifie ton prix et ta performance."

        await self.send_push_notification(expo_token, title, body, {
            "type": "buy_box_lost",
            "asin": product.get("asin"),
            "screen": "Products"
        })

        await save_notification({
            "type": "buy_box_lost",
            "title": title,
            "message": body,
            "data": product,
            "priority": "high"
        })

    async def notify_new_review(self, expo_token: str, review_data: Dict):
        """⭐ Notification d'une nouvelle review"""
        rating = review_data.get("rating", 0)
        product = review_data.get("product_name", "Produit")
        emoji = "⭐" if rating >= 4 else "😡" if rating <= 2 else "😐"

        title = f"{emoji} Nouvelle Review {rating}/5"
        body = f"{product} — {review_data.get('title', '')[:50]}"

        await self.send_push_notification(expo_token, title, body, {
            "type": "new_review",
            "asin": review_data.get("asin"),
            "rating": rating,
            "screen": "Products"
        })

        await save_notification({
            "type": "review",
            "title": title,
            "message": body,
            "data": review_data,
            "priority": "high" if rating <= 2 else "normal"
        })


notification_service = NotificationService()
