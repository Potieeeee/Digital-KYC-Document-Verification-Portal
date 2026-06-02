from .views import bulk_update_view, client_kyc_detail_view, edit_kyc_view
from .views import client_document_detail_view
from django.urls import path
from .views import (
    dashboard_view,
    create_kyc_view,
    reviewer_dashboard_view,
    review_kyc_detail_view,
    client_kyc_detail_view,
)

urlpatterns = [
    path("dashboard/", dashboard_view, name="dashboard"),
    path("kyc/create/", create_kyc_view, name="create_kyc"),
    path("kyc/profile/<int:profile_id>/", client_kyc_detail_view, name="client_kyc_detail"),
    path("reviewer/dashboard/", reviewer_dashboard_view, name="reviewer_dashboard"),
    path("reviewer/kyc/<int:profile_id>/", review_kyc_detail_view, name="review_kyc_detail"),
    path("kyc/edit/<int:profile_id>/", edit_kyc_view, name="edit_kyc"),
    path("kyc/document/<int:document_id>/", client_document_detail_view, name="client_document_detail"),
    path("manager/bulk-update/", bulk_update_view, name="bulk_update"),
]
