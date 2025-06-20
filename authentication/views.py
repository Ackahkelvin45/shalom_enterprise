from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CustomUserCreationForm
from .utils import create_otp_for_user,send_otp_email,generate_otp,send_forgot_password_email
from .models import CustomUser,OTP
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import authenticate, login,logout
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .forms import ShippingAddressForm
from .models import ShippingAddress
from django.contrib.auth.decorators import login_required
from products.models import Cart,Wishlist
from checkout.models import Order,OrderItem


from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib import messages



def sign_in(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, email=email, password=password)

        if user is not None:
       
            if user.is_verified:
               
                login(request, user)
                messages.success(request, "You have been logged in successfully!")
                return redirect('main:index')  
            else:
                messages.error(request, "Your account is not verified. Please verify your email.")
                return redirect('auth:verify_otp', user_id=user.id)  
        else:
           
            messages.error(request, "Invalid email or password.")
            return redirect( 'auth:signin')

  
    return render(request, 'authentication/signin.html')

def signup(request):
    if request.method == 'POST':
        # Extract data from POST
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()  # Normalize email
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        phone_number = request.POST.get('phone_number', '').strip()

        # Basic validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'authentication/signup.html')
            
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'authentication/signup.html')

        if not (any(c.isupper() for c in password) and any(c.isdigit() for c in password)):
            messages.error(request, "Password must contain at least one capital letter and one number.")
            return render(request, 'authentication/signup.html')

        # Check for existing email or phone number before creating user
        error_messages = []
        if CustomUser.objects.filter(email__iexact=email).exists():
            error_messages.append("This email is already registered. Please use a different email or log in.")
        
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            error_messages.append("This phone number is already registered. Please use a different number or log in.")
        
        if error_messages:
            for msg in error_messages:
                messages.error(request, msg)
            return render(request, 'authentication/signup.html')

        try:
            user = CustomUser(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                is_verified=False
            )
            user.set_password(password)
            user.save()

            # Generate and send OTP
            create_otp_for_user(user)

            return redirect('auth:verify_otp', user_id=user.id)
            
        except Exception as e:
            # Log the actual error for debugging
            print(f"Error creating user: {str(e)}")
            # Show generic error message to user
            messages.error(request, "We encountered an issue creating your account. Please try again.")
            return render(request, 'authentication/signup.html')
            
    return render(request, 'authentication/signup.html')

def verify_otp(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        print(otp_entered)

        # Get the latest OTP for the user
        latest_otp = OTP.objects.filter(user=user).order_by('-created_at').first()
        print(latest_otp.otp_code)

        if latest_otp and not latest_otp.is_expired() and latest_otp.otp_code == otp_entered:
            user.is_verified = True  # Mark user as verified
            user.save()
            messages.success(request, "Email verified successfully! You can now log in.")
            return redirect('auth:signin')
        else:
            messages.error(request, "Invalid or expired OTP. Please try again.")
            return redirect('auth:verify_otp', user_id=user.id)  # Redirect back to the same page

    return render(request, 'authentication/OTPverification.html', {'user_id': user.id})


def resend_otp(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Generate a new OTP
    otp_code = generate_otp()
    
    expires_at = timezone.now() + timezone.timedelta(minutes=5)
    
    # Create a new OTP instance
    OTP.objects.create(
        user=user,
        otp_code=otp_code,
        expires_at=expires_at
    )
    
    send_otp_email(user.email, otp_code)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'A new OTP has been sent to your email.',
        })
    
    # Handle non-AJAX requests
    messages.success(request, "A new OTP has been sent to your email.")
    return redirect('auth:verify_otp', user_id=user.id)





def user_logout(request):
    logout(request)  # Log out the user
    return redirect('auth:signin')  # Redirect to the sign-in page






class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_verified}"

