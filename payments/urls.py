from django.urls import path
from .views import stripe_webhook, create_payment_intent

urlpatterns = [
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    path('create-payment-intent/', create_payment_intent, name='create-payment-intent'),
]
