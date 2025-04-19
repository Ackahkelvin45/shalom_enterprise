# serializers.py
from rest_framework import serializers
from .models import Product, Wishlist, Cart,ProductImage
from .models import ProductCategory



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            request = self.context.get('request')
            if request:
                representation['image_url'] = request.build_absolute_uri(instance.image.url)
            else:
                # Fallback for when request is not available (shouldn't happen in your case now)
                representation['image_url'] = instance.image.url
        return representation
    
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'discount_price', 'slug', 'images', 'main_image']
    
    def get_main_image(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return self.context['request'].build_absolute_uri(main_image.image.url)
        first_image = obj.images.first()
        if first_image:
            return self.context['request'].build_absolute_uri(first_image.image.url)
        return None

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_at']

class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity', 'total_price', 'total_discount', 'added_at', 'image_url']

    def get_total_price(self, obj):
        return obj.total_price

    def get_total_discount(self, obj):
        return obj.total_discount
        
    def get_image_url(self, obj):
        main_image = obj.product.images.filter(is_main=True).first()
        if main_image:
            return self.context['request'].build_absolute_uri(main_image.image.url)
        first_image = obj.product.images.first()
        if first_image:
            return self.context['request'].build_absolute_uri(first_image.image.url)
        return None
    





class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

class ProductCategorySerializer(serializers.ModelSerializer):
    children = RecursiveSerializer(many=True, read_only=True)
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCategory
        fields = [
            'id', 
            'name', 
            'slug', 
            'description', 
            'parent', 
            'icon_url', 
            'is_active', 
            'created_at', 
            'updated_at', 
            'children'
        ]
    
    def get_icon_url(self, obj):
        if obj.icon:
            return self.context['request'].build_absolute_uri(obj.icon.url)
        return None