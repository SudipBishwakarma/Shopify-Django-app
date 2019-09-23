from django.urls import path
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.index, name='index'),
    path('design/', views.design, name='design'),
    path('welcome/', views.welcome, name='welcome'),
]