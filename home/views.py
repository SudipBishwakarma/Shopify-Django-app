from django.shortcuts import render, reverse
import shopify
from django.utils import timezone
from shopify_app.decorators import shopify_login_required
from django.views.decorators.clickjacking import xframe_options_exempt
from background_task import background, settings
from .models import TestModel
from shopify_app.models import ShopifyStore


# @xframe_options_exempt
def welcome(request):
    return render(request, 'home/welcome.html', {
        'callback_url': "http://%s/login/finalize" % (request.get_host()), 'page_name': 'Welcome'
    })


@shopify_login_required
# @xframe_options_exempt
def index(request):
    products = shopify.Product.find(limit=3)
    orders = shopify.Order.find(limit=3, order="created_at DESC")
    user = ShopifyStore.objects.get(myshopify_domain=request.session['shopify']['shop_url'])
    test_bg_task(request.session['shopify'], verbose_name=f'Test task: {user.myshopify_domain}', creator=user)
    return render(request, 'home/index.html', {
        'products': products,
        'orders': orders,
        'page_name': 'Home'
    })


@background(schedule=30)
def test_bg_task(data):
    token, shop_url = data.values()
    shopify_session = shopify.Session(shop_url, '2019-04', token)
    shopify.ShopifyResource.activate_session(shopify_session)
    products = shopify.Product.find_first()
    data = TestModel()
    data.test_name = products.title
    data.test_data = products.product_type
    data.save()
    shopify.ShopifyResource.clear_session()


# @xframe_options_exempt
def design(request):
    return render(request, 'home/design.html', {'page_name': 'Design'})
