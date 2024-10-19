from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.dispatch import receiver
from store.signals import order_created

@receiver(order_created)
def on_order_created(sender, **kwargs):
    order = kwargs['order']
    customer_email = order.customer.user.email

    # Prepare email content
    subject = f'Order Confirmation - Order #{order.id}'
    html_message = render_to_string('emails/order_confirmation.html', {'order': order})
    plain_message = strip_tags(html_message)
    from_email = 'Martx.com'
    to_email = customer_email

    # Send the email
    send_mail(
        subject,
        plain_message,
        from_email,
        [to_email],
        html_message=html_message,
    )
