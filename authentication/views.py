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
        email = request.POST.get('email', '').strip()
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

        try:
            user = CustomUser(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                is_verified=False  # User not verified until OTP confirmation
            )
            user.set_password(password)  # Hash the password
            user.save()

            # Generate and send OTP
            create_otp_for_user(user)

            return redirect('auth:verify_otp', user_id=user.id)
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return render(request, 'authentication/signup.html')
            
    # For GET requests, simply render the signup template
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
