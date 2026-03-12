from django.urls import path
from .views import login_api, login_page, logout_api


urlpatterns = [
    path("api/login/", login_api),
    path("login/", login_page, name="login_page"),
    path("api/logout/", logout_api, name="logout"),
]