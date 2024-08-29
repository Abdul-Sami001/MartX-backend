from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe
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
