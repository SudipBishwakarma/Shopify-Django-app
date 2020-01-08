from home.helpers import first_run
from .helpers import ShopifyHelper
from background_task import background


@background(schedule=30)
def task_first_run(shop_url):
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.bulk_add_products()
    store.bulk_add_variants()
    store.create_webhook()
    store.clear_session()
    print('Done!')


@background()
def inventory_levels_update(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.inventory_levels_update(data)
    store.clear_session()
    print('Task: `Inv. levels update` completed successfully.')


@background()
def inventory_items_update(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.inventory_items_update(data)
    store.clear_session()
    print('Task: `Inv. items update` completed successfully.')


@background()
def products_update(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.products_update(data)
    store.clear_session()
    print('Task: `Products update` completed successfully.')


@background()
def inventory_items_delete(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.inventory_items_delete(data)
    store.clear_session()
    print('Task: `Inv. items delete` completed successfully.')


@background()
def products_delete(data):
    shop_url = data.get('X-Shopify-Shop-Domain')
    store = ShopifyHelper(shop_url)
    store.activate_session()
    store.products_delete(data)
    store.clear_session()
    print('Task: `Products delete` completed successfully.')
