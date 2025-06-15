from django.urls import path
from .views import sign_in,signup,verify_otp,resend_otp,user_logout,forgot_password,reset_password,add_shipping_address,editProfile,profile,set_default_address,edit_shipping_address,delete_shipping_address


app_name="auth"

urlpatterns=[
    path ("signin/" ,sign_in,name="signin"),
    path ("register/",signup,name="signup"),
    path("verify/<int:user_id>/",verify_otp,name="verify_otp"),
    path ('resend-otp/<int:user_id>/',resend_otp,name="resend_otp"),
    path('logout/', user_logout, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', reset_password, name='reset_password'),
    path ('add-shipping-address/',add_shipping_address,name="add_shipping_address"),
    path ("edit-shipping-address/<int:id>/",edit_shipping_address,name="edit_shipping_address"),
   path('address/<int:address_id>/delete/',delete_shipping_address, name='delete_shipping_address'),
       path('address/<int:address_id>/set-default/',set_default_address, name='set_default_address'),

    path ("profile/",profile,name="profile"),
    path ("edit_profile/",editProfile,name="edit_profile"),

]