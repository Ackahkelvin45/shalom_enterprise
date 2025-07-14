import random
import threading
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from .models import CustomUser, OTP

def generate_otp():
    return str(random.randint(100000, 999999))  # 6-digit OTP

def get_otp_email_template(otp_code):
    """Generate HTML template for OTP email"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Arial', sans-serif;
                background-color: #f5f5f5;
                color: #333;
                line-height: 1.6;
            }}
            
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #D10024 0%, #2B2D42 100%);
                padding: 40px 30px;
                text-align: center;
                color: white;
            }}
            
            .header h1 {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }}
            
            .header p {{
                font-size: 16px;
                opacity: 0.9;
            }}
            
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 18px;
                color: #2B2D42;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            
            .message {{
                font-size: 16px;
                color: #555;
                margin-bottom: 30px;
                line-height: 1.8;
            }}
            
            .otp-container {{
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border: 2px solid #D10024;
                border-radius: 12px;
                padding: 25px;
                text-align: center;
                margin: 30px 0;
            }}
            
            .otp-label {{
                font-size: 14px;
                color: #2B2D42;
                font-weight: 600;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .otp-code {{
                font-size: 36px;
                font-weight: 800;
                color: #D10024;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
                text-shadow: 0 2px 4px rgba(209, 0, 36, 0.2);
            }}
            
            .otp-validity {{
                font-size: 14px;
                color: #666;
                margin-top: 15px;
                font-style: italic;
            }}
            
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
            }}
            
            .warning-icon {{
                color: #f39c12;
                font-weight: bold;
                margin-right: 8px;
            }}
            
            .footer {{
                background-color: #2B2D42;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .footer p {{
                margin-bottom: 10px;
                opacity: 0.9;
            }}
            
            .footer .company-name {{
                font-weight: 700;
                font-size: 18px;
                color: #D10024;
                margin-bottom: 15px;
            }}
            
            .divider {{
                height: 4px;
                background: linear-gradient(90deg, #D10024 0%, #2B2D42 100%);
                margin: 0;
            }}
            
            @media screen and (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                    border-radius: 8px;
                }}
                
                .header, .content, .footer {{
                    padding: 25px 20px;
                }}
                
                .header h1 {{
                    font-size: 24px;
                }}
                
                .otp-code {{
                    font-size: 28px;
                    letter-spacing: 4px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Email Verification</h1>
                <p>Secure your account with verification</p>
            </div>
            
            <div class="divider"></div>
            
            <div class="content">
                <div class="greeting">Hello there!</div>
                
                <div class="message">
                    We received a request to verify your email address. Please use the One-Time Password (OTP) below to complete your verification process.
                </div>
                
                <div class="otp-container">
                    <div class="otp-label">Your Verification Code</div>
                    <div class="otp-code">{otp_code}</div>
                    <div class="otp-validity">This code expires in 5 minutes</div>
                </div>
                
                <div class="warning">
                    <span class="warning-icon">⚠️</span>
                    <strong>Security Notice:</strong> Never share this code with anyone. Our team will never ask for your OTP over phone or email.
                </div>
                
                <div class="message" style="margin-top: 30px; font-size: 14px; color: #666;">
                    If you didn't request this verification, please ignore this email or contact our support team if you have concerns about your account security.
                </div>
            </div>
            
            <div class="footer">
                <div class="company-name">Your Company Name</div>
                <p>This is an automated message, please do not reply to this email.</p>
                <p>&copy; 2025 Your Company. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_password_reset_email_template(reset_link=None, custom_message=None):
    """Generate HTML template for password reset email"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Arial', sans-serif;
                background-color: #f5f5f5;
                color: #333;
                line-height: 1.6;
            }}
            
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #D10024 0%, #2B2D42 100%);
                padding: 40px 30px;
                text-align: center;
                color: white;
            }}
            
            .header h1 {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }}
            
            .header p {{
                font-size: 16px;
                opacity: 0.9;
            }}
            
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 18px;
                color: #2B2D42;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            
            .message {{
                font-size: 16px;
                color: #555;
                margin-bottom: 30px;
                line-height: 1.8;
            }}
            
            .reset-button {{
                display: inline-block;
                background: linear-gradient(135deg, #D10024 0%, #b8001f 100%);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                text-align: center;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(209, 0, 36, 0.3);
            }}
            
            .reset-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(209, 0, 36, 0.4);
            }}
            
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
            }}
            
            .warning-icon {{
                color: #f39c12;
                font-weight: bold;
                margin-right: 8px;
            }}
            
            .footer {{
                background-color: #2B2D42;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .footer p {{
                margin-bottom: 10px;
                opacity: 0.9;
            }}
            
            .footer .company-name {{
                font-weight: 700;
                font-size: 18px;
                color: #D10024;
                margin-bottom: 15px;
            }}
            
            .divider {{
                height: 4px;
                background: linear-gradient(90deg, #D10024 0%, #2B2D42 100%);
                margin: 0;
            }}
            
            @media screen and (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                    border-radius: 8px;
                }}
                
                .header, .content, .footer {{
                    padding: 25px 20px;
                }}
                
                .header h1 {{
                    font-size: 24px;
                }}
                
                .reset-button {{
                    display: block;
                    width: 100%;
                    margin: 20px 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Password Reset</h1>
                <p>Secure your account</p>
            </div>
            
            <div class="divider"></div>
            
            <div class="content">
                <div class="greeting">Hello there!</div>
                
                <div class="message">
                    {custom_message if custom_message else "We received a request to reset your password. Click the button below to create a new password for your account."}
                </div>
                
                {f'<div style="text-align: center; margin: 30px 0;"><a href="{reset_link}" class="reset-button">Reset My Password</a></div>' if reset_link else ''}
                
                <div class="warning">
                    <span class="warning-icon">⚠️</span>
                    <strong>Security Notice:</strong> If you didn't request a password reset, please ignore this email or contact our support team immediately.
                </div>
                
                <div class="message" style="margin-top: 30px;">
                    This password reset link will expire in 24 hours for your security. If you need assistance, please contact our support team.
                </div>
                
                {f'<div class="message" style="margin-top: 20px; font-size: 14px; color: #666;">copy and paste the URL below into your web browser if you havw trouble :<br><span style="color: #D10024; word-break: break-all;">{reset_link}</span></div>' if reset_link else ''}
            </div>
            
            <div class="footer">
                <div class="company-name">Your Company Name</div>
                <p>This is an automated message, please do not reply to this email.</p>
                <p>&copy; 2025 Your Company. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_otp_email(email, otp):
    
    try:
        subject = "Your OTP for Email Verification"
        text_content = f"Your OTP for email verification is: {otp}"
        html_content = get_otp_email_template(otp)
        
        # Create email message
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        print(f"Error sending OTP email: {str(e)}")
        # You might want to raise the exception again or handle it differently
        raise  # This re-raises the caught exception

def create_otp_for_user(user):
    otp_code = generate_otp()
    expires_at = timezone.now() + timezone.timedelta(minutes=5)  # OTP expires in 5 minutes
    OTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)

    # Use threading to send the email asynchronously
    email_thread = threading.Thread(target=send_otp_email, args=(user.email, otp_code))
    email_thread.start()  # Start the thread

def send_forgot_password_email(message, user, reset_link=None):
    subject = "Reset Password"
    text_content = message
    html_content = get_password_reset_email_template(reset_link, message)
    
    # Create email message
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()