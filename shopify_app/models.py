from django.db import models


class ShopifyStore(models.Model):
    """Model representing shopify stores which have installed this app."""
    name = models.CharField(max_length=100, help_text='Shopify store name.', null=True, blank=True)
    myshopify_domain = models.CharField(max_length=100, help_text='Shopify store domain.', unique=True)
    email = models.EmailField(max_length=100, help_text='Store email address.', null=True, blank=True)
    shop_owner = models.CharField(max_length=100, help_text='Shopify store owner name.', null=True, blank=True)
    country_name = models.CharField(max_length=100, help_text='Store location.', null=True, blank=True)
    access_token = models.CharField(max_length=100, help_text='Permanent token received from shopify.')
    date_installed = models.DateTimeField(help_text='App installation date.', null=True, blank=True)

    def __str__(self):
        """String representation for model object."""
        return self.name


class Product(models.Model):
    """Model representing products fetched from shopify store."""
    store = models.ForeignKey('ShopifyStore', on_delete=models.CASCADE, help_text='ID from ShopifyStore models id.')
    product_id = models.BigIntegerField(verbose_name='product ID', help_text='Shopify product id.')
    title = models.CharField(max_length=200, help_text='Product title', null=True, blank=True)
    vendor = models.CharField(max_length=200, help_text='Product vendor.', null=True, blank=True)
    type = models.CharField(max_length=200, help_text='Product type', null=True, blank=True)
    image = models.CharField(max_length=300, help_text='Product image', null=True, blank=True)

    def __str__(self):
        """String representation for model object."""
        return self.title


class Variant(models.Model):
    """Model representing variant product belonging to the main product."""
    store = models.ForeignKey('ShopifyStore', on_delete=models.CASCADE, help_text='Shopify store id.')
    variant_id = models.BigIntegerField('variant ID', help_text='Variant product from shopify store.')
    product_id = models.BigIntegerField('product ID', help_text='Parent product of variant.', null=True, blank=True)
    title = models.CharField(max_length=200, help_text='Variant title', null=True, blank=True)
    price = models.FloatField(help_text='Variant product price.')
    sku = models.CharField(max_length=30, help_text='Variant SKU.', null=True, blank=True)
    qty = models.IntegerField(default=0, help_text='Variant quantity')
    inventory_management = models.BooleanField(help_text='Inventory Managed', default=False, null=True, blank=True)
    inventory_item_id = models.BigIntegerField(help_text='Variant inventory item id')

    def __str__(self):
        return self.title


class InventoryAdjustmentHistory(models.Model):
    """Model representing inventory adjustment history of shopify variant products."""
    variant = models.ForeignKey('Variant', on_delete=models.CASCADE, help_text='Variant primary key.')
    updated_at = models.DateTimeField(null=True, blank=True)
    adjustment = models.IntegerField(help_text='Inventory adjustment: new qty from webhook - current qty')
    qty = models.IntegerField(help_text='Current quantity')

    def __str__(self):
        return f'Adjustment: {self.adjustment}'
