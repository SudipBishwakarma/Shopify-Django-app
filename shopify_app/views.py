from django.shortcuts import render, redirect
from django.conf import settings
import shopify
from django.template import RequestContext
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import json
from .models import ShopifyStore
from django.utils import timezone
from .helpers import verify_webhook, ShopifyHelper
from . import tasks


def index(request):
    context = {'SHOPIFY_API_SCOPE': settings.SHOPIFY_API_SCOPE, 'request': RequestContext(request)}
    return render(request, 'index.html', context)


def _return_address(request):
    return request.session.get('return_to') or reverse('home:index')


def login(request):
    # Ask user for their ${shop}.myshopify.com address

    # If the ${shop}.myshopify.com address is already provided in the URL,
    # just skip to authenticate

    if request.session.get('shopify'):
        return redirect(_return_address(request))

    if 'shop' in request.session:
        request.GET = request.GET.copy()
        request.GET['shop'] = request.session['shop']

    if request.GET.get('shop'):
        return authenticate(request)

    return render(request, 'shopify_app/login.html')


def create_shopify_store_user(data):
    shop_url, token = data.values()
    shopify_session = shopify.Session(shop_url, settings.SHOPIFY_API_VERSION, token)
    shopify.ShopifyResource.activate_session(shopify_session)
    user, created = ShopifyStore.objects.get_or_create(myshopify_domain=shop_url)
    if created:
        shop = shopify.Shop.current()
        user.myshopify_domain = shop_url
        user.access_token = token
        user.date_installed = timezone.now()
        user.email = shop.email
        user.shop_owner = shop.shop_owner
        user.country_name = shop.country_name
        user.name = shop.name
        user.save()
    else:
        if user.access_token != token:
            user.access_token = token
    shopify.ShopifyResource.clear_session()


def authenticate(request):
    shop = request.GET.get('shop') or request.POST.get('shop')
    if shop:
        scope = settings.SHOPIFY_API_SCOPE
        redirect_uri = request.build_absolute_uri(reverse('shopify_app:finalize'))
        permission_url = shopify.Session(shop.strip(), settings.SHOPIFY_API_VERSION).create_permission_url(scope, redirect_uri)
        return redirect(permission_url)

    return redirect(_return_address(request))


def finalize(request):
    shop_url = request.GET.get('shop')
    try:
        shopify_session = shopify.Session(shop_url, settings.SHOPIFY_API_VERSION)
        request.session['shopify'] = {
            "shop_url": shop_url,
            "access_token": shopify_session.request_token(request.GET)
        }
        create_shopify_store_user(request.session['shopify'])
    except Exception:
        messages.error(request, "Could not log in to Shopify store.")
        return redirect(reverse('shopify_app:login'))

    messages.info(request, "Logged in to shopify store.")
    response = redirect(_return_address(request))
    request.session.pop('return_to', None)
    return response


def logout(request):
    request.session.pop('shopify', None)
    request.session.pop('shop', None)
    messages.info(request, "Successfully logged out.")

    return redirect(reverse('shopify_app:login'))


@csrf_exempt
def webhook_inventory_levels_update(request):
    if request.method == 'POST' and verify_webhook(request.body, request.headers.get('X-Shopify-Hmac-Sha256')):
        topic = request.headers.get('X-Shopify-Topic')
        shop_url = request.headers.get('X-Shopify-Shop-Domain')
        data = json.loads(request.body)
        print(data)
        data.update({'X-Shopify-Shop-Domain': shop_url})
        if topic == 'inventory_levels/update':
            tasks.inventory_levels_update(data,
                                          verbose_name=f'Task for inventory_levels/update webhook event: {shop_url}')
    return render(request, 'shopify_app/webhook.html')


@csrf_exempt
def webhook_inventory_items_update(request):
    if request.method == 'POST' and verify_webhook(request.body, request.headers.get('X-Shopify-Hmac-Sha256')):
        topic = request.headers.get('X-Shopify-Topic')
        shop_url = request.headers.get('X-Shopify-Shop-Domain')
        data = json.loads(request.body)
        print(data)
        data.update({'X-Shopify-Shop-Domain': shop_url})
        if topic == 'inventory_items/update':
            tasks.inventory_items_update(data,
                                         verbose_name=f'Task for inventory_levels/update webhook event: {shop_url}')
    return render(request, 'shopify_app/webhook.html')


@csrf_exempt
def webhook_products_update(request):
    if request.method == 'POST' and verify_webhook(request.body, request.headers.get('X-Shopify-Hmac-Sha256')):
        topic = request.headers.get('X-Shopify-Topic')
        shop_url = request.headers.get('X-Shopify-Shop-Domain')
        data = json.loads(request.body)
        print(data)
        data.update({'X-Shopify-Shop-Domain': shop_url})
        if topic == 'products/update':
            tasks.products_update(data, verbose_name=f'Task for inventory_levels/update webhook event: {shop_url}')
    return render(request, 'shopify_app/webhook.html')


@csrf_exempt
def webhook_inventory_items_delete(request):
    if request.method == 'POST' and verify_webhook(request.body, request.headers.get('X-Shopify-Hmac-Sha256')):
        topic = request.headers.get('X-Shopify-Topic')
        shop_url = request.headers.get('X-Shopify-Shop-Domain')
        data = json.loads(request.body)
        print(data)
        data.update({'X-Shopify-Shop-Domain': shop_url})
        if topic == 'inventory_items/delete':
            tasks.inventory_items_delete(data,
                                         verbose_name=f'Task for inventory_levels/update webhook event: {shop_url}')
    return render(request, 'shopify_app/webhook.html')


@csrf_exempt
def webhook_products_delete(request):
    if request.method == 'POST' and verify_webhook(request.body, request.headers.get('X-Shopify-Hmac-Sha256')):
        topic = request.headers.get('X-Shopify-Topic')
        shop_url = request.headers.get('X-Shopify-Shop-Domain')
        data = json.loads(request.body)
        print(data)
        data.update({'X-Shopify-Shop-Domain': shop_url})
        if topic == 'products/delete':
            tasks.products_delete(data, verbose_name=f'Task for inventory_levels/update webhook event: {shop_url}')
    return render(request, 'shopify_app/webhook.html')
