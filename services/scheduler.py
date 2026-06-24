"""
Scheduler - Tâches automatiques en arrière-plan
Surveille stock, prix, concurrents toutes les X heures
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from services.amazon_service import amazon_api
from services.notification_service import notification_service
from services.database_service import (
    save_price_history, get_competitors, save_daily_snapshot,
    get_sales, save_notification
)
from services.ai_service import predict_stock_needs, generate_weekly_report
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
EXPO_TOKEN = os.getenv("EXPO_PUSH_TOKEN", "")

scheduler = AsyncIOScheduler()

# ==================== TÂCHES AUTOMATIQUES ====================

async def check_inventory_levels():
    """Vérifier les niveaux de stock toutes les 2 heures"""
    try:
        logger.info("⏰ Vérification des niveaux de stock...")
        low_stock_items = await amazon_api.get_low_stock_items(threshold=15)

        for item in low_stock_items:
            await notification_service.notify_low_stock(EXPO_TOKEN, item)
            
            # Calculer les jours avant rupture (estimation)
            qty = item.get("quantity", 0)
            # Estimation basée sur 5 ventes/jour (sera affiné avec vraies données)
            days_until_oos = max(1, qty // 5)
            
            if days_until_oos <= 30:  # Moins de 30 jours → commande urgente
                await notification_service.notify_reorder_needed(
                    EXPO_TOKEN, item, days_until_oos
                )

        logger.info(f"✅ {len(low_stock_items)} produits en stock bas détectés")

    except Exception as e:
        logger.error(f"❌ Erreur check_inventory_levels: {e}")


async def check_new_orders():
    """Vérifier les nouvelles commandes toutes les 15 minutes"""
    try:
        logger.info("⏰ Vérification des nouvelles commandes...")
        orders = await amazon_api.get_orders(days_back=1, status="Unshipped")
        
        orders_list = orders.get("payload", {}).get("Orders", [])
        
        for order in orders_list:
            order_id = order.get("AmazonOrderId", "")
            amount = float(order.get("OrderTotal", {}).get("Amount", 0))
            
            await notification_service.notify_new_sale(EXPO_TOKEN, {
                "order_id": order_id,
                "product_name": "Commande Amazon",
                "amount": amount,
                "quantity": 1
            })

        logger.info(f"✅ {len(orders_list)} nouvelles commandes")

    except Exception as e:
        logger.error(f"❌ Erreur check_new_orders: {e}")


async def monitor_competitors():
    """Surveiller les concurrents toutes les 4 heures"""
    try:
        logger.info("⏰ Surveillance des concurrents...")
        competitors = await get_competitors()
        
        for competitor in competitors:
            asin = competitor.get("asin")
            if not asin:
                continue
                
            try:
                # Vérifier le prix actuel
                pricing = await amazon_api.get_competitive_pricing([asin])
                
                # Sauvegarder l'historique
                await save_price_history(asin, {
                    "price": competitor.get("last_price"),
                    "buy_box_price": competitor.get("buy_box_price"),
                    "bsr": competitor.get("bsr")
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur surveillance concurrent {asin}: {e}")

        logger.info(f"✅ {len(competitors)} concurrents surveillés")

    except Exception as e:
        logger.error(f"❌ Erreur monitor_competitors: {e}")


async def save_daily_analytics():
    """Sauvegarder les analytics quotidiens (minuit)"""
    try:
        logger.info("⏰ Sauvegarde des analytics quotidiens...")
        
        sales_summary = await amazon_api.get_sales_summary(days_back=1)
        inventory = await amazon_api.get_inventory()
        
        await save_daily_snapshot({
            "date": datetime.now().date().isoformat(),
            "total_sales": sales_summary.get("total_sales", 0),
            "total_orders": sales_summary.get("orders_count", 0),
            "net_revenue": sales_summary.get("net_revenue", 0),
            "total_fees": sales_summary.get("total_fees", 0),
            "total_refunds": sales_summary.get("total_refunds", 0),
        })

        logger.info("✅ Analytics quotidiens sauvegardés")

    except Exception as e:
        logger.error(f"❌ Erreur save_daily_analytics: {e}")


async def send_weekly_report():
    """Envoyer le rapport hebdomadaire (lundi 8h)"""
    try:
        logger.info("⏰ Génération du rapport hebdomadaire...")
        
        sales_data = await amazon_api.get_sales_summary(days_back=7)
        inventory = await amazon_api.get_low_stock_items(threshold=20)
        
        report = await generate_weekly_report({
            "sales": sales_data,
            "inventory_alerts": inventory,
            "period": "7 derniers jours"
        })

        # Notification push avec le résumé
        await notification_service.send_push_notification(
            EXPO_TOKEN,
            "📊 Rapport Hebdomadaire Disponible",
            f"Ventes: ${sales_data.get('total_sales', 0):.2f} | Commandes: {sales_data.get('orders_count', 0)}",
            {"type": "weekly_report", "screen": "Analytics"}
        )

        await save_notification({
            "type": "weekly_report",
            "title": "📊 Rapport Hebdomadaire",
            "message": report[:500] + "...",
            "data": {"full_report": report},
            "priority": "normal"
        })

        logger.info("✅ Rapport hebdomadaire envoyé")

    except Exception as e:
        logger.error(f"❌ Erreur send_weekly_report: {e}")


def start_scheduler():
    """Démarrer toutes les tâches planifiées"""
    
    # Vérifier les nouvelles commandes toutes les 15 minutes
    scheduler.add_job(
        check_new_orders,
        IntervalTrigger(minutes=15),
        id="check_orders",
        replace_existing=True
    )

    # Vérifier le stock toutes les 2 heures
    scheduler.add_job(
        check_inventory_levels,
        IntervalTrigger(hours=2),
        id="check_inventory",
        replace_existing=True
    )

    # Surveiller les concurrents toutes les 4 heures
    scheduler.add_job(
        monitor_competitors,
        IntervalTrigger(hours=4),
        id="monitor_competitors",
        replace_existing=True
    )

    # Analytics quotidiens à minuit
    scheduler.add_job(
        save_daily_analytics,
        CronTrigger(hour=0, minute=0),
        id="daily_analytics",
        replace_existing=True
    )

    # Rapport hebdomadaire le lundi à 8h
    scheduler.add_job(
        send_weekly_report,
        CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_report",
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Scheduler démarré avec 5 tâches automatiques")
    return scheduler
