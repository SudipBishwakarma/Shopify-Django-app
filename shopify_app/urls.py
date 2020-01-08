from django.urls import path
from . import views

app_name = 'shopify_app'
urlpatterns = [
    path('', views.login, name='login'),
    path('authenticate/', views.authenticate, name='authenticate'),
    path('finalize/', views.finalize, name='finalize'),
    path('logout/', views.logout, name='logout'),
    path('webhook/inv_levels_update/', views.webhook_inventory_levels_update, name='inventory_levels_update'),
    path('webhook/inv_items_update/', views.webhook_inventory_items_update, name='inventory_items_update'),
    path('webhook/products_update/', views.webhook_products_update, name='products_update'),
    path('webhook/inv_items_delete/', views.webhook_inventory_items_delete, name='inventory_items_delete'),
    path('webhook/products_delete/', views.webhook_products_delete, name='products_delete'),
]
