from django.urls import path
from .views import login_api, login_page


urlpatterns = [
    path("api/login/", login_api),
    path("login/", login_page, name="login_page"),
]