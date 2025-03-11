# utils.py
import random
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import  CustomUser,OTP

def generate_otp():
    return str(random.randint(100000, 999999))  # 6-digit OTP

def send_otp_email(email, otp):
    subject = "Your OTP for Email Verification"
    message = f"Your OTP for email verification is: {otp}"
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

def create_otp_for_user(user):
    otp_code = generate_otp()
    expires_at = timezone.now() + timezone.timedelta(minutes=5)  # OTP expires in 5 minutes
    OTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)

    # Use threading to send the email asynchronously
    email_thread = threading.Thread(target=send_otp_email, args=(user.email, otp_code))
    email_thread.start()  # Start the thread



def send_forgot_password_email(message,user):
    subject="Reset Passowrd"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

    