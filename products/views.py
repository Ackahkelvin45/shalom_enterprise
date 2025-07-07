from django.shortcuts import render
from .models import ProductCategory, Product, ProductImage,Brand, Wishlist, Cart,ProductReview,HotDeal
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
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ProductCategory
from .serializer import ProductCategorySerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from datetime import datetime
from django.db.models import Prefetch



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
    
    # Get active products that are NOT in active hot deals
    now = timezone.now()
    active_deal_products = HotDeal.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).values_list('product_id', flat=True)
    
    products = Product.objects.filter(
        is_active=True
    ).exclude(
        id__in=active_deal_products
    ).prefetch_related('images')
    
    brands = Brand.objects.all()
    
    # Get all filter parameters from request
    category_ids = request.GET.getlist('category')
    brand_ids = request.GET.getlist('brand')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    search_query = request.GET.get('search', '').strip()
    page_size = request.GET.get('page_size', 4)  # Default to 4 items per page
    
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
    paginator = Paginator(products, page_size)
    
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
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'images',
            'reviews',
            Prefetch('reviews', queryset=ProductReview.objects.select_related('user'), to_attr='prefetched_reviews')
        ),
        slug=slug,
        is_active=True
    )
    
    # Get active hot deal for this product if exists
    hot_deal = HotDeal.objects.filter(
        product=product,
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).first()
    
    # Get main image
    main_image = product.images.filter(is_main=True).first() or product.images.first()
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).prefetch_related('images')[:4]
    
    # Calculate discount percentage
    current_price = hot_deal.current_price if hot_deal else product.discount_price or product.price
    discount_percent = None
    
    if hot_deal and hot_deal.discount_percentage:
        discount_percent = hot_deal.discount_percentage
    elif product.discount_price and product.price:
        discount_percent = 100 - (product.discount_price / product.price * 100)
        discount_percent = int(round(discount_percent))
    
    reviews = product.reviews.all()
    # In your product_detail view
    reviews = product.reviews.all()
    rating_distribution = {
        5: reviews.filter(rating=5).count(),
        4: reviews.filter(rating=4).count(),
        3: reviews.filter(rating=3).count(),
        2: reviews.filter(rating=2).count(),
        1: reviews.filter(rating=1).count(),
    }
    print(rating_distribution)
    context = {
        'product': product,
        'hot_deal': hot_deal,
        'main_image': main_image,
        'images': product.images.all(),
        'related_products': related_products,
        'discount_percent': discount_percent,
        'current_price': current_price,
        'rating_distribution': rating_distribution,
        'rating_count': reviews.count(),
        'average_rating': product.average_rating,
    }
    return render(request, 'products/product_detail.html', context)

