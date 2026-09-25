# ============================================================
# CareerLens – Premium / Payment Router
# File: backend/routers/premium.py
# Placeholder integration for Stripe / Razorpay
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from middleware.auth import get_authenticated_user
from database import supabase
from config import settings
import logging, uuid
import stripe

logger = logging.getLogger("careerlens.premium")
router = APIRouter()


class InitiatePaymentRequest(BaseModel):
    provider: str = "stripe"   # stripe | razorpay
    plan: str = "premium"


@router.post("/initiate")
async def initiate_payment(body: InitiatePaymentRequest, user=Depends(get_authenticated_user)):
    """
    Create a real Stripe PaymentIntent for Premium upgrade.
    Returns the client_secret so the frontend can confirm payment via Stripe.js.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payment service is not configured.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        intent = stripe.PaymentIntent.create(
            amount=500,        # $5.00 in cents — matches /plans pricing
            currency="usd",
            metadata={
                "user_id": user["user_id"],
                "plan_type": "premium",
            },
            description="CareerLens Premium Monthly Subscription",
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe PaymentIntent creation failed for user {user['user_id']}: {e}")
        raise HTTPException(status_code=502, detail="Payment service error. Please try again.")

    # Persist payment record for audit trail
    payment_id = intent.id
    try:
        supabase.table("payment_records").insert({
            "id": payment_id,
            "user_id": user["user_id"],
            "provider": "stripe",
            "amount": 500,
            "currency": "USD",
            "status": "pending",
            "plan_type": "premium",
        }).execute()
    except Exception as e:
        logger.warning(f"Could not persist payment record {payment_id}: {e}")

    return {
        "success": True,
        "payment_id": payment_id,
        "client_secret": intent.client_secret,
    }


@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Handle Stripe payment webhooks.
    Verify signature before updating payment records or upgrading plans.
    """
    body = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            body,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event.get("type", "")
    logger.info(f"Received webhook event: {event_type}")

    if event_type == "payment_intent.succeeded":
        payment_intent = event.get("data", {}).get("object", {})
        user_id = payment_intent.get("metadata", {}).get("user_id")
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
                    "resume_analyses": settings.FREEMIUM_MAX_ANALYSES,
                    "mock_interviews": settings.FREEMIUM_MAX_INTERVIEWS,
                    "chatbot_messages": settings.FREEMIUM_MAX_CHATBOT_MSGS,
                    "ats_checker": False,
                    "cover_letter": False,
                    "skill_gap": False,
                    "portfolio_gen": settings.FREEMIUM_MAX_PORTFOLIO_GENS,
                    "interview_probability": settings.FREEMIUM_MAX_INTERVIEW_PROBABILITY,
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
                    "interview_probability": "unlimited",
                    "job_match": True,
                    "github_analyzer": True,
                    "ai_mentor": True,
                },
            },
        },
    }

