from django.shortcuts import render, reverse
import shopify
from django.utils import timezone
from shopify_app.decorators import shopify_login_required
from django.views.decorators.clickjacking import xframe_options_exempt
# from .models import TestModel, FirstRun
from .helpers import first_run
from shopify_app.models import ShopifyStore
from shopify_app.tasks import test_bg_task


# @xframe_options_exempt
def welcome(request):
    return render(request, 'home/welcome.html', {
        'callback_url': "http://%s/login/finalize" % (request.get_host()), 'page_name': 'Welcome'
    })


@shopify_login_required
# @xframe_options_exempt
def index(request):
    store_url = request.session['shopify']['shop_url']
    products = shopify.Product.find(limit=3)
    orders = shopify.Order.find(limit=3, order="created_at DESC")
    user = ShopifyStore.objects.get(myshopify_domain=store_url)

    if first_run(store_url):
        test_bg_task(request.session['shopify'], verbose_name=f'Test task: {user.myshopify_domain}', creator=user)

    return render(request, 'home/index.html', {
        'products': products,
        'orders': orders,
        'page_name': 'Home'
    })


# @xframe_options_exempt
def design(request):
    return render(request, 'home/design.html', {'page_name': 'Design'})
