import time
import math
import shopify
from .models import ShopifyStore, Product, Variant, InventoryAdjustmentHistory


class Operations:
    def __init__(self, myshopify_domain):
        self._myshopify_domain = myshopify_domain
        try:
            self._user = ShopifyStore.objects.get(myshopify_domain=self._myshopify_domain)
        except Exception as e:
            raise e

        self._token, self._url = self._user.access_token, self._user.myshopify_domain
        self._count_products = self._count_variants = 0

    def activate_session(self):
        shopify_session = shopify.Session(self._url, '2019-04', self._token)
        shopify.ShopifyResource.activate_session(shopify_session)

    def clear_session(self):
        shopify.ShopifyResource.clear_session()

    def count_products(self):
        self._count_products = shopify.Product.count()
        return self._count_products

    def count_variants(self):
        self._count_variants = shopify.Variant.count()
        return self._count_variants

    def get_user(self):
        return self._user

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
        print('Took about %ss' % math.ceil((time.time() - tic)))

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
        print('Took about %ss' % math.ceil((time.time() - tic)))

    def webhook_inventory_adjustment(self, inventory_item_id, adjustment, updated_at):
        try:
            variant = Variant.objects.get(inventory_item_id=inventory_item_id, product__store_id=self._user.id)
            inventory_adjustment = InventoryAdjustmentHistory()
            inventory_adjustment.variant = variant
            inventory_adjustment.updated_at = updated_at
            inventory_adjustment.qty = adjustment
            inventory_adjustment.adjustment = adjustment - variant.qty
            inventory_adjustment.save()
            variant.qty = adjustment
            variant.save()
        except Exception as e:
            print(e)
            pass

    def __str__(self):
        return "Shopify store: %s" % self._user.myshopify_domain
