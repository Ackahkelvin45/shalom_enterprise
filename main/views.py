from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from products.models import Product,ProductCategory,Brand,ProductReview
from django.db.models import Prefetch  # Add this import
from django.db.models import Avg  


# Create your views here.


def index_view(request):
    two_days_ago = timezone.now() - timedelta(days=20)
    
    # Get products created in the last 2 days that are active
    products = Product.objects.filter(
        is_active=True
    ).order_by('-created_at')[:10].select_related('category', 'brand').prefetch_related(
        'images',
        Prefetch('reviews', queryset=ProductReview.objects.all())  # Explicit prefetch
    )
    
    # Get top sellers
    top_sellers = Product.get_top_sellers(limit=6)
    
    # Get top rated products (products with highest average rating)
    top_rated = Product.objects.filter(
        is_active=True,
        reviews__isnull=False
    ).annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating')[:6].select_related('category', 'brand').prefetch_related(
        'images',
        Prefetch('reviews', queryset=ProductReview.objects.all())
    )
    print(top_rated)
    # Get top categories for the tab navigation
    top_categories = ProductCategory.objects.filter(is_active=True).order_by('?')[:4]
    brands = Brand.objects.all()[:3]
    
    context = {
        'products': products,
        'top_categories': top_categories,
        "brands": brands,
        "top_sellers": top_sellers,
        "top_rated": top_rated, 
        'categories':ProductCategory.objects.all()
    
    }
    return render(request, "main/index.html", context)


def Faq_view(request):
    return render(request, "main/faq.html")


def about_view(request):
    return render(request, "main/about.html")