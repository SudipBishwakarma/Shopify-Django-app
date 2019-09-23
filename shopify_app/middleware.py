from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import shopify


class ConfigurationError(Exception):
    pass


class LoginProtection(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response
        if not settings.SHOPIFY_API_KEY or not settings.SHOPIFY_API_SECRET:
            raise ConfigurationError("SHOPIFY_API_KEY and SHOPIFY_API_SECRET must be set in settings")
        shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY,
                              secret=settings.SHOPIFY_API_SECRET)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'shop' not in request.session:
            query_string = request.META['QUERY_STRING']
            if query_string and (query_string.find('=') >= 0 and query_string.find('&')):
                shopify_request_header = dict(item.split('=') for item in query_string.split('&'))
                if shopify_request_header.get('shop'):
                    request.session['shop'] = shopify_request_header.get('shop')

        if hasattr(request, 'session') and 'shopify' in request.session:
            shop_url = request.session['shopify']['shop_url']
            token = request.session['shopify']['access_token']
            shopify_session = shopify.Session(shop_url, '2019-04', token)
            shopify.ShopifyResource.activate_session(shopify_session)

    def process_response(self, request, response):
        shopify.ShopifyResource.clear_session()
        return response
