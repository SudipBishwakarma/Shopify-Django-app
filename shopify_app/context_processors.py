import shopify
from django.conf import settings
from .models import ShopifyStore


def current_shop(request):
    shop = ''
    if hasattr(request, 'session') and 'shopify' in request.session:
        shop_url = request.session['shopify']['shop_url']
        shop = ShopifyStore.objects.get(myshopify_domain=shop_url)
    return {'current_shop': shop, 'api_key': settings.SHOPIFY_API_KEY}
