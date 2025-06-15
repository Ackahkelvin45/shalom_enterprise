from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):  # or admin.StackedInline for a different layout
    model = OrderItem
    extra = 0  # Don't show extra empty forms
    readonly_fields = ('created_at', 'total_price')
    fields = ('product', 'quantity', 'price', 'discount_price', 'total_price', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False  # Prevent adding items directly through order admin

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user_email', 'status', 'total_amount', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'payment_method')
    search_fields = ('order_number', 'user__email', 'contact_phone')
    actions = ['cancel_orders']
    
    def cancel_orders(self, request, queryset):
        for order in queryset:
            if order.can_be_cancelled():
                order.status = 'cancelled'
                order.save()
                
        self.message_user(request, f"{queryset.count()} orders were cancelled.")
    cancel_orders.short_description = "Cancel selected orders"
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


    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing order
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
    
    def discount_price(self, obj):
        return obj.discount_price
    discount_price.short_description = 'Discounted Price'
    
    def has_add_permission(self, request):
        return False  # Prevent adding items directly - should be done through order