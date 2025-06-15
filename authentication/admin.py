from django.contrib import admin
from .models import CustomUser,OTP

# Register your models here.
from unfold.admin import ModelAdmin





@admin.register(CustomUser)
class CustomAdminClass(ModelAdmin):
    pass