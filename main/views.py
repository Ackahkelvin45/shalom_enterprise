from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from products.models import Product,ProductCategory,Brand,ProductReview
from django.db.models import Prefetch  # Add this import


# Create your views here.


def index_view(request):
    two_days_ago = timezone.now() - timedelta(days=20)
    
    # Get products created in the last 2 days that are active
    products = Product.objects.filter(
        created_at__gte=two_days_ago,
        is_active=True
    ).order_by('-created_at').select_related('category', 'brand').prefetch_related(
        'images',
        Prefetch('reviews', queryset=ProductReview.objects.all())  # Explicit prefetch
    )

    
    # Get top categories for the tab navigation
    top_categories = ProductCategory.objects.filter(is_active=True).order_by('?')[:4]
    brands = Brand.objects.all()[:3]
    
    context = {
        'products': products,
        'top_categories': top_categories,
        "brands": brands
    }
    return render(request, "main/index.html", context)