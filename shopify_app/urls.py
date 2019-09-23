from django.urls import path
from . import views

app_name = 'shopify_app'
urlpatterns = [
    path('', views.login, name='login'),
    path('authenticate/', views.authenticate, name='authenticate'),
    path('finalize/', views.finalize, name='finalize'),
    path('logout/', views.logout, name='logout'),
]