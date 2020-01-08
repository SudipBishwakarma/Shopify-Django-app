from django.shortcuts import render, reverse, redirect
import shopify
from shopify_app.decorators import shopify_login_required
from django.utils.decorators import method_decorator
from .helpers import first_run
from shopify_app.models import ShopifyStore, Product, Variant, InventoryAdjustmentHistory
from shopify_app.tasks import task_first_run

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from .tables import ProductTable, ProductDetailTable, InventoryAdjustmentHistoryTable
from .filters import ProductFilter


@method_decorator(shopify_login_required, name='dispatch')
class ProductListView(SingleTableMixin, FilterView):
    table_class = ProductTable
    template_name = 'home/product.html'
    filterset_class = ProductFilter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store = None

    def get_filterset_kwargs(self, filterset_class):
        shop_url = self.request.session['shopify']['shop_url']
        self._store = ShopifyStore.objects.get(myshopify_domain=shop_url)
        kwargs = super(ProductListView, self).get_filterset_kwargs(filterset_class)
        kwargs['store'] = self._store
        return kwargs

    def get_queryset(self):
        self.queryset = Product.objects.filter(store_id=self._store)
        return self.queryset


@shopify_login_required
def product_detail(request, product_id=None):
    try:
        store = ShopifyStore.objects.get(myshopify_domain=request.session.get('shopify').get('shop_url'))
        table = ProductDetailTable(Variant.objects.filter(store=store, product_id=product_id))
        return render(request, "home/product_detail.html", {"table": table})
    except Exception as e:
        print(e)
        return redirect(reverse('home:products-list'))


@shopify_login_required
def inventory_adjustment_history_list(request, product_id=None, variant_id=None):
    try:
        store = ShopifyStore.objects.get(myshopify_domain=request.session.get('shopify').get('shop_url'))
        variant = Variant.objects.get(store=store, product_id=product_id, variant_id=variant_id)
        table = InventoryAdjustmentHistoryTable(InventoryAdjustmentHistory.objects.filter(variant=variant))
        return render(request, 'home/inventory_history.html', {'table': table})
    except Exception as e:
        print(e)
        return redirect(reverse('home:products-list'))


def url_redirect(request, product_id=None, variant_id=None):
    if variant_id is None:
        url_params = {"product_id": product_id}
        url = reverse("home:product-detail", kwargs=url_params)
    else:
        url_params = {"product_id": product_id, "variant_id": variant_id}
        url = reverse("home:inventory-adjustment-history-list", kwargs=url_params)
    return redirect(url)


# @xframe_options_exempt
def welcome(request):
    return render(request, 'home/welcome.html', {
        'callback_url': "http://%s/login/finalize" % (request.get_host()), 'page_name': 'Welcome'
    })


@shopify_login_required
# @xframe_options_exempt
def index(request):
    store_url = request.session['shopify']['shop_url']
    products = shopify.Product.find(limit=3)
    orders = shopify.Order.find(limit=3, order="created_at DESC")
    user = ShopifyStore.objects.get(myshopify_domain=store_url)

    # if first_run(store_url):
    #     task_first_run(store_url, verbose_name=f'First run task: {user.myshopify_domain}', creator=user)
    #     test_bg_task(store_url, verbose_name=f'Test task: {user.myshopify_domain}', creator=user)

    return render(request, 'home/index.html', {
        'products': products,
        'orders': orders,
        'page_name': 'Home'
    })


# @xframe_options_exempt
def design(request):
    return render(request, 'home/design.html', {'page_name': 'Design'})

