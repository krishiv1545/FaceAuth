from django.urls import path
from .views import admin_dashboard, add_student, biometric_capture


urlpatterns = [
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("add-student/", add_student, name="add_student"),
    path("api/biometric-capture/", biometric_capture)
]