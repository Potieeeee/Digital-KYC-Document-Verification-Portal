from django.urls import path
from .views import audit_logs_view, client_audit_logs_view, mark_notifications_seen_view

urlpatterns = [
    path("audit/logs/", audit_logs_view, name="audit_logs"),
    path("audit/my-logs/", client_audit_logs_view, name="audit_my_logs"),
    path("notifications/mark-seen/", mark_notifications_seen_view, name="mark_notifications_seen"),
]