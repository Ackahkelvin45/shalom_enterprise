from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib import messages
from .models import Order, OrderItem 
from authentication.models import ShippingAddress
from  products.models import Cart
from django.utils import timezone
import random
import string
from django.conf import settings
import logging
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from .forms import OrderCancellationForm

def confirm_order(request):
   
        # Get cart items
        cart_items = Cart.objects.filter(user=request.user).select_related('product')
        
        if not cart_items.exists():
            messages.warning(request, "Your cart is empty")
            return redirect('cart:cartproducts')
        
        # Calculate totals
        cart_subtotal = sum(item.total_price for item in cart_items)
        total_savings = sum(item.total_discount for item in cart_items)
        cart_total = cart_subtotal - total_savings
        
        # Create order
        order = Order(
            user=request.user,
            total_amount=cart_total,
            discount_amount=total_savings,
            status='pending',
            payment_method='cash_on_delivery'
        )
        
        # Check if user has a default shipping address
        default_address = ShippingAddress.objects.filter(user=request.user, is_default=True).first()
        if default_address:
            order.shipping_address = default_address
            order.contact_phone = default_address.phone
        
        order.save()
        
        # Create order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                discount_price=item.product.discount_price
            )
        
        # Clear the cart
        cart_items.delete()
        
        return redirect('checkout:order_confirmation', order_id=order.id)






from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.shipping_address and order.status == 'confirmed':
        # Send confirmation email
        
        return render(request, 'checkout/order_success.html', {'order': order})
    
    shipping_addresses = ShippingAddress.objects.filter(user=request.user)
    
    if request.method == 'POST':
        if 'confirm_order' in request.POST:
            address_id = request.POST.get('shipping_address')
            if address_id:
                address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
                order.shipping_address = address
                order.status = 'confirmed'
                order.save()
                
                # Send confirmation email
                send_order_confirmation_email(order)
                return render(request, 'checkout/order_success.html', {'order': order})
            else:
                messages.error(request, "Please select a shipping address")
        
        elif 'add_address' in request.POST:
            request.session['order_confirmation_redirect'] = order_id
            return redirect('auth:profile')
    
    context = {
        'order': order,
        'shipping_addresses': shipping_addresses
    }
    return render(request, 'checkout/order_confirmation.html', context)

from smtplib import SMTPException
from django.core.mail import EmailMessage

def send_order_confirmation_email(order):
    subject = f"Order Confirmation - #{order.order_number}"
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'items': order.items.all()
    })
    plain_message = strip_tags(html_message)
    
    try:
        email = EmailMessage(
            subject=subject,
            body=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[order.user.email],
        )
        email.content_subtype = "html"  # Set content to HTML
        email.send(fail_silently=False)
        
    except SMTPException as e:
        print(f"Failed to send order confirmation email: {e}")
        # You might want to implement retry logic or notification here






@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST' and 'cancel_order' in request.POST:
        if not order.can_be_cancelled():
            messages.error(request, "This order cannot be cancelled at this stage.")
            return redirect('checkout:order_detail', order_id=order.id)
            
        form = OrderCancellationForm(request.POST)
        if form.is_valid():
            order.status = 'cancelled'
            order.cancellation_reason = form.cleaned_data['reason']
            order.cancellation_notes = form.cleaned_data['notes']
            order.save()
            
            # Here you might want to send a cancellation email
            # send_order_cancellation_email(order)
            
            messages.success(request, "Your order has been cancelled successfully.")
            return redirect('checkout:order_detail', order_id=order.id)
    else:
        form = OrderCancellationForm()
    
    context = {
        'order': order,
        'cancellation_form': form,
    }
    return render(request, 'checkout/order_detail.html', context)




from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_order_cancellation_email(order):
    subject = f"Order #{order.order_number} Cancellation Confirmation"
    message = render_to_string('emails/order_cancelled.html', {
        'order': order,
    })
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=message,
        fail_silently=False,
    )