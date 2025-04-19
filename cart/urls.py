from django.urls import path
from .views import get_cart


app_name="cart"

urlpatterns=[
    path("all/",get_cart,name="cartproducts")
]

