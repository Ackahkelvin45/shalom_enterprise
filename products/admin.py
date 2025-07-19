from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from .models import ProductCategory, Product, ProductImage, Brand, Cart, Wishlist, ProductReview, HotDeal, TopSeller


class ProductImageInline(StackedInline):
    model = ProductImage
    extra = 3
    min_num = 1
    fields = ('image', 'is_main', 'image_preview')
    readonly_fields = ('image_preview',)
    ordering = ('-is_main',)  # Main image first

    verbose_name = "Product Image"
    verbose_name_plural = "Product Images"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "No image uploaded"
    image_preview.short_description = 'Preview'


class ProductReviewInline(TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('user', 'rating', 'title', 'comment', 'created_at')
    fields = ('user', 'rating', 'title', 'comment', 'created_at')
    can_delete = False
    ordering = ('-created_at',)
    classes = ['collapse']
    verbose_name = "Review"
    verbose_name_plural = "Reviews"


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('name', 'category', 'brand', 'price', 'is_active', 'image_preview')
    list_filter = ('is_active', 'category', 'brand', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'category__name', 'brand__name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('main_image_preview',)  # Removed rating-related readonly fields
    list_editable = ('is_active', 'price')
    list_per_page = 50
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    save_on_top = True

    def get_fieldsets(self, request, obj=None):
        # Different fieldsets for add vs change view
        if obj:  # Editing an existing product
            return (
                ('Basic Information', {
                    'fields': ('name', 'slug', 'description', 'category', 'brand')
                }),
                ('Pricing', {
                    'fields': ('price',),
                }),
                ('Status', {
                    'fields': ('is_active', 'main_image_preview'),
                }),
            )
        else:  # Adding a new product
            return (
                ('Basic Information', {
                    'fields': ('name', 'slug', 'description', 'category', 'brand')
                }),
                ('Pricing', {
                    'fields': ('price',),
                }),
                ('Status', {
                    'fields': ('is_active',)                }),
            )

    def get_readonly_fields(self, request, obj=None):
        # Only show main_image_preview when editing existing product
        if obj:
            return ('main_image_preview',)
        return ()

    def main_image_preview(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', main_image.image.url)
        return "No main image set"
    main_image_preview.short_description = 'Main Image Preview'

    def image_preview(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', main_image.image.url)
        return "-"
    image_preview.short_description = 'Image'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'brand').prefetch_related('images')
@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'product_count', 'icon_preview')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('product_count', 'icon_preview')
    list_per_page = 50

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.icon.url)
        return "No icon"
    icon_preview.short_description = 'Icon Preview'

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ('name', 'is_active', 'product_count', 'logo_preview')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('product_count', 'logo_preview')
    list_per_page = 50

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.logo.url)
        return "No logo"
    logo_preview.short_description = 'Logo Preview'

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ('product', 'image_preview', 'is_main')
    list_filter = ('is_main', 'product__category')
    search_fields = ('product__name',)
    list_per_page = 50
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'price_used', 'total_price', 'added_at')
    list_filter = ('added_at', 'updated_at')
    search_fields = ('user__email', 'product__name')
    list_select_related = ('user', 'product')
    list_per_page = 50
    date_hierarchy = 'added_at'


@admin.register(Wishlist)
class WishlistAdmin(ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__email', 'product__name')
    list_select_related = ('user', 'product')
    list_per_page = 50
    date_hierarchy = 'added_at'


@admin.register(ProductReview)
class ProductReviewAdmin(ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__email', 'title')
    list_select_related = ('product', 'user')
    list_per_page = 50
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(HotDeal)
class HotDealAdmin(ModelAdmin):
    list_display = ('product', 'discount_percentage', 'fixed_price', 
                   'current_price', 'is_active', 'is_currently_active', 
                   'start_date', 'end_date')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('product__name',)
    list_select_related = ('product',)
    list_per_page = 50
    date_hierarchy = 'start_date'
    readonly_fields = ('current_price', 'is_currently_active')


@admin.register(TopSeller)
class TopSellerAdmin(ModelAdmin):
    list_display = ('product', 'sales_count', 'is_active', 'last_updated')
    list_filter = ('is_active', 'last_updated')
    search_fields = ('product__name',)
    list_select_related = ('product',)
    list_per_page = 50
    date_hierarchy = 'last_updated'
    list_editable = ('is_active', 'sales_count')