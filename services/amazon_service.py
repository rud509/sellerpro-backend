"""
Service Amazon SP-API
Gère toutes les connexions avec Amazon Seller Central
"""

import httpx
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json

class AmazonSPAPI:
    def __init__(self):
        self.client_id = os.getenv("AMAZON_CLIENT_ID")
        self.client_secret = os.getenv("AMAZON_CLIENT_SECRET")
        self.refresh_token = os.getenv("AMAZON_REFRESH_TOKEN")
        self.marketplace_id = os.getenv("AMAZON_MARKETPLACE_ID", "ATVPDKIKX0DER")
        self.access_token = None
        self.token_expiry = None
        self.base_url = "https://sellingpartnerapi-na.amazon.com"
        self.lwa_url = "https://api.amazon.com/auth/o2/token"

    async def get_access_token(self) -> str:
        """Obtenir ou renouveler le token d'accès Amazon"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.lwa_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        if response.status_code != 200:
            raise Exception(f"Erreur token Amazon: {response.text}")

        data = response.json()
        self.access_token = data["access_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        return self.access_token

    async def _make_request(self, method: str, endpoint: str, params: dict = None, body: dict = None):
        """Faire une requête authentifiée à l'API Amazon"""
        token = await self.get_access_token()
        headers = {
            "x-amz-access-token": token,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=headers,
                params=params,
                json=body,
                timeout=30.0
            )

        if response.status_code not in [200, 201]:
            raise Exception(f"Erreur API Amazon {response.status_code}: {response.text}")

        return response.json()

    # ==================== COMMANDES ====================

    async def get_orders(self, days_back: int = 7, status: str = None) -> Dict:
        """Récupérer les commandes récentes"""
        created_after = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {
            "MarketplaceIds": self.marketplace_id,
            "CreatedAfter": created_after,
        }
        if status:
            params["OrderStatuses"] = status

        return await self._make_request("GET", "/orders/v0/orders", params=params)

    async def get_order_details(self, order_id: str) -> Dict:
        """Détails d'une commande spécifique"""
        return await self._make_request("GET", f"/orders/v0/orders/{order_id}")

    async def get_order_items(self, order_id: str) -> Dict:
        """Items d'une commande"""
        return await self._make_request("GET", f"/orders/v0/orders/{order_id}/orderItems")

    # ==================== INVENTAIRE ====================

    async def get_inventory(self) -> Dict:
        """Récupérer l'inventaire FBA complet"""
        params = {
            "details": True,
            "marketplaceId": self.marketplace_id,
        }
        return await self._make_request(
            "GET",
            "/fba/inventory/v1/summaries",
            params={
                "details": "true",
                "granularityType": "Marketplace",
                "granularityId": self.marketplace_id,
                "marketplaceIds": self.marketplace_id
            }
        )

    async def get_low_stock_items(self, threshold: int = 10) -> List[Dict]:
        """Récupérer les produits en stock bas"""
        inventory = await self.get_inventory()
        low_stock = []

        summaries = inventory.get("payload", {}).get("inventorySummaries", [])
        for item in summaries:
            qty = item.get("inventoryDetails", {}).get("fulfillableQuantity", 0)
            if qty <= threshold:
                low_stock.append({
                    "asin": item.get("asin"),
                    "sku": item.get("sellerSku"),
                    "name": item.get("productName", "Produit inconnu"),
                    "quantity": qty,
                    "alert_level": "critical" if qty <= 3 else "warning"
                })

        return low_stock

    # ==================== PRODUITS & CATALOGUE ====================

    async def get_catalog_item(self, asin: str) -> Dict:
        """Obtenir les détails d'un produit par ASIN"""
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "attributes,images,productTypes,salesRanks,summaries"
        }
        return await self._make_request("GET", f"/catalog/2022-04-01/items/{asin}", params=params)

    async def search_catalog(self, keywords: str, category: str = None) -> Dict:
        """Rechercher des produits dans le catalogue Amazon"""
        params = {
            "keywords": keywords,
            "marketplaceIds": self.marketplace_id,
            "includedData": "attributes,images,salesRanks,summaries"
        }
        if category:
            params["productType"] = category

        return await self._make_request("GET", "/catalog/2022-04-01/items", params=params)

    # ==================== PRICING ====================

    async def get_competitive_pricing(self, asins: List[str]) -> Dict:
        """Obtenir les prix compétitifs pour une liste d'ASINs"""
        params = {
            "MarketplaceId": self.marketplace_id,
            "Asins": ",".join(asins),
            "ItemType": "Asin"
        }
        return await self._make_request("GET", "/products/pricing/v0/competitivePrice", params=params)

    async def get_my_price(self, asins: List[str]) -> Dict:
        """Obtenir mes propres prix"""
        params = {
            "MarketplaceId": self.marketplace_id,
            "Asins": ",".join(asins),
            "ItemType": "Asin"
        }
        return await self._make_request("GET", "/products/pricing/v0/price", params=params)

    async def get_buy_box_price(self, asin: str) -> Dict:
        """Obtenir le prix Buy Box pour un ASIN"""
        pricing = await self.get_competitive_pricing([asin])
        try:
            offers = pricing["payload"][0]["Product"]["CompetitivePricing"]["CompetitivePrices"]
            buy_box = next((p for p in offers if p["competitivePriceId"] == "1"), None)
            if buy_box:
                return {
                    "asin": asin,
                    "buy_box_price": buy_box["Price"]["LandedPrice"]["Amount"],
                    "currency": buy_box["Price"]["LandedPrice"]["CurrencyCode"]
                }
        except (KeyError, IndexError, StopIteration):
            pass
        return {"asin": asin, "buy_box_price": None}

    # ==================== FINANCES ====================

    async def get_financial_events(self, days_back: int = 30) -> Dict:
        """Récupérer les événements financiers (ventes, frais, remboursements)"""
        posted_after = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return await self._make_request(
            "GET",
            "/finances/v0/financialEvents",
            params={"PostedAfter": posted_after}
        )

    async def get_sales_summary(self, days_back: int = 30) -> Dict:
        """Résumé des ventes avec calcul de profit"""
        events = await self.get_financial_events(days_back)
        
        total_sales = 0
        total_fees = 0
        total_refunds = 0
        orders_count = 0

        financial_events = events.get("payload", {}).get("FinancialEvents", {})
        
        # Ventes
        for order in financial_events.get("ShipmentEventList", []):
            for item in order.get("ShipmentItemList", []):
                for charge in item.get("ItemChargeList", []):
                    if charge["ChargeType"] == "Principal":
                        total_sales += float(charge["ChargeAmount"]["CurrencyAmount"])
                        orders_count += 1
                for fee in item.get("ItemFeeList", []):
                    total_fees += abs(float(fee["FeeAmount"]["CurrencyAmount"]))

        # Remboursements
        for refund in financial_events.get("RefundEventList", []):
            for item in refund.get("ShipmentItemAdjustmentList", []):
                for charge in item.get("ItemChargeAdjustmentList", []):
                    total_refunds += abs(float(charge["ChargeAmount"]["CurrencyAmount"]))

        return {
            "period_days": days_back,
            "total_sales": round(total_sales, 2),
            "total_fees": round(total_fees, 2),
            "total_refunds": round(total_refunds, 2),
            "net_revenue": round(total_sales - total_fees - total_refunds, 2),
            "orders_count": orders_count,
            "average_order_value": round(total_sales / orders_count, 2) if orders_count > 0 else 0
        }

    # ==================== REVIEWS & FEEDBACK ====================

    async def get_product_reviews_count(self, asin: str) -> Dict:
        """Obtenir le nombre de reviews d'un produit"""
        catalog = await self.get_catalog_item(asin)
        try:
            summaries = catalog.get("summaries", [{}])[0]
            return {
                "asin": asin,
                "rating": summaries.get("browseClassification", {}).get("rating"),
                "review_count": summaries.get("browseClassification", {}).get("numberOfReviews", 0)
            }
        except (KeyError, IndexError):
            return {"asin": asin, "rating": None, "review_count": 0}

    # ==================== BSR (Best Seller Rank) ====================

    async def get_sales_rank(self, asin: str) -> List[Dict]:
        """Obtenir le BSR d'un produit"""
        catalog = await self.get_catalog_item(asin)
        try:
            ranks = catalog.get("salesRanks", [{}])[0].get("ranks", [])
            return [
                {
                    "category": r.get("title", ""),
                    "rank": r.get("value", 0),
                    "link": r.get("link", "")
                }
                for r in ranks
            ]
        except (KeyError, IndexError):
            return []

    # ==================== RAPPORTS ====================

    async def request_report(self, report_type: str, days_back: int = 30) -> str:
        """Demander un rapport Amazon"""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        body = {
            "reportType": report_type,
            "marketplaceIds": [self.marketplace_id],
            "dataStartTime": start_date,
        }
        response = await self._make_request("POST", "/reports/2021-06-30/reports", body=body)
        return response.get("reportId")

    async def get_report_status(self, report_id: str) -> Dict:
        """Vérifier le statut d'un rapport"""
        return await self._make_request("GET", f"/reports/2021-06-30/reports/{report_id}")


# Instance globale
amazon_api = AmazonSPAPI()
