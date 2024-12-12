from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Comment
from cart.forms import CartAddProductForm
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import CommentForm


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    # Поиск по товарам  
    search_query = request.GET.get('search', None)

    # Фильтрация по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Сортировка
    sort_by = request.GET.get('sort_by')

    try:
        if min_price:
            min_price = float(min_price)
        if max_price:
            max_price = float(max_price)
    except ValueError:
        min_price = None
        max_price = None
    
    if min_price and max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)   

    # Поиск товаров
    if search_query:
        products = products.filter(  
            Q(name__icontains=search_query) 
            |
            Q(slug__icontains=search_query)
        )
        
    # Фильтрация по категории
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Сортировка по цене
    if sort_by == 'price_asc':
        products = products.order_by('price')  # По возрастанию цены
    elif sort_by == 'price_desc':
        products = products.order_by('-price')  # По убыванию цены

    # Пагинация
    paginator = Paginator(products, 6)  # 6 товаров на страницу
    page_number = request.GET.get('page')  # Получаем номер страницы из запроса
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'page_obj': page_obj,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    
    return render(request, 'shop/product/list.html', context=context) 


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    comments = product.comments.all()  # Получаем все комментарии к товару
    cart_product_form = CartAddProductForm()

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.product = product
                comment.user = request.user
                comment.save()
                return redirect('shop:product_detail', id=product.id, slug=product.slug)
        else:
            return redirect('login')  # Редирект на страницу входа, если пользователь не авторизован
    else:
        form = CommentForm()

    return render(request, 'shop/product/detail.html', {
        'product': product,
        'comments': comments,
        'cart_product_form': cart_product_form,
        'form': form,  # Передача формы комментария в контекст
    })