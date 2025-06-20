from django.db import models
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from authentication.models import CustomUser
from django.utils import timezone
from products.models import Product
from authentication.models import ShippingAddress

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    CANCELLATION_REASONS = [
        ('changed_mind', 'Changed my mind'),
        ('found_cheaper', 'Found cheaper elsewhere'),
        ('shipping_time', 'Shipping takes too long'),
        ('other', 'Other reason'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT, related_name='orders', null=True)
    contact_phone = models.CharField(max_length=20,null=True,blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, default='cash_on_delivery')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancellation_reason = models.CharField(
        max_length=50, 
        choices=CANCELLATION_REASONS, 
        blank=True, 
        null=True
    )
    cancellation_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed']

    def __str__(self):
        return f"Order #{self.order_number} by {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{self.user.id}-{Order.objects.count() + 1}"
        super().save(*args, **kwargs)

    def send_status_notification(self):
        """Send email notification when status changes to shipped or delivered"""
        if self.status in ['shipped', 'delivered']:
            subject = f"Your Order #{self.order_number} has been {self.status}"
            
            context = {
                'order': self,
                'status': self.get_status_display(),
                'user': self.user,
            }
            
            message = render_to_string('emails/order_status_update.txt', context)
            html_message = render_to_string('emails/order_status_update.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False,
            )


@receiver(pre_save, sender=Order)
def order_status_change_handler(sender, instance, **kwargs):
    """Signal handler to detect status changes and send notifications"""
    if instance.pk:  # Only for existing orders
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != instance.status:  # Status changed
                instance.send_status_notification()
        except Order.DoesNotExist:
            pass


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.order_number}"

    @property
    def total_price(self):
        if self.discount_price:
            return self.discount_price * self.quantity
        return self.price * self.quantity