from django.contrib import admin
from .models import ProductCategory, Product, ProductImage,Brand,Cart,Wishlist,ProductReview,HotDeal
from unfold.admin import ModelAdmin

# Register your models here.



@admin.register(ProductCategory)
@admin.register(Product)
@admin.register(ProductImage)
@admin.register(Brand)
@admin.register(Cart)
@admin.register(Wishlist)
@admin.register(ProductReview)
@admin.register(HotDeal)

class CustomAdminClass(ModelAdmin):
    pass