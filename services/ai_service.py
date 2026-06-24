"""
Service IA Claude (Anthropic)
Chatbot intelligent pour analyse Amazon, négociation Alibaba, prévisions
"""

import anthropic
import os
import json
from typing import List, Dict, Optional

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Tu es SellerPro AI, un assistant expert en e-commerce Amazon et sourcing Alibaba.
Tu parles couramment français et anglais (tu t'adaptes à la langue de l'utilisateur).

Tes expertises :
- Analyse de compte vendeur Amazon (ventes, profits, stock, BSR, reviews)
- Stratégies de pricing et de Buy Box
- Recherche de produits (comme Jungle Scout / Helium 10)
- Analyse de concurrents
- Sourcing et négociation avec des fournisseurs Alibaba
- Prévisions de stock et de demande
- Optimisation de listings Amazon (titre, bullets, description, keywords)
- Calcul de marges et rentabilité FBA

Quand tu reçois des données du compte Amazon, analyse-les en profondeur et donne des recommandations concrètes et actionnables.

Pour les commandes Alibaba, tu peux :
- Rédiger des messages de négociation professionnels
- Calculer les quantités optimales à commander
- Évaluer les fournisseurs
- Gérer les conversations de négociation

Tu es direct, précis, et orienté résultats. Tu donnes toujours des chiffres concrets."""

async def chat_with_ai(
    messages: List[Dict],
    context_data: Optional[Dict] = None
) -> str:
    """
    Chat principal avec Claude IA
    context_data : données Amazon à analyser (optionnel)
    """
    system = SYSTEM_PROMPT

    if context_data:
        system += f"\n\nDONNÉES COMPTE AMAZON EN TEMPS RÉEL:\n{json.dumps(context_data, indent=2, ensure_ascii=False)}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=messages
    )

    return response.content[0].text


async def analyze_account(account_data: Dict) -> Dict:
    """Analyse complète du compte Amazon avec IA"""
    prompt = f"""Analyse complète de ce compte Amazon vendeur et donne-moi :

1. 📊 RÉSUMÉ EXÉCUTIF (3-4 points clés)
2. 💰 ANALYSE FINANCIÈRE (ventes, profits, tendances)
3. ⚠️ ALERTES CRITIQUES (problèmes urgents)
4. 🚀 TOP 3 OPPORTUNITÉS D'AMÉLIORATION
5. 📦 ÉTAT DU STOCK (risques de rupture)
6. 🎯 ACTIONS À FAIRE CETTE SEMAINE

Données du compte :
{json.dumps(account_data, indent=2, ensure_ascii=False)}

Réponds en français. Sois très précis avec les chiffres."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "analysis": response.content[0].text,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


async def analyze_product(product_data: Dict) -> Dict:
    """Analyse d'un produit spécifique avec recommandations"""
    prompt = f"""Analyse ce produit Amazon en profondeur :

DONNÉES PRODUIT :
{json.dumps(product_data, indent=2, ensure_ascii=False)}

Donne-moi :
1. 🏆 SCORE DE SANTÉ DU LISTING (0-100) avec explication
2. 📈 ANALYSE BSR ET TENDANCES
3. 💲 ANALYSE DES PRIX ET BUY BOX
4. ⭐ ANALYSE DES REVIEWS
5. 🔑 KEYWORDS MANQUANTS POTENTIELS
6. 📝 SUGGESTIONS D'AMÉLIORATION DU LISTING (titre, bullets, description)
7. 📦 RECOMMANDATION DE STOCK

Sois très spécifique et actionnable."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "analysis": response.content[0].text,
        "asin": product_data.get("asin", ""),
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


async def generate_alibaba_negotiation(
    product_name: str,
    target_price: float,
    quantity: int,
    supplier_name: str,
    negotiation_stage: str = "initial",
    previous_offer: float = None,
    language: str = "english"
) -> Dict:
    """
    Générer un message de négociation Alibaba avec IA
    negotiation_stage: 'initial', 'counter_offer', 'closing', 'quality_check'
    """
    stage_context = {
        "initial": "Premier contact avec le fournisseur. Sois professionnel, direct, et montre que tu es un acheteur sérieux.",
        "counter_offer": f"Le fournisseur a offert ${previous_offer}. Négocie pour descendre vers ${target_price}.",
        "closing": "On est proche d'un accord. Finalise les termes et conditions.",
        "quality_check": "Discute des standards de qualité, inspections, et certifications requises."
    }

    prompt = f"""Génère un message de négociation Alibaba professionnel.

CONTEXTE :
- Produit : {product_name}
- Fournisseur : {supplier_name}
- Prix cible : ${target_price} par unité
- Quantité : {quantity} unités
- Stade de négociation : {negotiation_stage}
- {stage_context.get(negotiation_stage, "")}

Génère en {language}. Le message doit être :
- Professionnel et respectueux (culture business chinoise)
- Clair sur les termes (prix, quantité, délais, qualité)
- Stratégique (ne pas montrer le prix maximum qu'on peut payer)
- Inclure les termes de paiement (30% dépôt, 70% avant expédition)
- Mentionner les exigences d'inspection (si pertinent)

Format: Message complet prêt à envoyer, sans explications."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "message": response.content[0].text,
        "stage": negotiation_stage,
        "product": product_name,
        "supplier": supplier_name,
        "target_price": target_price,
        "quantity": quantity
    }


