from django.conf import settings
from django.shortcuts import reverse

import hmac
import hashlib
import base64
import json
from time import time
import math

import shopify

from .models import ShopifyStore, Product, Variant, InventoryAdjustmentHistory

SECRET = settings.SHOPIFY_API_SECRET
URL = settings.URL


def verify_webhook(data, hmac_header):
    digest = hmac.new(SECRET.encode('utf-8'), data, hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)

    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))


def inventory_adjustment_history(qty, updated_at, variant):
    """Creates inventory adjustment history per variant inventory adjustment"""
    try:
        obj = InventoryAdjustmentHistory()
        obj.variant = variant
        obj.updated_at = updated_at
        obj.adjustment = qty - variant.qty
        obj.qty = qty
        obj.save()
        print("Inventory History created for variant: %s" % variant.id)
    except Exception as e:
        print(e)


class ShopifyHelper:
    def __init__(self, myshopify_domain):
        self._myshopify_domain = myshopify_domain
        try:
            self._user = ShopifyStore.objects.get(myshopify_domain=self._myshopify_domain)
        except Exception as e:
            raise e

        self._token, self._url = self._user.access_token, self._user.myshopify_domain

    def activate_session(self):
        shopify_session = shopify.Session(self._url, settings.SHOPIFY_API_VERSION, self._token)
        shopify.ShopifyResource.activate_session(shopify_session)

    def clear_session(self):
        shopify.ShopifyResource.clear_session()

    def get_user(self):
        return self._user

    def create_webhook(self):
        """Create webhook for listening events for inventory adjustment, product and variant deletion."""
        def address(name): return f"https://{URL + reverse('shopify_app:' + name)}"
        try:
            webhooks = shopify.Webhook.find()
            if webhooks:
                for _ in webhooks:
                    _.destroy()
            webhook = shopify.Webhook()
            webhook.create({'topic': 'inventory_levels/update', 'address': address('inventory_levels_update')})
            webhook.create({'topic': 'inventory_items/update', 'address': address('inventory_items_update')})
            webhook.create({'topic': 'products/update', 'address': address('products_update')})
            webhook.create({'topic': 'inventory_items/delete', 'address': address('inventory_items_delete')})
            webhook.create({'topic': 'products/delete', 'address': address('products_delete')})
        except Exception as e:
            print(e)

    def inventory_levels_update(self, data):
        inventory_item_id = data.get('inventory_item_id')
        available = data.get('available')
        updated_at = data.get('updated_at')
        try:
            variant, created = Variant.objects.get_or_create(store=self._user, inventory_item_id=inventory_item_id)
            if created:
                client = shopify.GraphQL()
                query = '''
                    query {
                        inventoryItem(id: "gid://shopify/InventoryItem/%s") {
                            variant {
                                id
                                title
                                price
                                sku
                                product {
                                    id
                                    title
                                    vendor
                                    productType
                                    featuredImage {
                                        transformedSrc(maxWidth: 50)
                                    }
                                }
                            }
                        }
                    }
                ''' % inventory_item_id
                result = json.loads(client.execute(query))['data']['inventoryItem']

                variant.variant_id = int(result['variant']['id'].split('/')[-1])
                variant.product_id = int(result['variant']['product']['id'].split('/')[-1])
                variant.title = result['variant']['title']
                variant.price = float(result['variant']['price'])
                variant.sku = result['variant']['sku'].strip()

                inventory_adjustment_history(available, updated_at, variant)

                variant.qty = available
                variant.save()

                product, _created = Product.objects.get_or_create(store=self._user,
                                                                  product_id=variant.product_id)
                image = result['variant']['product']['featuredImage']['transformedSrc']
                if _created:
                    product.title = result['variant']['product']['title']
                    product.vendor = result['variant']['product']['vendor']
                    product.type = result['variant']['product']['productType']
                    product.image = image
                    product.save()
                else:
                    if product.image is None:
                        product.image = image
                        product.save()
            else:
                inventory_adjustment_history(available, updated_at, variant)

                variant.qty = available
                variant.save()

        except Exception as e:
            print(e)

    def inventory_items_update(self, data):
        inventory_item_id = data.get('id')
        sku = data.get('sku').strip()
        tracked = data.get('tracked')
        try:
            variant = Variant.objects.get(store=self._user, inventory_item_id=inventory_item_id)
            variant.sku = sku
            variant.inventory_management = tracked
            variant.save()
            print('Variant %s updated' % variant.id)
        except Exception as e:
            print(e)

    def products_update(self, data):
        product_id = data.get('id')
        title = data.get('title')
        vendor = data.get('vendor')
        p_type = data.get('product_type')
        try:
            product = Product.objects.get(store=self._user, product_id=product_id)
            product.title = title
            product.vendor = vendor
            product.type = p_type

            if product.image is None:
                client = shopify.GraphQL()
                query = '''
                    query {
                        product(id: "gid://shopify/Product/%s") {
                            id
                            featuredImage {
                                transformedSrc(maxWidth: 50)
                            }
                        }
                    }
                ''' % product_id

                result = json.loads(client.execute(query))['data']['product']
                image = result['featuredImage']

                product.image = image

            product.save()
            print("Product updated: %s" % product.id)
        except Exception as e:
            print(e)

    def inventory_items_delete(self, data):
        inventory_item_id = data.get('id')
        try:
            variant = Variant.objects.get(store=self._user, inventory_item_id=inventory_item_id)
            variant.delete()
        except Exception as e:
            print(e)

    def products_delete(self, data):
        product_id = data.get('id')
        try:
            variants = Variant.objects.filter(store=self._user, product_id=product_id)
            variants.delete()
            product = Product.objects.get(store=self._user, product_id=product_id)
            product.delete()
        except Exception as e:
            print(e)

    def bulk_remove(self):
        Product.objects.filter(store=self._user).delete()
        Variant.objects.filter(store=self._user).delete()

    def bulk_add_products(self, limit=250):
        def get_products(page_info='', chunk=1, limit=''):
            """Fetch products recursively."""
            cache = page_info
            products = shopify.Product.find(limit=limit, page_info=page_info)
            product_models = [Product(store=self._user,
                                      product_id=product.id,
                                      title=product.title,
                                      vendor=product.vendor,
                                      type=product.product_type,
                                      image=product.image.thumb if product.image else None,
                                      published=True if product.published_at else False) for product in products]
            Product.objects.bulk_create(product_models)
            cursor = shopify.ShopifyResource.connection.response.headers.get('Link')
            for _ in cursor.split(','):
                if _.find('next') > 0:
                    page_info = _.split(';')[0].strip('<>').split('page_info=')[1]
            print('chunk fetched: %s' % chunk)
            if cache != page_info:
                return get_products(page_info, chunk + 1, limit)
            return None

        tic = time()
        get_products(limit=limit)
        print('Products fetch took about %ss' % math.ceil((time() - tic)))

    def bulk_add_variants(self, limit=250):
        def get_variants(page_info='', chunk=1, limit=''):
            """Fetch variants recursively."""
            cache = page_info
            variants = shopify.Variant.find(limit=250, page_info=page_info)
            variant_models = [Variant(store=self._user,
                                      variant_id=variant.id,
                                      product_id=variant.product_id,
                                      title=variant.title,
                                      price=variant.price,
                                      sku=variant.sku.strip(),
                                      qty=variant.inventory_quantity,
                                      inventory_management=True if variant.inventory_management else False,
                                      inventory_item_id=variant.inventory_item_id) for variant in variants]
            Variant.objects.bulk_create(variant_models)
            cursor = shopify.ShopifyResource.connection.response.headers.get('Link')
            for _ in cursor.split(','):
                if _.find('next') > 0:
                    page_info = _.split(';')[0].strip('<>').split('page_info=')[1]
            print('chunk fetched: %s' % chunk)
            if cache != page_info:
                return get_variants(page_info, chunk + 1, limit)
            return None

        tic = time()
        get_variants(limit=limit)
        print('Variants fetch took about %ss' % math.ceil((time() - tic)))

    def __str__(self):
        return "Shopify store: %s" % self._user.myshopify_domain
