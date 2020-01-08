from django.urls import path, re_path
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.index, name='index'),
    path('design/', views.design, name='design'),
    path('welcome/', views.welcome, name='welcome'),
    path('products/', views.ProductListView.as_view(), name='products-list'),
    path('products/<int:product_id>/', views.product_detail, name='product-detail'),
    re_path(r'^products/(?P<product_id>\d+)/variants/$', views.url_redirect),
    path('products/<int:product_id>/variants/<int:variant_id>/inventory_history/',
         views.inventory_adjustment_history_list,
         name='inventory-adjustment-history-list'),
    re_path(r'^products/(?P<product_id>\d+)/variants/(?P<variant_id>\d+)',
            views.url_redirect)
]
