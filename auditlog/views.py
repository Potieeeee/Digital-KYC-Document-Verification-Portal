from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import AuditLog
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
import datetime
from django.utils.dateparse import parse_date

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
    # Allow Admin, Manager and Reviewer to access audit logs/search
    return user.groups.filter(name__in=["Admin", "Manager", "Reviewer"]).exists()

@login_required
@user_passes_test(is_admin_or_compliance)
def audit_logs_view(request):
    logs = AuditLog.objects.all()

    # Quick combined query
    q = request.GET.get("q", "").strip()
    if q:
        logs = logs.filter(
            Q(actor__username__icontains=q)
            | Q(action__icontains=q)
            | Q(object_type__icontains=q)
            | Q(object_id__icontains=q)
        )

    # Fielded filters
    username = request.GET.get("username", "").strip()
    if username:
        logs = logs.filter(actor__username__icontains=username)

    action = request.GET.get("action", "").strip()
    if action:
        logs = logs.filter(action__icontains=action)

    object_type = request.GET.get("object", "").strip()
    if object_type:
        logs = logs.filter(object_type__icontains=object_type)

    object_id = request.GET.get("id", "").strip()
    if object_id:
        logs = logs.filter(object_id__icontains=object_id)

    # Date filters (expecting YYYY-MM-DD)
    date_from = request.GET.get("date_from", "").strip()
    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            start_dt = timezone.make_aware(datetime.datetime.combine(parsed, datetime.time.min))
            logs = logs.filter(created_at__gte=start_dt)

    date_to = request.GET.get("date_to", "").strip()
    if date_to:
        parsed = parse_date(date_to)
        if parsed:
            end_dt = timezone.make_aware(datetime.datetime.combine(parsed, datetime.time.max))
            logs = logs.filter(created_at__lte=end_dt)

    logs = logs.order_by("-created_at")[:500]

    return render(request, "auditlog/logs.html", {
        "logs": logs,
        "filters": request.GET,
    })