import django_tables2 as tables
from shopify_app.models import Product, Variant, InventoryAdjustmentHistory
from django.urls import reverse
from django.utils.html import format_html


class ProductTable(tables.Table):
    no_image = "https://cdn.shopify.com/s/assets/" \
               "no-image-2048-5e88c1b20e087fb7bbe9a3771824e743c244f437e4f8ba93bbf7b11b53f7824c_thumb.gif"
    image = tables.TemplateColumn(template_name='home/product_image.html',
                                  verbose_name='', extra_context={'no_image': no_image})
    title = tables.Column(linkify=("home:product-detail", [tables.A("product_id")]), verbose_name='Product')

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap.html"
        fields = ["image", "title", "type", "vendor"]


class ProductDetailTable(tables.Table):
    qty = tables.Column(verbose_name="Inventory")
    title = tables.Column(verbose_name='Variant')

    def render_title(self, value, record):
        product = Product.objects.get(store=record.store, product_id=record.product_id)
        title = product.title
        if value != 'Default Title':
            title = f'{product.title} - {value}'
        url_params = {"product_id": product.product_id, "variant_id": record.variant_id}
        url = reverse("home:inventory-adjustment-history-list", kwargs=url_params)
        content = f'<a href={url}>{title}</a>'
        return format_html(content)

    class Meta:
        model = Variant
        template_name = "django_tables2/bootstrap.html"
        fields = ["title", "sku", "qty"]


class InventoryAdjustmentHistoryTable(tables.Table):
    updated_at = tables.Column(verbose_name='Date', attrs={'td': {'id': 'qty_check'}})
    qty = tables.Column(verbose_name='Quantity')

    class Meta:
        model = InventoryAdjustmentHistory
        template_name = "django_tables2/bootstrap.html"
        fields = ["updated_at", "adjustment", "qty"]
