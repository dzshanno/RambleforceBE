from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.utils.auth import get_current_active_user
from app.database.models import Payment, Order, Registration, User
from app.utils.stripe_service import StripeService
from app.utils.logging_config import setup_logging
from app.schemas.payment import PaymentCreate, PaymentResponse
from typing import Optional

# Set up logging
logger = setup_logging()

router = APIRouter()
stripe_service = StripeService()


@router.post("/create-payment-intent", response_model=PaymentResponse)
async def create_payment_intent(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a payment intent for either event registration or merchandise order"""
    try:
        # Validate the order or registration exists and belongs to the user
        if payment.order_id:
            order = (
                db.query(Order)
                .filter(Order.id == payment.order_id, Order.user_id == current_user.id)
                .first()
            )
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            amount = int(order.total_amount * 100)  # Convert to cents
            metadata = {"order_id": str(order.id)}
        elif payment.registration_id:
            registration = (
                db.query(Registration)
                .filter(
                    Registration.id == payment.registration_id,
                    Registration.user_id == current_user.id,
                )
                .first()
            )
            if not registration:
                raise HTTPException(status_code=404, detail="Registration not found")
            event = registration.event
            amount = int(event.price * 100)  # Convert to cents
            metadata = {"registration_id": str(registration.id)}
        else:
            raise HTTPException(
                status_code=400,
                detail="Either order_id or registration_id must be provided",
            )

        # Create payment intent with Stripe
        intent = await stripe_service.create_payment_intent(
            amount=amount, currency="gbp", metadata=metadata
        )

        # Create payment record in database
        payment_db = Payment(
            stripe_payment_intent_id=intent.id,
            amount=amount,
            currency="gbp",
            status="pending",
            payment_type="merchandise" if payment.order_id else "event_registration",
            user_id=current_user.id,
            order_id=payment.order_id,
            registration_id=payment.registration_id,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )
        db.add(payment_db)
        db.commit()
        db.refresh(payment_db)

        return {"client_secret": intent.client_secret, "payment_id": payment_db.id}

    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    try:
        # Get the webhook payload and signature header
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        # Verify webhook signature
        event = await stripe_service.verify_webhook_signature(payload, sig_header)

        # Handle the event
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            # Update payment status in database
            payment = (
                db.query(Payment)
                .filter(Payment.stripe_payment_intent_id == payment_intent.id)
                .first()
            )

            if payment:
                payment.status = "succeeded"
                if payment.order_id:
                    order = db.query(Order).get(payment.order_id)
                    if order:
                        order.status = "paid"
                elif payment.registration_id:
                    registration = db.query(Registration).get(payment.registration_id)
                    if registration:
                        registration.payment_status = "paid"
                        registration.status = "registered"

                db.commit()

        return Response(status_code=200)

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
