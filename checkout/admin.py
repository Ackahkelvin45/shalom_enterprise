from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('created_at', 'total_price')
    fields = ('product', 'quantity', 'price', 'discount_price', 'total_price', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'status' in self.fields:
            self.fields['status'].widget.attrs.update({
                'class': 'status-select',
                'style': 'padding: 5px; border-radius: 4px; border: 1px solid #ddd;'
            })

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderStatusForm
    list_display = ('order_number', 'user_email', 'get_status_display', 'total_amount', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('order_number', 'user__email', 'contact_phone')
    actions = ['cancel_orders']
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'total_amount')
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'total_amount', 'discount_amount')
        }),
        ('Shipping & Contact', {
            'fields': ('shipping_address', 'contact_phone')
        }),
        ('Payment & Dates', {
            'fields': ('payment_method', 'created_at', 'updated_at')
        }),
    )
    inlines = [OrderItemInline]

    class Media:
        css = {
            'all': ('admin/css/order_status.css',)
        }
        js = ('admin/js/order_status.js',)

    def get_status_display(self, obj):
        status_colors = {
            'pending': '#FFA500',  # Orange
            'processing': '#1E90FF',  # DodgerBlue
            'shipped': '#9370DB',  # MediumPurple
            'delivered': '#32CD32',  # LimeGreen
            'cancelled': '#FF0000',  # Red
            'refunded': '#A9A9A9',  # DarkGray
        }
        color = status_colors.get(obj.status.lower(), '#000000')
        return format_html(
            '<span class="status-badge" style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_display.short_description = 'Status'
    get_status_display.admin_order_field = 'status'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def cancel_orders(self, request, queryset):
        for order in queryset:
            if order.can_be_cancelled():
                order.status = 'cancelled'
                order.save()
        self.message_user(request, f"{queryset.count()} orders were cancelled.")
    cancel_orders.short_description = "Cancel selected orders"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'shipping_address')
        return self.readonly_fields

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'product_name', 'quantity', 'price', 'discount_price', 'total_price')
    list_filter = ('order__status', 'created_at')
    search_fields = ('order__order_number', 'product__name')
    readonly_fields = ('order', 'product', 'price', 'discount_price', 'created_at', 'total_price')
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = 'Order Number'
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    
    def has_add_permission(self, request):
        return False