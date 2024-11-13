# app/utils/stripe_service.py
from stripe.error import StripeError
import stripe
from app.utils.config import settings
from app.utils.logging_config import setup_logging
from datetime import datetime

logger = setup_logging()


class StripeService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_payment_intent(self, amount: int, currency: str, metadata: dict):
        """Create a payment intent for the specified amount"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,  # Amount in cents
                currency=currency,
                metadata=metadata,
                automatic_payment_methods={"enabled": True},
            )
            return intent
        except StripeError as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise

    async def verify_webhook_signature(self, payload: bytes, sig_header: str):
        """Verify that the webhook came from Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except Exception as e:
            logger.error(f"Error verifying webhook: {str(e)}")
            raise
