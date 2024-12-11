from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.utils import json

from store.models import Order
from .models import Payment
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        payment = Payment.objects.get(payment_id=payment_intent['id'])
        payment.status = Payment.COMPLETED
        payment.save()
        payment.order.payment_status = 'completed'
        payment.order.save()

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        payment = Payment.objects.get(payment_id=payment_intent['id'])
        payment.status = Payment.FAILED
        payment.save()
        payment.order.payment_status = 'failed'
        payment.order.save()

    return JsonResponse({'status': 'success'}, status=200)


@csrf_exempt
@api_view(['POST'])
def create_payment_intent(request):
    try:
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the order and calculate total amount
        order = Order.objects.get(id=order_id)
        total_amount = order.calculate_total_amount() * 100  # Convert to cents for Stripe

        # Create a PaymentIntent with Stripe
        print(stripe.api_key)
        intent = stripe.PaymentIntent.create(
            amount=int(total_amount),  # Amount in cents
            currency='usd',
            metadata={'order_id': order_id}
        )


        return Response({
            'clientSecret': intent['client_secret']
        })
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
