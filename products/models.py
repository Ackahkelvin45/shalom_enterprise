from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.cache import cache


# Create your models here.

class ProductCategory(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100, blank=False, null=True,unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    icon= models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name
    

class Brand ( models.Model):
    """Brand model"""
    name = models.CharField(max_length=100, blank=False, null=True,unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    logo= models.ImageField(upload_to='brands/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name

class Product(models.Model):
    """Main product model"""
    name = models.CharField(max_length=200,blank=False, null=True,unique=True)
    slug = models.SlugField(max_length=200, unique=True,blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2,blank=False, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    is_active = models.BooleanField(default=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def get_top_sellers(cls, limit=10):
        """Get the top selling products with caching"""
        cache_key = f'top_sellers_{limit}'
        top_sellers = cache.get(cache_key)
        
        if top_sellers is None:
            top_sellers = list(cls.objects.filter(
                topseller__is_active=True
            ).select_related(
                'topseller'
            ).order_by(
                '-topseller__sales_count'
            )[:limit])
            cache.set(cache_key, top_sellers, 60 * 60)  # Cache for 1 hour
        
        return top_sellers
    

    @property
    def rating_count(self):
            """Return total number of reviews"""
            return self.reviews.count()

    @property
    def average_rating(self):
        """Calculate average rating using prefetched data if available"""
        reviews = getattr(self, 'prefetched_reviews', None) or self.reviews.all()
        
        if not reviews:
            return 0
            
        total = sum(review.rating for review in reviews)
        average = total / len(reviews)
        return round(average * 2) / 2  # Round to nearest 0.5

    @property
    def rating_count(self):
        """Return count using prefetched data if available"""
        reviews = getattr(self, 'prefetched_reviews', None) or self.reviews.all()
        return len(reviews)


class ProductImage(models.Model):
    """Product image model"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Image for {self.product.name}"
   



User = get_user_model()

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Prevent duplicate items
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

    def __str__(self):
        return f"{self.user.email}'s wishlist: {self.product.name}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price_used = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')  
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        price_info = f"@{self.price_used}"
        if self.price_used < self.product.price:
            price_info += f" (DEAL! Save GHS{self.product.price - self.price_used} each)"
        return f"{self.user.email}'s cart: {self.product.name} x{self.quantity} {price_info}"
    

    @property
    def total_price(self):
        return self.price_used * self.quantity  # Use price_used instead of product.price

    @property
    def total_discount(self):
        if self.price_used < self.product.price:
            return (self.product.price - self.price_used) * self.quantity
        return 0
    

    @property
    def total_price(self):
        return self.product.price * self.quantity

    @property
    def total_discount(self):
        if self.product.discount_price:
            return (self.product.price - self.product.discount_price) * self.quantity
        return 0
    


class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}'s review for {self.product.name}"

    def get_rating_stars(self):
        return range(self.rating)
    
    def get_empty_stars(self):
        return range(5 - self.rating)
    



class HotDeal(models.Model):
    """Model for managing product deals with either percentage discount or fixed price"""
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='hot_deals'
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Percentage discount (e.g., 20 for 20% off)"
    )
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Automatically calculated current price"
    )
    fixed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Fixed special price (overrides percentage discount)"
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text="When the deal should become active"
    )
    end_date = models.DateTimeField(
        help_text="When the deal should expire"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Toggle deal on/off"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Hot Deal"
        verbose_name_plural = "Hot Deals"

    def __str__(self):
        return f"Hot Deal for {self.product.name}"

    def clean(self):
        # Validate that at least one pricing option is set
        if not self.discount_percentage and not self.fixed_price:
            raise ValidationError("Either discount percentage or fixed price must be set")
        
        # Validate that end date is after start date
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")

        # Calculate and set current_price during validation
        self._calculate_current_price()

    def save(self, *args, **kwargs):
        # Calculate current price before saving
        self._calculate_current_price()
        super().save(*args, **kwargs)

    def _calculate_current_price(self):
        """Internal method to calculate and set current_price"""
        if self.fixed_price is not None:
            self.current_price = self.fixed_price
        elif self.discount_percentage is not None and self.product.price is not None:
            discounted = self.product.price * (100 - self.discount_percentage) / 100
            self.current_price = max(0, discounted)  # Ensure price doesn't go negative
        else:
            self.current_price = None

    @property
    def is_currently_active(self):
        """Check if the deal is currently active based on dates"""
        now = timezone.now()
        if not all([self.start_date, self.end_date]):
            return False
        return (self.is_active and 
                self.start_date <= now <= self.end_date)




class TopSeller(models.Model):
    """Model to track top selling products"""
    product = models.OneToOneField(
        Product, 
        on_delete=models.CASCADE,
        related_name='topseller'  # Changed from 'top_seller' to 'topseller'
    )
    sales_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of times this product has been sold"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this product should be displayed as a top seller"
    )
    
    class Meta:
        ordering = ['-sales_count']
        verbose_name = "Top Seller"
        verbose_name_plural = "Top Sellers"

    def __str__(self):
        return f"Top Seller: {self.product.name} ({self.sales_count} sales)"