from django.db import models

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
    

    @property
    def average_rating(self):
        """Calculate average rating using prefetched data if available"""
        # Try to use prefetched reviews first
        reviews = getattr(self, 'prefetched_reviews', None) or self.reviews.all()
        
        if not reviews:
            return 0
            
        total = sum(review.rating for review in reviews)
        average = total / len(reviews)
        return max(0, min(5, round(average * 2) / 2))  # Round to nearest 0.5

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
   

# models.py
from django.contrib.auth import get_user_model

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
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')  
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"{self.user.email}'s cart: {self.product.name} x{self.quantity}"

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