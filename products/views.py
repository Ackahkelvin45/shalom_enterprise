from django.shortcuts import render

# Create your views here.


def products(request):
    return render (request,"products/all_products.html")


def products_detail(request):
    return render (request,"products/product_detail.html")