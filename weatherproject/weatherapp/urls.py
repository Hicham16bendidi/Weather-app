from django.urls import path 
from . import views
from django.contrib import admin


urlpatterns = [
    path('admin/',admin.site.urls),
    path('',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('register/', views.register_view, name='register'),
    path('home/',views.home,name='home'),
    path('preferences/', views.update_preferences, name='update_preferences'),
]
