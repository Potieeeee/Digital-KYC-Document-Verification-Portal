from django.urls import path
from .views import register_view
from .views import profile_view

urlpatterns = [
    path("register/", register_view, name="register"),
    path("profile/", profile_view, name="profile"),
    path("accounts/profile/", profile_view, name="accounts_profile"),
]