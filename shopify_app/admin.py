from django.contrib import admin
from .models import ShopifyStore


@admin.register(ShopifyStore)
class ShopifyStoreAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Store Info', {'fields': ['name',
                                   'myshopify_domain',
                                   'email',
                                   'shop_owner',
                                   'country_name',
                                   'access_token',
                                   'date_installed']}),
    ]
    readonly_fields = ('access_token', 'date_installed')
    list_display = ('name', 'myshopify_domain', 'shop_owner', 'country_name', 'date_installed')
    list_filter = ('myshopify_domain', 'date_installed')
    search_fields = ('myshopify_domain',)
