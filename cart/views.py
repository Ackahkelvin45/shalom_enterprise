from django.shortcuts import render, redirect
from django.contrib import messages
from products.models import Cart
from django.views.decorators.http import require_POST

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

@require_POST
def remove_from_cart(request, product_id):
    cart_item = Cart.objects.get(user=request.user, product_id=product_id)
    cart_item.delete()
    messages.success(request, "Product removed from cart.")
    return redirect("cart:cartproducts")


@require_POST
def update_cart(request, product_id):
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            messages.error(request, "Quantity must be at least 1.")
            return redirect("cart:cartproducts")
            
        cart_item = Cart.objects.get(user=request.user, product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated successfully.")
    except Cart.DoesNotExist:
        messages.error(request, "Product not found in your cart.")
    except ValueError:
        messages.error(request, "Invalid quantity.")
    
    return redirect("cart:cartproducts")  # This redirect will refresh the page and recalculate totals