password_reset_token_generator = CustomPasswordResetTokenGenerator()

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = CustomUser.objects.filter(email=email).first()

        if user:
            # Generate a password reset token
            token = password_reset_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Create the reset link
            reset_link = request.build_absolute_uri(
                reverse('auth:reset_password', kwargs={'uidb64': uid, 'token': token})
            )

            # Send the email
            message = render_to_string('authentication/password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            
            send_forgot_password_email(message=message,user=user)

            messages.success(request, "A password reset link has been sent to your email.")
            return redirect('auth:signin')
        else:
            messages.error(request, "No user found with this email address.")
            return redirect('auth:forgot_password')

    return render(request, 'authentication/forgot_password.html')





def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and password_reset_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your password has been reset successfully. You can now log in.")
                return redirect('auth:signin')
            else:
                messages.error(request, "Passwords do not match.")
                return redirect('auth:reset_password', uidb64=uidb64, token=token)  # Fixed here

        return render(request, 'authentication/reset_password.html')
    else:
        messages.error(request, "Invalid or expired password reset link.")
        return redirect('auth:signin')








def editProfile(request):

    
    user = request.user  

    if request.method == "POST":
        try:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()

            # Basic validation
            if not first_name:
                raise ValidationError("First name is required.")
            if not last_name:
                raise ValidationError("Last name is required.")
            if not email:
                raise ValidationError("Email is required.")
            
            # Email format validation
            if '@' not in email:
                raise ValidationError("Please enter a valid email address.")
            
            # Check if email is being changed to another user's email
            if email != user.email and CustomUser.objects.filter(email=email).exists():
                raise ValidationError("This email is already in use by another account.")
            
            # Check if phone number is being changed to another user's phone
            if phone_number and phone_number != user.phone_number and CustomUser.objects.filter(phone_number=phone_number).exists():
                raise ValidationError("This phone number is already in use by another account.")

            # Update user fields
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.phone_number = phone_number
            
            # Full clean and save
            user.full_clean()  # This triggers model validation
            user.save()
            
            messages.success(request, "Profile updated successfully.")
            return redirect('auth:profile')
            
        except ValidationError as e:
            messages.error(request, str(e))
        except IntegrityError as e:
            if 'email' in str(e).lower():
                messages.error(request, "This email is already in use by another account.")
            elif 'phone_number' in str(e).lower():
                messages.error(request, "This phone number is already in use by another account.")
            else:
                messages.error(request, "An error occurred while saving your profile. Please try again.")
        except Exception as e:
            # Log the actual error for debugging
            print(f"Error updating profile: {str(e)}")
            messages.error(request, "An unexpected error occurred. Please try again.")
    
    return render(request, 'authentication/profile.html', {'user': user})






@login_required
def profile(request):
    user = request.user
    wishlist_items = Wishlist.objects.filter(user=user).all()
    
    # Get filter parameter from request
    status_filter = request.GET.get('status', 'confirmed')
    
    # Filter orders based on status
    orders = Order.objects.filter(user=user).prefetch_related('items')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    shipping_addresses = ShippingAddress.objects.filter(user=user).order_by('-is_default', '-created_at')
    
    # Prepare addresses with their edit forms
    addresses_with_forms = []
    for address in shipping_addresses:
        addresses_with_forms.append({
            'address': address,
            'edit_form': ShippingAddressForm(instance=address)
        })
    
    context = {
        'user': user,
        'wishlist_items': wishlist_items,
        'orders': orders,
        'addresses_with_forms': addresses_with_forms,
        'address_form': ShippingAddressForm(),
        'status_filter': status_filter,
        'order_statuses': Order.ORDER_STATUS,
    }
    return render(request, 'authentication/profile.html', context)


@login_required
def add_shipping_address(request):
    redirect_order_id = request.session.pop('order_confirmation_redirect', None)
    next_url = reverse('auth:profile')  # Default to profile
    
    if redirect_order_id:
        next_url = reverse('checkout:order_confirmation', args=[redirect_order_id])
    
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            if address.is_default:
                ShippingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            address.save()
            messages.success(request, "Shipping address added successfully!")
            return redirect(next_url)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect(next_url)



@login_required
def edit_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            edited_address = form.save(commit=False)
            
            if edited_address.is_default:
                ShippingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            edited_address.save()
            messages.success(request, "Shipping address updated successfully!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return redirect('auth:profile')


@login_required
def delete_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Shipping address deleted successfully!'
            })
        
        messages.success(request, "Shipping address deleted successfully!")
        return redirect('auth:profile')
    
    # If not POST, redirect back to profile
    return redirect('auth:profile')

@login_required
def set_default_address(request, address_id):
    ShippingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, "Default shipping address updated successfully!")
    return redirect('auth:profile')