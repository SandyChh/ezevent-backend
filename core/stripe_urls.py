from django.urls import path
from .stripe_webhook import stripe_webhook

urlpatterns = [
    path("webhook/", stripe_webhook, name="stripe-webhook"),
]
