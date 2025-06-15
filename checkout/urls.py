# urls.py
from django.urls import path
from .views import confirm_order, order_confirmation,order_detail


app_name="checkout"
urlpatterns = [
  
    path('confirm/', confirm_order, name='confirm_order'),
    path('confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),


    
]