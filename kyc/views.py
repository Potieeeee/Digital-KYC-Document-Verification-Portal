from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import hashlib
from django.core.paginator import Paginator
from django.utils import timezone

from .models import KYCDocument, KYCProfile
from .forms import KYCProfileForm, KYCDocumentFormSet, KYCReviewForm
from .services import calculate_kyc_risk
from auditlog.services import create_audit_log


# ============================================================
# ROLE CHECKERS
# ============================================================

def is_staff_reviewer(user):
    return user.groups.filter(name__in=["Reviewer", "Manager", "Admin"]).exists()


def is_manager_or_admin(user):
    return user.groups.filter(name__in=["Manager", "Admin"]).exists()


def is_reviewer_manager_admin(user):
    return user.groups.filter(name__in=["Reviewer", "Manager", "Admin"]).exists()


# ============================================================
# CLIENT DASHBOARD
# ============================================================

@login_required
def dashboard_view(request):
    """
    Client dashboard.
    Reviewers, managers, and admins are redirected to reviewer dashboard.
    """

    if is_reviewer_manager_admin(request.user):
        return redirect("reviewer_dashboard")

    profile = KYCProfile.objects.filter(user=request.user).first()

    return render(request, "kyc/dashboard.html", {
        "profile": profile
    })


# ============================================================
# CLIENT KYC CREATION
# ============================================================

@login_required
def create_kyc_view(request):
    """
    Allows a client to create and submit a KYC profile.
    """

    if is_reviewer_manager_admin(request.user):
        return redirect("reviewer_dashboard")

    existing_profile = KYCProfile.objects.filter(user=request.user).first()

    if existing_profile:
        return redirect("dashboard")

    if request.method == "POST":
        profile_form = KYCProfileForm(request.POST)
        formset = KYCDocumentFormSet(request.POST, request.FILES)

        if profile_form.is_valid() and formset.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.reference_code = f"KYC-{request.user.id:06d}"
            profile.status = "submitted"
            profile.submitted_at = timezone.now()
            profile.save()

            formset.instance = profile
            formset.save()

            # Keep only the newest document per document_type, and cap total to 3
            docs = list(KYCDocument.objects.filter(profile=profile).order_by('-id'))
            kept = []
            seen_types = set()
            for doc in docs:
                if doc.document_type in seen_types:
                    doc.delete()
                else:
                    seen_types.add(doc.document_type)
                    kept.append(doc)

            # If more than 3 distinct types exist, delete the older ones (kept is newest-first)
            if len(kept) > 3:
                for doc in kept[3:]:
                    doc.delete()

            calculate_kyc_risk(profile)

            create_audit_log(
                actor=request.user,
                action="KYC_SUBMITTED",
                object_type="KYCProfile",
                object_id=profile.id,
                metadata={
                    "client": profile.full_name,
                    "status": profile.status,
                    "reference_code": profile.reference_code,
                    "risk_level": profile.risk_level,
                    "risk_score": profile.risk_score,
                },
                request=request
            )

            messages.success(request, "KYC submitted successfully.")
            return redirect("dashboard")

    else:
        profile_form = KYCProfileForm()
        formset = KYCDocumentFormSet()

    return render(request, "kyc/create.html", {
        "profile_form": profile_form,
        "formset": formset
    })


# ============================================================
# REVIEWER DASHBOARD
# ============================================================

@login_required
@user_passes_test(is_staff_reviewer)
def reviewer_dashboard_view(request):
    """
    Reviewer dashboard.
    Shows all KYC applications with filtering and pagination.
    """

    profiles = KYCProfile.objects.all().order_by("-created_at")

    status = request.GET.get("status")
    risk_level = request.GET.get("risk_level")
    search = request.GET.get("search")

    if status:
        profiles = profiles.filter(status=status)

    if risk_level:
        profiles = profiles.filter(risk_level=risk_level)

    if search:
        profiles = profiles.filter(full_name__icontains=search)

    paginator = Paginator(profiles, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "kyc/reviewer_dashboard.html", {
        "page_obj": page_obj,
        "status": status,
        "risk_level": risk_level,
        "search": search,
    })


# ============================================================
# REVIEW KYC DETAIL
# ============================================================

@login_required
@user_passes_test(is_staff_reviewer)
def review_kyc_detail_view(request, profile_id):
    """
    Allows reviewer, manager, or admin to approve, reject,
    or request resubmission of a KYC application.
    """

    profile = get_object_or_404(KYCProfile, id=profile_id)

    if request.method == "POST":
        form = KYCReviewForm(request.POST)

        if form.is_valid():
            old_status = profile.status

            review = form.save(commit=False)
            review.profile = profile
            review.reviewer = request.user
            review.save()

            new_status = review.decision

            profile.status = new_status
            profile.reviewed_at = timezone.now()
            profile.save(update_fields=["status", "reviewed_at"])

            action_map = {
                "approved": "KYC_APPROVED",
                "rejected": "KYC_REJECTED",
                "resubmission_required": "KYC_RESUBMISSION_REQUIRED",
            }

            audit_action = action_map.get(new_status, "KYC_REVIEWED")

            create_audit_log(
                actor=request.user,
                action=audit_action,
                object_type="KYCProfile",
                object_id=profile.id,
                metadata={
                    "client": profile.full_name,
                    "reference_code": profile.reference_code,
                    "old_status": old_status,
                    "new_status": new_status,
                    "decision": review.decision,
                    "remarks": review.remarks,
                    "reviewer": request.user.username,
                },
                request=request
            )

            if new_status == "approved":
                messages.success(request, "KYC application approved successfully.")
            elif new_status == "rejected":
                messages.success(request, "KYC application rejected successfully.")
            elif new_status == "resubmission_required":
                messages.success(request, "KYC application marked for resubmission.")
            else:
                messages.success(request, "KYC decision saved.")

            return redirect("reviewer_dashboard")

    else:
        form = KYCReviewForm()

    return render(request, "kyc/review_detail.html", {
        "profile": profile,
        "form": form,
    })


