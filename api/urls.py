from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    MyKYCAPIView,
    AdminKYCListAPIView,
    ThirdPartyKYCStatusAPIView,
    BackgroundCheckWebhookAPIView,
)

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("kyc/me/", MyKYCAPIView.as_view(), name="api_my_kyc"),
    path("admin/kyc/", AdminKYCListAPIView.as_view(), name="api_admin_kyc"),
    path("kyc/status/<str:reference_code>/", ThirdPartyKYCStatusAPIView.as_view(), name="api_third_party_status"),
    path("webhook/background-check/", BackgroundCheckWebhookAPIView.as_view(), name="api_background_webhook"),
]