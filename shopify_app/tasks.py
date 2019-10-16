import shopify
# from .models import ShopifyStore, Product, Variant, InventoryAdjustmentHistory
from home.models import TestModel
from home.helpers import first_run
from .helpers import ShopifyHelper
from background_task import background


@background(schedule=30)
def test_bg_task(data):
    token, shop_url = data.values()
    shopify_session = shopify.Session(shop_url, '2019-04', token)
    shopify.ShopifyResource.activate_session(shopify_session)
    products = shopify.Product.find_first()
    data = TestModel()
    data.test_name = products.title
    data.test_data = products.product_type
    data.save()
    shopify.ShopifyResource.clear_session()
    print('Done!')
    first_run(shop_url, False)
