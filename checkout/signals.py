from .models import Order
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import TopSeller
from django.core.cache import cache
@receiver(pre_save, sender=Order)
def update_top_sellers_on_order_completion(sender, instance, **kwargs):
    """Update top sellers when order status changes to delivered"""
    if instance.pk:  # Only for existing orders
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != 'delivered' and instance.status == 'delivered':
                # Order was just marked as delivered - update top sellers
                for item in instance.items.all():
                    top_seller, created = TopSeller.objects.get_or_create(
                        product=item.product,
                        defaults={'sales_count': 0, 'is_active': True}
                    )
                    top_seller.sales_count += item.quantity
                    top_seller.save()
                    # Clear cache
                    cache.delete_many([f'top_sellers_{i}' for i in range(5, 50, 5)])
        except Order.DoesNotExist:
            pass