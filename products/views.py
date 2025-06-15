from django.shortcuts import render
from .models import ProductCategory, Product, ProductImage,Brand, Wishlist, Cart,ProductReview
from django.shortcuts import render, get_object_or_404
from .serializer import ProductSerializer,CartSerializer,WishlistSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



# Create your views here.

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ProductCategory
from .serializer import ProductCategorySerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def categories_json(request):
    categories = ProductCategory.objects.filter(is_active=True, parent__isnull=True)
    serializer = ProductCategorySerializer(
        categories, 
        many=True, 
        context={'request': request}
    )
    return Response({'categories': serializer.data})





def products(request):
    categories = ProductCategory.objects.all()
    products = Product.objects.filter(is_active=True).prefetch_related('images')
    brands = Brand.objects.all()
    
    # Get all filter parameters from request
    category_ids = request.GET.getlist('category')
    brand_ids = request.GET.getlist('brand')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    search_query = request.GET.get('search', '').strip()
    page_size = request.GET.get('page_size', 4)  # Default to 20 items per page
    
    # Apply filters
    if category_ids:
        products = products.filter(category__id__in=category_ids)
    
    if brand_ids:
        products = products.filter(brand__id__in=brand_ids)
    
    if price_min:
        products = products.filter(price__gte=price_min)
    
    if price_max:
        products = products.filter(price__lte=price_max)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, page_size)  # Use the page_size from request
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        "categories": categories,
        "products": products,
        "brands": brands,
        "selected_categories": [int(c) for c in category_ids if c.isdigit()],
        "selected_brands": [int(b) for b in brand_ids if b.isdigit()],
        "price_min": price_min,
        "price_max": price_max,
        "search_query": search_query,
    }
    return render(request, "products/all_products.html", context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get main image (first image marked as main or first available)
    main_image = product.images.filter(is_main=True).first() or product.images.first()
    
    # Get related products (same category, excluding current product)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).prefetch_related('images')[:4]
    
    # Calculate discount percentage if available
    discount_percent = None
    if product.discount_price and product.price:
        discount_percent = 100 - (product.discount_price / product.price * 100)
        discount_percent = int(round(discount_percent))
    
    context = {
        'product': product,
        'main_image': main_image,
        'images': product.images.all(),
        'related_products': related_products,
        'discount_percent': discount_percent,
    }
    return render(request, 'products/product_detail.html', context)










# views.py


# Wishlist Views
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_api(request, product_id=None):
    # Common serializer context setup
    serializer_context = {'request': request}
    
    if request.method == 'GET':
        # Get user's wishlist
        wishlist = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist, many=True, context=serializer_context)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Add to wishlist
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        if created:
            serializer = WishlistSerializer(wishlist_item, context=serializer_context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Product already in wishlist.'}, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        # Remove from wishlist
        wishlist_item = get_object_or_404(Wishlist, user=request.user, product_id=product_id)
        wishlist_item.delete()
        return Response({'detail': 'Product removed from wishlist.'}, status=status.HTTP_204_NO_CONTENT)
    
    
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_api(request, product_id=None):
    # Common serializer context setup
    serializer_context = {'request': request}
    
    if request.method == 'GET':
        cart = Cart.objects.filter(user=request.user).select_related('product')
        serializer = CartSerializer(cart, many=True, context=serializer_context)
        
        # Calculate totals
        total_items = cart.count()
        subtotal = sum(item.total_price for item in cart)
        total_discount = sum(item.total_discount for item in cart)
        grand_total = subtotal - total_discount
        
        response_data = {
            'items': serializer.data,
            'summary': {
                'total_items': total_items,
                'subtotal': subtotal,
                'total_discount': total_discount,
                'grand_total': grand_total
            }
        }
        return Response(response_data)

    elif request.method == 'POST':
        # Add to cart
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': request.data.get('quantity', 1)}  # Default to 1 if not provided
        )
        if not created:
            cart_item.quantity += int(request.data.get('quantity', 1))  # Add the requested quantity
            cart_item.save()
        serializer = CartSerializer(cart_item, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method == 'PUT':
        # Update cart item quantity
        cart_item = get_object_or_404(Cart, user=request.user, product_id=product_id)
        quantity = int(request.data.get('quantity', 1))
        
        if quantity < 1:
            cart_item.delete()
            return Response({'detail': 'Item removed from cart.'}, status=status.HTTP_204_NO_CONTENT)
        
        cart_item.quantity = quantity
        cart_item.save()
        serializer = CartSerializer(cart_item, context=serializer_context)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        # Remove from cart
        cart_item = get_object_or_404(Cart, user=request.user, product_id=product_id)
        cart_item.delete()
        return Response({'detail': 'Product removed from cart.'}, status=status.HTTP_204_NO_CONTENT)
    elif request.method == 'DELETE':
        # Remove from cart
        print("delere",product_id)
        cart_item = get_object_or_404(Cart, user=request.user, product_id=product_id)
        print("product_id")
        cart_item.delete()
        return Response({'detail': 'Product removed from cart.'}, status=status.HTTP_204_NO_CONTENT)





@login_required
@require_POST
def submit_review(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        data = json.loads(request.body)
       
        # Create new review (no check for existing reviews)
        review = ProductReview.objects.create(
                product= product,
                user= request.user,
                rating= int(data.get('rating')),
                title=data.get('title'),
                comment=data.get('comment')
            )
       
        
        return JsonResponse({
            'success': True,
            'review': {
                'user': request.user.first_name + ' ' + request.user.last_name,
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'created_at': review.created_at.strftime("%B %d, %Y"),
                'stars': list(review.get_rating_stars()),
                'empty_stars': list(review.get_empty_stars())
            }
        })
        
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)