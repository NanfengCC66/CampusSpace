from django.urls import path
from .views import HomeView, RegisterView, login_view, logout_view

app_name = 'users'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]