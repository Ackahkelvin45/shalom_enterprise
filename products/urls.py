from django.urls import path
from .views import products,products_detail


app_name="products"

urlpatterns=[

    path ('all/',products,name="all-products"),
    path ('detial/',products_detail,name="product-detail")

    
]