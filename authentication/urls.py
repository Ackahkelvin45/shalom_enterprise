from django.urls import path
from .views import sign_in,signup,verify_otp,resend_otp,user_logout,forgot_password,reset_password


app_name="auth"

urlpatterns=[
    path ("signin/" ,sign_in,name="signin"),
    path ("register/",signup,name="signup"),
    path("verify/<int:user_id>/",verify_otp,name="verify_otp"),
    path ('resend-otp/<int:user_id>/',resend_otp,name="resend_otp"),
    path('logout/', user_logout, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', reset_password, name='reset_password'),

]