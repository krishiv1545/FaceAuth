from django.urls import path
from .views import admin_dashboard, add_student, biometric_capture, add_student_api, recognize_face, create_event_log, student_activity_view


urlpatterns = [
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("add-student/", add_student, name="add_student"),
    path("api/biometric-capture/", biometric_capture),
    path("api/add-student/", add_student_api),
    path("api/recognize-face/", recognize_face),
    path("api/create-event-log/", create_event_log),
    path("student-activity/", student_activity_view, name="student_activity"),
]