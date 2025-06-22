from django.contrib import admin
from .models import Settings,SocialMedia

# Register your models here.
from unfold.admin import ModelAdmin



@admin.register(Settings)
class CustomAdminClass(ModelAdmin):
    pass


@admin.register(SocialMedia)   
class CustomAdminClass(ModelAdmin):
    pass