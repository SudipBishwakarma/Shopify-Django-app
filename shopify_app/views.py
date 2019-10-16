from django.shortcuts import render, redirect
from django.conf import settings
import shopify
from django.template import RequestContext
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from shopify_app.helpers import verify_webhook

import json
from django.middleware.csrf import CsrfViewMiddleware
from .models import ShopifyStore
from django.utils import timezone
from shopify_app.helpers import ShopifyHelper


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
    shopify_session = shopify.Session(shop_url, '2019-04', token)
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
        permission_url = shopify.Session(shop.strip(), '2019-04').create_permission_url(scope, redirect_uri)
        return redirect(permission_url)

    return redirect(_return_address(request))


def finalize(request):
    shop_url = request.GET.get('shop')
    try:
        shopify_session = shopify.Session(shop_url, '2019-04')
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
def shopify_webhook(request):
    if request.method == 'POST' and verify_webhook(request.body, request.headers.get('X-Shopify-Hmac-Sha256')):
        print(request.headers.get('X-Shopify-Topic'))
        shop_url = request.headers.get('X-Shopify-Shop-Domain')
        data = json.loads(request.body)
        store = ShopifyHelper(shop_url)
        store.activate_session()
        inventory_item_id = data.get('inventory_item_id')
        adjustment = data.get('available')
        updated_at = data.get('updated_at')
        store.webhook_inventory_adjustment(inventory_item_id, adjustment, updated_at)

    return render(request, 'shopify_app/webhook.html')
