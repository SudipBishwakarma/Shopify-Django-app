from itertools import islice
import shopify
from .models import ShopifyStore, Product, Variant, InventoryAdjustmentHistory


class UserLocal:
    def __init__(self, myshopify_domain):
        self.myshopify_domain = myshopify_domain
        try:
            self.user = ShopifyStore.objects.get(myshopify_domain=self.myshopify_domain)
        except Exception as e:
            raise e

        token, url = self.user.access_token, self.user.myshopify_domain
        shopify_session = shopify.Session(url, '2019-04', token)
        shopify.ShopifyResource.activate_session(shopify_session)
        self.count_products = shopify.Product.count()
        self.count_variants = shopify.Variant.count()

    def count_products(self):
        return self.count_products

    def count_variants(self):
        return self.count_variants

    def clear_session(self):
        shopify.ShopifyResource.clear_session()

    def bulk_add_products(self, products):
        """Add products to database."""
        for product in products:
            print(product)

    def __str__(self):
        return "Shopify store: %s" % self.user.myshopify_domain
