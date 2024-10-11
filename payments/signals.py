# payments/signals.py
from django.dispatch import receiver
from store.signals import order_created
from .models import Payment
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

@receiver(order_created)
def create_payment_for_order(sender, **kwargs):
    order = kwargs['order']

    # Check if a payment already exists for this order
    # if Payment.objects.filter(order=order).exists():
    #     print(f"Payment already exists for Order {order.id}")
    #     return  # Exit the signal handler if a payment already exists

    # Calculate the total amount
    amount = sum(item.unit_price * item.quantity for item in order.items.all())

    # Create a payment record in the database
    payment = Payment.objects.create(
        order=order,
        amount=amount,
        status=Payment.PENDING,
        payment_method='stripe'
    )

    # Create a Stripe PaymentIntent
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe expects amount in cents
            currency='pkr',
            metadata={'order_id': order.id},
        )
        payment.payment_id = intent['id']
        payment.save()

        print(f"Payment {payment.payment_id} created for Order {order.id}")

    except stripe.error.StripeError as e:
        # Handle errors and update payment status to failed
        payment.status = Payment.FAILED
        payment.save()
        print(f"Stripe error: {e}")
