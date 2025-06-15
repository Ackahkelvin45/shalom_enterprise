# config/dashboard.py
from django.contrib.auth import get_user_model
from django.conf import settings
from products.models import Product

def dashboard_callback(request, context):
    print("!!! Dashboard callback executing !!!")  # Debug output
    
    active_users = get_user_model().objects.filter(is_active=True).count()
    active_products = Product.objects.filter(is_active=True).count()
    
    stats = {
        "active_users": {
            "value": active_users,
            "label": "Active Users",
            "icon": "people",
        },
        "active_products": {
            "value": active_products,
            "label": "Active Products",
            "icon": "inventory_2",
        },
    }
    
    print("!!! Stats generated:", stats)  # Debug output
    context.update({"custom_stats": stats})
    return context