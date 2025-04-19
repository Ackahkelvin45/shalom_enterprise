from django.shortcuts import render
from  products.models import Cart

# Create your views here.


def get_cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    
    # Calculate totals
    cart_subtotal = sum(item.total_price for item in cart_items)
    total_savings = sum(item.total_discount for item in cart_items)
    cart_total = cart_subtotal - total_savings
    
    context = {
        "products": cart_items,
        "cart_subtotal": cart_subtotal,
        "total_savings": total_savings,
        "cart_total": cart_total
    }
    return render(request, "cart/cartpage.html", context)