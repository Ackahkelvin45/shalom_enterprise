from django.contrib import admin
from .models import ProductCategory, Product, ProductImage,Brand,Cart,Wishlist,ProductReview

# Register your models here.


admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(ProductImage)   
admin.site.register(Brand)
admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(ProductReview)