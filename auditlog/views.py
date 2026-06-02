from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import AuditLog
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

@login_required
def client_audit_logs_view(request):
    """Show audit logs relevant to the logged-in client (their actions and related KYCProfile events)."""
    profile_id = None
    try:
        profile_id = request.user.kyc_profile.id
    except Exception:
        profile_id = None

    logs = AuditLog.objects.filter(
        Q(actor=request.user) | Q(object_type='KYCProfile', object_id=str(profile_id))
    ).order_by('-created_at')[:200]

    return render(request, "auditlog/logs.html", {
        "logs": logs
    })


@login_required
def mark_notifications_seen_view(request):
    """Store the current time in session so the navbar badge can show unread items only."""
    if request.user.groups.filter(name='Client').exists():
        session_key = 'nav_notifications_seen_client'
    elif request.user.groups.filter(name__in=['Reviewer', 'Manager', 'Admin']).exists():
        session_key = 'nav_notifications_seen_reviewer'
    elif request.user.groups.filter(name='ThirdPartyAPI').exists():
        session_key = 'nav_notifications_seen_thirdparty'
    else:
        session_key = 'nav_notifications_seen_default'

    request.session[session_key] = timezone.now().isoformat()
    request.session.modified = True
    return JsonResponse({'ok': True})

def is_admin_or_compliance(user):
    return user.groups.filter(name__in=["Admin", "Manager"]).exists()

@login_required
@user_passes_test(is_admin_or_compliance)
def audit_logs_view(request):
    logs = AuditLog.objects.all().order_by("-created_at")[:100]

    return render(request, "auditlog/logs.html", {
        "logs": logs
    })