# views.py
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_api(request, product_id=None):
    """
    Enhanced wishlist API with:
    - Better error handling
    - Consistent response format
    - Product details in GET response
    - Hot deal support
    """
    try:
        if request.method == 'GET':
            # Get wishlist items with full product details
            wishlist_items = Wishlist.objects.filter(
                user=request.user
            ).select_related('product').prefetch_related('product__images')
            
            # Check for hot deals
            now = timezone.now()
            hot_deals = {
                deal.product_id: deal.current_price
                for deal in HotDeal.objects.filter(
                    is_active=True,
                    start_date__lte=now,
                    end_date__gte=now,
                    product_id__in=[item.product_id for item in wishlist_items]
                )
            }
            
            data = []
            for item in wishlist_items:
                product = item.product
                current_price = hot_deals.get(product.id, product.discount_price or product.price)
                
                data.append({
                    'id': item.id,
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'slug': product.slug,
                        'price': str(product.price),
                        'current_price': str(current_price),
                        'is_hot_deal': product.id in hot_deals,
                        'image': product.images.first().image.url if product.images.first() else None,
                        'category': product.category.name if product.category else None
                    },
                    'added_at': item.added_at
                })
            
            return Response(data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            # Validate product_id
            if not product_id:
                return Response(
                    {'success': False, 'error': 'Product ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get product with hot deal info
            product = get_object_or_404(Product, pk=product_id)
            hot_deal = HotDeal.objects.filter(
                product=product,
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).first()
            
            # Create wishlist item
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                product=product
            )
            
            response_data = {
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'current_price': str(hot_deal.current_price if hot_deal else (product.discount_price or product.price)),
                    'is_hot_deal': hot_deal is not None
                }
            }
            
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(response_data, status=status_code)

        elif request.method == 'DELETE':
            if not product_id:
                return Response(
                    {'success': False, 'error': 'Product ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            deleted_count, _ = Wishlist.objects.filter(
                user=request.user,
                product_id=product_id
            ).delete()
            
            if deleted_count > 0:
                return Response(
                    {'success': True, 'message': 'Product removed from wishlist'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'success': False, 'error': 'Product not found in wishlist'},
                status=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return Response(
            {'success': False, 'error': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_api(request, product_id=None):
    serializer_context = {'request': request}
    
    if request.method == 'GET':
            cart_items = Cart.objects.filter(user=request.user).select_related('product')
            
            # Calculate totals
            total_items = cart_items.count()
            subtotal = float(sum(float(item.price_used) * item.quantity for item in cart_items))
            total_discount = float(sum(
                (float(item.product.price) - float(item.price_used)) * item.quantity 
                for item in cart_items 
                if float(item.price_used) < float(item.product.price)
            ))
            grand_total = subtotal
            
            serializer = CartSerializer(cart_items, many=True, context=serializer_context)
            
            response_data = {
                'items': serializer.data,
                'summary': {
                    'total_items': total_items,
                    'subtotal': float(subtotal),
                    'total_discount': float(total_discount),
                    'grand_total': float(grand_total),
                    'total_savings': float(total_discount)
                }
            }
            return Response(response_data)
        
    elif request.method == 'POST':
        # Add to cart with hot deal pricing
        product = get_object_or_404(Product, id=product_id)
        
        # Check for active hot deal
        hot_deal = HotDeal.objects.filter(
            product=product,
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
        
        # Determine the price to use
        price = (
            hot_deal.current_price 
            if hot_deal 
            else (product.discount_price or product.price)
        )
        
        # Get or create cart item
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={
                'quantity': int(request.data.get('quantity', 1)),
                'price_used': price
            }
        )
        
        # If item already existed, update quantity and price
        if not created:
            cart_item.quantity += int(request.data.get('quantity', 1))
            # Update price in case deal status changed
            cart_item.price_used = price
            cart_item.save()
        
        serializer = CartSerializer(cart_item, context=serializer_context)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method == 'PUT':
        # Update cart item quantity
        if not product_id:
            return Response(
                {'detail': 'Product ID is required for update.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cart_item = get_object_or_404(Cart, user=request.user, product_id=product_id)
        quantity = int(request.data.get('quantity', 1))
        
        if quantity < 1:
            cart_item.delete()
            return Response(
                {'detail': 'Item removed from cart.'}, 
                status=status.HTTP_204_NO_CONTENT
            )
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartSerializer(cart_item, context=serializer_context)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        # Remove item from cart
        if not product_id:
            return Response(
                {'detail': 'Product ID is required for deletion.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cart_item = get_object_or_404(Cart, user=request.user, product_id=product_id)
        cart_item.delete()
        return Response(
            {'detail': 'Product removed from cart.'}, 
            status=status.HTTP_204_NO_CONTENT
        )

    return Response(
        {'detail': 'Method not allowed.'}, 
        status=status.HTTP_405_METHOD_NOT_ALLOWED
    )




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

def show_hotdeals(request):
    # Get all active deals that haven't expired yet
    hot_deals = HotDeal.objects.filter(
        is_active=True,
        end_date__gte=timezone.now()
    ).select_related('product', 'product__category', 'product__brand')
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    selected_categories = request.GET.getlist('category')
    selected_brands = request.GET.getlist('brand')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    selected_discount_ranges = request.GET.getlist('discount_range')
    selected_deal_status = request.GET.getlist('deal_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sort_option = request.GET.get('sort', 'discount_desc')
    page_size = int(request.GET.get('page_size', 20))
    
    # Apply search filter
    if search_query:
        hot_deals = hot_deals.filter(
            Q(product__name__icontains=search_query) |
            Q(product__description__icontains=search_query)
        )
    
    # Apply category filter - safely convert to integers
    if selected_categories:
        try:
            category_ids = [int(cat_id) for cat_id in selected_categories if cat_id.isdigit()]
            if category_ids:
                hot_deals = hot_deals.filter(product__category__id__in=category_ids)
        except (ValueError, TypeError):
            pass
    
    # Apply brand filter - safely convert to integers
    if selected_brands:
        try:
            brand_ids = [int(brand_id) for brand_id in selected_brands if brand_id.isdigit()]
            if brand_ids:
                hot_deals = hot_deals.filter(product__brand__id__in=brand_ids)
        except (ValueError, TypeError):
            pass
    
    # Apply price range filter
    if price_min:
        try:
            hot_deals = hot_deals.filter(current_price__gte=float(price_min))
        except (ValueError, TypeError):
            pass
    
    if price_max:
        try:
            hot_deals = hot_deals.filter(current_price__lte=float(price_max))
        except (ValueError, TypeError):
            pass
    
    # Apply discount range filters
    discount_filters = Q()
    for range in selected_discount_ranges:
        if range == '10-29':
            discount_filters |= Q(discount_percentage__gte=10, discount_percentage__lt=30)
        elif range == '30-49':
            discount_filters |= Q(discount_percentage__gte=30, discount_percentage__lt=50)
        elif range == '50+':
            discount_filters |= Q(discount_percentage__gte=50)
    
    if selected_discount_ranges:
        hot_deals = hot_deals.filter(discount_filters)
    
    # Apply deal status filters
    status_filters = Q()
    for status in selected_deal_status:
        if status == 'ending_soon':
            ending_soon_date = timezone.now() + timedelta(hours=24)
            status_filters |= Q(end_date__lte=ending_soon_date)
        elif status == 'new_deals':
            new_deals_date = timezone.now() - timedelta(days=7)
            status_filters |= Q(start_date__gte=new_deals_date)
    
    if selected_deal_status:
        hot_deals = hot_deals.filter(status_filters)
    
    # Apply date range filter
    if start_date:
        try:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            hot_deals = hot_deals.filter(start_date__gte=start_date)
        except (ValueError, TypeError):
            pass

    if end_date:
        try:
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            hot_deals = hot_deals.filter(end_date__lte=end_date)
        except (ValueError, TypeError):
            pass
    
    # Apply sorting
    if sort_option == 'discount_desc':
        hot_deals = hot_deals.order_by('-discount_percentage')
    elif sort_option == 'price_asc':
        hot_deals = hot_deals.order_by('current_price')
    elif sort_option == 'price_desc':
        hot_deals = hot_deals.order_by('-current_price')
    elif sort_option == 'ending_soon':
        hot_deals = hot_deals.order_by('end_date')
    else:
        hot_deals = hot_deals.order_by('-created_at')
    
    # Get categories with deal counts for sidebar
    categories = ProductCategory.objects.annotate(
        deal_count=Count('products__hot_deals', filter=Q(products__hot_deals__is_active=True) & 
                                      Q(products__hot_deals__end_date__gte=timezone.now()))
    ).filter(deal_count__gt=0)
    
    # Get brands with deal counts for sidebar
    brands = Brand.objects.annotate(
        deal_count=Count('products__hot_deals', filter=Q(products__hot_deals__is_active=True) & 
                                    Q(products__hot_deals__end_date__gte=timezone.now()))
    ).filter(deal_count__gt=0)
    
    # Get top deals with highest discounts for sidebar
    top_deals = hot_deals.order_by('-discount_percentage')[:3]
    
    # Pagination
    paginator = Paginator(hot_deals, page_size)
    page_number = request.GET.get('page')
    try:
        hot_deals_page = paginator.page(page_number)
    except PageNotAnInteger:
        hot_deals_page = paginator.page(1)
    except EmptyPage:
        hot_deals_page = paginator.page(paginator.num_pages)
    
    context = {
        'hot_deals': hot_deals_page,
        'categories': categories,
        'brands': brands,
        'top_deals': top_deals,
        'search_query': search_query,
        'selected_categories': [int(c) for c in selected_categories if c.isdigit()],
        'selected_brands': [int(b) for b in selected_brands if b.isdigit()],
        'price_min': price_min,
        'price_max': price_max,
        'selected_discount_ranges': selected_discount_ranges,
        'selected_deal_status': selected_deal_status,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'products/hot_deals.html', context)

def top_sellers(request):
    categories = ProductCategory.objects.all()
    brands = Brand.objects.all()
    
    # Get top sellers with filtering
    top_sellers = Product.get_top_sellers(limit=20)
    
    # Get all filter parameters from request
    category_ids = request.GET.getlist('category')
    brand_ids = request.GET.getlist('brand')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    search_query = request.GET.get('search', '').strip()
    
    # Apply filters to top sellers
    if category_ids:
        top_sellers = [p for p in top_sellers if str(p.category.id) in category_ids]
    
    if brand_ids:
        top_sellers = [p for p in top_sellers if p.brand and str(p.brand.id) in brand_ids]
    
    if price_min:
        try:
            price_min = float(price_min)
            top_sellers = [p for p in top_sellers if p.discount_price or p.price >= price_min]
        except ValueError:
            pass
    
    if price_max:
        try:
            price_max = float(price_max)
            top_sellers = [p for p in top_sellers if p.discount_price or p.price <= price_max]
        except ValueError:
            pass
    
    if search_query:
        search_query = search_query.lower()
        top_sellers = [p for p in top_sellers 
                      if (p.name and search_query in p.name.lower()) or 
                         (p.description and search_query in p.description.lower())]
    
    context = {
        'top_sellers': top_sellers,
        'categories': categories,
        'brands': brands,
        'title': 'Top Selling Products',
        'selected_categories': [int(c) for c in category_ids if c.isdigit()],
        'selected_brands': [int(b) for b in brand_ids if b.isdigit()],
        'price_min': price_min,
        'price_max': price_max,
        'search_query': search_query,
    }
    return render(request, 'products/top_sellers.html', context)