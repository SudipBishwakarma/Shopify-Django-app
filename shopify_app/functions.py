import time
import math
import shopify
from .models import ShopifyStore, Product, Variant, InventoryAdjustmentHistory


class UserLocal:
    def __init__(self, myshopify_domain):
        self._myshopify_domain = myshopify_domain
        try:
            self._user = ShopifyStore.objects.get(myshopify_domain=self._myshopify_domain)
        except Exception as e:
            raise e

        token, url = self._user.access_token, self._user.myshopify_domain
        shopify_session = shopify.Session(url, '2019-04', token)
        shopify.ShopifyResource.activate_session(shopify_session)
        self._count_products = shopify.Product.count()
        self._count_variants = shopify.Variant.count()

    def count_products(self):
        return self._count_products

    def count_variants(self):
        return self._count_variants

    def get_user(self):
        return self._user

    def clear_session(self):
        shopify.ShopifyResource.clear_session()

    def bulk_add_products(self):
        """Add products to database."""
        tic = time.time()
        chunk = math.ceil(self._count_products / 250)
        while chunk > 0:
            products = shopify.Product.find(limit=250, page=chunk)
            product_models = [Product(store=self._user,
                                      product_id=product.id,
                                      title=product.title,
                                      vendor=product.vendor,
                                      type=product.product_type,
                                      image=product.image.thumb if product.image else None) for product in products]
            Product.objects.bulk_create(product_models)
            print('chunk added: %s' % chunk)
            chunk -= 1
        print('Took %ss' % math.ceil((time.time() - tic)))

    def bulk_add_variants(self):
        """Add variants to database."""
        tic = time.time()
        chunk = math.ceil(self._count_variants / 250)
        while chunk > 0:
            variants = shopify.Variant.find(limit=250, page=chunk)
            variant_models = [Variant(product=Product.objects.get(product_id=variant.product_id),
                                      variant_id=variant.id,
                                      title=variant.title,
                                      price=variant.price,
                                      sku=variant.sku,
                                      qty=variant.inventory_quantity,
                                      inventory_item_id=variant.inventory_item_id) for variant in variants]
            Variant.objects.bulk_create(variant_models)
            print('chunk added: %s' % chunk)
            chunk -= 1
        print('Took %ss' % math.ceil((time.time() - tic)))

    def __str__(self):
        return "Shopify store: %s" % self.user.myshopify_domain
