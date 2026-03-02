"""
Stripe billing integration for freemium model.

Free tier: 5 total resume scores
Pro tier: $12/month unlimited scoring
Ultra tier: $29/month unlimited scoring + AI resume rewriting

Supports:
- Checkout session creation (redirect to Stripe-hosted payment page)
- Webhook handling for subscription lifecycle events
- Subscription status checking
"""

import os
from typing import Optional, Dict, Any

from cloud.config import settings

# Try to import stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False


def _init_stripe():
    if STRIPE_AVAILABLE and settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return True
    return False


def is_billing_configured() -> bool:
    """Check if Stripe is properly configured."""
    return (
        STRIPE_AVAILABLE
        and bool(settings.STRIPE_SECRET_KEY)
        and bool(settings.STRIPE_PRICE_ID)
    )


def create_checkout_session(
    user_id: int,
    email: str,
    tier: str = "pro",
    success_url: str = "https://resume-scorer-web.streamlit.app",
    cancel_url: str = "https://resume-scorer-web.streamlit.app",
) -> Optional[Dict[str, Any]]:
    """
    Create a Stripe Checkout session for Pro or Ultra subscription.

    Returns dict with checkout_url, or None if Stripe not configured.
    """
    if not _init_stripe():
        return None

    if tier == "ultra" and settings.STRIPE_PRICE_ID_ULTRA:
        price_id = settings.STRIPE_PRICE_ID_ULTRA
    else:
        price_id = settings.STRIPE_PRICE_ID

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={"user_id": str(user_id), "tier": tier},
        )
        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }
    except stripe.StripeError as e:
        return {"error": str(e)}


def handle_webhook_event(payload: bytes, sig_header: str) -> Dict[str, Any]:
    """
    Process a Stripe webhook event.

    Returns action dict: {"action": "upgrade"|"downgrade"|"none", "user_id": int, ...}
    """
    if not _init_stripe():
        return {"action": "none", "error": "Stripe not configured"}

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        return {"action": "none", "error": f"Webhook verification failed: {e}"}

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        metadata = data.get("metadata", {})
        user_id = int(metadata.get("user_id", 0))
        tier = metadata.get("tier", "pro")  # "pro" or "ultra"
        customer_id = data.get("customer", "")
        subscription_id = data.get("subscription", "")
        return {
            "action": "upgrade",
            "user_id": user_id,
            "tier": tier,
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": subscription_id,
        }

    elif event_type in (
        "customer.subscription.deleted",
        "customer.subscription.updated",
    ):
        subscription = data
        status = subscription.get("status", "")
        customer_id = subscription.get("customer", "")

        if status in ("canceled", "unpaid", "past_due"):
            return {
                "action": "downgrade",
                "stripe_customer_id": customer_id,
                "tier": "free",
                "reason": status,
            }

    return {"action": "none", "event_type": event_type}


def get_subscription_status(stripe_customer_id: str) -> Optional[Dict[str, Any]]:
    """Check current subscription status for a Stripe customer."""
    if not _init_stripe() or not stripe_customer_id:
        return None

    try:
        subscriptions = stripe.Subscription.list(
            customer=stripe_customer_id, status="active", limit=1
        )
        if subscriptions.data:
            sub = subscriptions.data[0]
            return {
                "status": sub.status,
                "current_period_end": sub.current_period_end,
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        return {"status": "inactive"}
    except stripe.StripeError:
        return None


def create_portal_session(stripe_customer_id: str, return_url: str = "https://resume-scorer-web.streamlit.app") -> Optional[str]:
    """Create a Stripe Customer Portal session for managing subscriptions."""
    if not _init_stripe() or not stripe_customer_id:
        return None

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )
        return session.url
    except stripe.StripeError:
        return None
