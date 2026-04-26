# ============================================================
# CareerLens – Premium / Payment Router
# File: backend/routers/premium.py
# Placeholder integration for Stripe / Razorpay
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from middleware.auth import get_authenticated_user
from database import supabase
from config import settings
import logging, uuid

logger = logging.getLogger("careerlens.premium")
router = APIRouter()


class InitiatePaymentRequest(BaseModel):
    provider: str = "stripe"   # stripe | razorpay
    plan: str = "premium"


@router.post("/initiate")
async def initiate_payment(body: InitiatePaymentRequest, user=Depends(get_authenticated_user)):
    """
    Placeholder: Initiate a payment session.
    Replace with real Stripe/Razorpay SDK calls when ready.
    """
    payment_id = str(uuid.uuid4())
    supabase.table("payment_records").insert({
        "id": payment_id,
        "user_id": user["user_id"],
        "provider": body.provider,
        "amount": 500,   # $5.00 in cents
        "currency": "USD",
        "status": "pending",
        "plan_type": "premium",
    }).execute()

    # TODO: Replace with actual Stripe PaymentIntent or Razorpay order creation
    return {
        "success": True,
        "payment_id": payment_id,
        "message": "Payment initiation placeholder. Integrate Stripe/Razorpay SDK here.",
        "stripe_key": settings.STRIPE_SECRET_KEY[:8] + "..." if settings.STRIPE_SECRET_KEY else "not configured",
    }


@router.post("/webhook")
async def payment_webhook(payload: dict):
    """
    Placeholder: Handle payment provider webhook.
    Verify signature, update payment record, upgrade user plan.
    """
    # TODO: Verify webhook signature (Stripe: stripe.Webhook.construct_event)
    event_type = payload.get("type", "")
    logger.info(f"Received webhook event: {event_type}")

    if event_type == "payment_intent.succeeded":
        user_id = payload.get("metadata", {}).get("user_id")
        if user_id:
            supabase.rpc("upgrade_user_to_premium", {"p_user_id": user_id}).execute()

    return {"received": True}


@router.get("/plans")
async def get_plans():
    """Return freemium vs premium plan comparison."""
    return {
        "success": True,
        "plans": {
            "freemium": {
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "features": {
                    "resume_analyses": 1,
                    "mock_interviews": 1,
                    "chatbot_messages": 20,
                    "ats_checker": False,
                    "cover_letter": False,
                    "skill_gap": False,
                    "portfolio_gen": 4,
                    "job_match": False,
                    "github_analyzer": False,
                    "ai_mentor": False,
                },
            },
            "premium": {
                "name": "Premium",
                "price": 500,
                "currency": "USD",
                "billing": "monthly",
                "features": {
                    "resume_analyses": "unlimited",
                    "mock_interviews": "unlimited",
                    "chatbot_messages": "unlimited",
                    "ats_checker": True,
                    "cover_letter": True,
                    "skill_gap": True,
                    "portfolio_gen": True,
                    "job_match": True,
                    "github_analyzer": True,
                    "ai_mentor": True,
                },
            },
        },
    }