async def predict_stock_needs(inventory_data: List[Dict], sales_data: Dict) -> Dict:
    """Prévision intelligente des besoins en stock"""
    prompt = f"""Analyse ces données de stock et ventes pour prédire les besoins futurs.

INVENTAIRE ACTUEL :
{json.dumps(inventory_data, indent=2, ensure_ascii=False)}

HISTORIQUE DES VENTES :
{json.dumps(sales_data, indent=2, ensure_ascii=False)}

Pour chaque produit, calcule et donne-moi :
1. 📅 DATE DE RUPTURE ESTIMÉE (si aucune commande)
2. 📦 QUANTITÉ À COMMANDER MAINTENANT
3. ⏰ DATE LIMITE POUR COMMANDER (délai fournisseur inclus)
4. 💰 INVESTISSEMENT ESTIMÉ POUR LE RÉAPPROVISIONNEMENT
5. 🚨 NIVEAU D'URGENCE (critique/élevé/moyen/faible)

Base-toi sur :
- Taux de vente actuel
- Tendances saisonnières
- Délai d'approvisionnement typique Alibaba vers FBA : 30-45 jours

Réponds en JSON structuré."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "predictions": response.content[0].text,
        "generated_at": __import__("datetime").datetime.now().isoformat()
    }


async def research_product_opportunity(
    keyword: str,
    category: str = None
) -> Dict:
    """Analyse d'opportunité produit (style Jungle Scout / Helium 10)"""
    prompt = f"""Analyse cette opportunité de produit Amazon comme un expert en product research.

MOT-CLÉ PRINCIPAL : {keyword}
CATÉGORIE : {category or "À déterminer"}

Fournis une analyse complète incluant :

1. 🎯 SCORE D'OPPORTUNITÉ (0-100)
2. 📊 ESTIMATION DE LA DEMANDE
   - Volume de recherche mensuel estimé
   - Tendance (croissante/stable/déclinante)
   - Saisonnalité
3. 💰 ANALYSE FINANCIÈRE ESTIMÉE
   - Prix de vente moyen sur Amazon
   - Coût d'approvisionnement estimé (Alibaba)
   - Marge brute estimée
   - ROI estimé
4. 🏆 ANALYSE DE LA COMPÉTITION
   - Niveau de compétition (faible/moyen/élevé)
   - Nombre de vendeurs estimé
   - Difficultés à entrer sur le marché
5. ⭐ PROFIL REVIEWS TYPIQUE
   - Nombre de reviews des top vendeurs
   - Note moyenne
6. 🚀 RECOMMANDATION FINALE
   - GO / NO GO / AVEC PRÉCAUTIONS
   - Raisons principales
7. 💡 STRATÉGIE D'ENTRÉE SUGGÉRÉE
   - Comment se différencier
   - Budget de lancement estimé

Base-toi sur tes connaissances du marché Amazon US."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "keyword": keyword,
        "category": category,
        "research": response.content[0].text,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


async def analyze_competitor(competitor_data: Dict) -> Dict:
    """Analyse approfondie d'un concurrent"""
    prompt = f"""Analyse ce concurrent Amazon en profondeur et donne-moi une stratégie pour le battre.

DONNÉES CONCURRENT :
{json.dumps(competitor_data, indent=2, ensure_ascii=False)}

Analyse :
1. 🔍 POINTS FORTS DU CONCURRENT
2. ⚡ FAIBLESSES ET VULNÉRABILITÉS
3. 💲 STRATÉGIE DE PRIX
4. ⭐ ANALYSE DES REVIEWS (points de douleur des clients)
5. 🎯 COMMENT LES BATTRE
   - Sur le prix
   - Sur la qualité
   - Sur le listing
   - Sur les reviews
6. 🚨 ALERTES (si ils deviennent out of stock, baissent leur prix, etc.)
7. 📋 PLAN D'ACTION CONCRET

Sois stratégique et direct."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "analysis": response.content[0].text,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


async def generate_weekly_report(account_data: Dict) -> str:
    """Générer le rapport hebdomadaire automatique"""
    prompt = f"""Génère un rapport hebdomadaire professionnel pour ce compte Amazon vendeur.

DONNÉES DE LA SEMAINE :
{json.dumps(account_data, indent=2, ensure_ascii=False)}

Format du rapport :
# 📊 RAPPORT HEBDOMADAIRE SELLERPRO
## Semaine du [date]

### 💰 PERFORMANCE FINANCIÈRE
### 📦 ÉTAT DES STOCKS
### 🏆 TOP PRODUITS
### ⚠️ ALERTES & PROBLÈMES
### 📈 TENDANCES
### 🎯 ACTIONS DE LA SEMAINE PROCHAINE

Sois précis avec les chiffres. Compare avec la semaine précédente si les données sont disponibles."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text