# ============================================================
# CLIENT KYC DETAIL
# ============================================================

@login_required
def client_kyc_detail_view(request, profile_id):
    """
    Allows a client to view only their own KYC profile.
    Anti-IDOR protection is applied using user=request.user.
    """

    profile = get_object_or_404(
        KYCProfile,
        id=profile_id,
        user=request.user
    )

    return render(request, "kyc/client_detail.html", {
        "profile": profile
    })


# ============================================================
# EDIT CLIENT KYC
# ============================================================

@login_required
def edit_kyc_view(request, profile_id):
    """
    Allows a client to edit only their own KYC profile.
    Anti-IDOR protection is applied using user=request.user.
    """

    if is_reviewer_manager_admin(request.user):
        return redirect("reviewer_dashboard")

    profile = get_object_or_404(
        KYCProfile,
        id=profile_id,
        user=request.user
    )

    if request.method == "POST":
        profile_form = KYCProfileForm(request.POST, instance=profile)
        formset = KYCDocumentFormSet(
            request.POST,
            request.FILES,
            instance=profile
        )

        if profile_form.is_valid() and formset.is_valid():
            old_status = profile.status

            profile_form.save()
            formset.save()

            # Keep only the newest document per document_type, and cap total to 3
            docs = list(KYCDocument.objects.filter(profile=profile).order_by('-id'))
            kept = []
            seen_types = set()
            for doc in docs:
                if doc.document_type in seen_types:
                    doc.delete()
                else:
                    seen_types.add(doc.document_type)
                    kept.append(doc)

            if len(kept) > 3:
                for doc in kept[3:]:
                    doc.delete()

            calculate_kyc_risk(profile)

            create_audit_log(
                actor=request.user,
                action="KYC_UPDATED",
                object_type="KYCProfile",
                object_id=profile.id,
                metadata={
                    "client": profile.full_name,
                    "old_status": old_status,
                    "new_status": profile.status,
                    "risk_level": profile.risk_level,
                    "risk_score": profile.risk_score,
                },
                request=request
            )

            messages.success(request, "KYC updated successfully.")
            return redirect("dashboard")

    else:
        profile_form = KYCProfileForm(instance=profile)
        formset = KYCDocumentFormSet(instance=profile)

    return render(request, "kyc/edit.html", {
        "profile": profile,
        "profile_form": profile_form,
        "formset": formset,
    })


# ============================================================
# CLIENT DOCUMENT DETAIL
# ============================================================

@login_required
def client_document_detail_view(request, document_id):
    """
    Allows a client to view only their own uploaded document.
    Anti-IDOR protection is applied using profile__user=request.user.
    """

    document = get_object_or_404(
        KYCDocument,
        id=document_id,
        profile__user=request.user
    )

    create_audit_log(
        actor=request.user,
        action="CLIENT_VIEWED_DOCUMENT",
        object_type="KYCDocument",
        object_id=document.id,
        metadata={
            "document_type": document.document_type,
            "profile_id": document.profile.id,
        },
        request=request
    )

    return render(request, "kyc/document_detail.html", {
        "document": document
    })


# ============================================================
# MANAGER BULK UPDATE
# ============================================================

@login_required
@user_passes_test(is_manager_or_admin)
def bulk_update_view(request):
    """
    Allows manager or admin to update multiple KYC applications.
    """

    if request.method != "POST":
        return redirect("reviewer_dashboard")

    selected_ids = request.POST.getlist("selected_profiles")
    action = request.POST.get("action")

    allowed_actions = ["approved", "rejected", "resubmission_required"]

    if not selected_ids:
        messages.error(request, "Please select at least one KYC application.")
        return redirect("reviewer_dashboard")

    if action not in allowed_actions:
        messages.error(request, "Invalid action.")
        return redirect("reviewer_dashboard")

    profiles = KYCProfile.objects.filter(id__in=selected_ids)

    action_map = {
        "approved": "BULK_KYC_APPROVED",
        "rejected": "BULK_KYC_REJECTED",
        "resubmission_required": "BULK_KYC_RESUBMISSION_REQUIRED",
    }

    audit_action = action_map.get(action, "BULK_KYC_UPDATE")

    for profile in profiles:
        old_status = profile.status

        profile.status = action
        profile.reviewed_at = timezone.now()
        profile.save(update_fields=["status", "reviewed_at"])

        create_audit_log(
            actor=request.user,
            action=audit_action,
            object_type="KYCProfile",
            object_id=profile.id,
            metadata={
                "client": profile.full_name,
                "reference_code": profile.reference_code,
                "old_status": old_status,
                "new_status": action,
                "updated_by": request.user.username,
            },
            request=request
        )

    messages.success(request, "Bulk update completed.")
    return redirect("reviewer_dashboard")
