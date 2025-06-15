from django.urls import path
from .views import get_cart,remove_from_cart,update_cart


app_name="cart"

urlpatterns=[
    path("all/",get_cart,name="cartproducts"),
     path('remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('update/<int:product_id>/', update_cart, name='update_cart'),
]

