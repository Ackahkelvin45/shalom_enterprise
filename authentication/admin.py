from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OTP, ShippingAddress
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin

# Unregister default Group
admin.site.unregister(Group)

@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    # Fields to display in the list view
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 
                   'is_active', 'is_staff', 'is_verified', 'created_at')
    
    # Fields that can be edited directly in the list view
    list_editable = ('is_active', 'is_verified')
    
    # Fields to search by
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    
    # Filter options
    list_filter = ('is_active', 'is_staff', 'is_verified', 'created_at')
    
    # Fieldsets for add/edit forms
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_active', 'is_staff', 'is_verified')
        }),
        ('Dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields shown when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'phone_number'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    
    # Ordering
    ordering = ('-created_at',)
    
    # Pagination
    list_per_page = 25
    
    # Remove permissions fields completely
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'user_permissions' in form.base_fields:
            del form.base_fields['user_permissions']
        if 'groups' in form.base_fields:
            del form.base_fields['groups']
        return form

@admin.register(OTP)
class OTPAdmin(ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__email', 'otp_code')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(ShippingAddress)
class ShippingAddressAdmin(ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'region', 'is_default', 'created_at')
    list_filter = ('city', 'region', 'is_default')
    search_fields = ('user__email', 'full_name', 'city', 'region')
    list_editable = ('is_default',)
    readonly_fields = ('created_at', 'updated_at')