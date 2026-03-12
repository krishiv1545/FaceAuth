from django.urls import path
from .views import superadmin_dashboard, create_organization, organizations_view


urlpatterns = [
    path("superadmin-dashboard/", superadmin_dashboard, name="superadmin_dashboard"),
    path("create-organization/", create_organization),
    path("organizations/", organizations_view, name="organizations_view"),
]