from django.urls import path
from .views import products,product_detail,wishlist_api,cart_api,submit_review,categories_json,show_hotdeals,top_sellers


app_name="products"

urlpatterns=[

    path ('all/',products,name="all-products"),
    path ('detial/<str:slug>/',product_detail,name="product-detail"),
    # Wishlist URLs
    path('api/wishlist/', wishlist_api, name='wishlist'),
    path('api/wishlist/<int:product_id>/', wishlist_api, name='wishlist-item'),
    
    # Cart URLs
    path('api/cart/', cart_api, name='cart'),
    path('api/cart/<int:product_id>/', cart_api, name='cart-item'),

    path('api/review/submit/<int:product_id>/', submit_review, name='submit_review'),
    path('api/categories/', categories_json, name='categories-json'),
    path('hot-deals/', show_hotdeals, name='hot-deals'),
    path('top-selling/', top_sellers, name='top-selling'),




    
]

