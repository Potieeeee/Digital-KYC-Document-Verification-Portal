from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from auditlog.models import AuditLog
from kyc.models import KYCProfile


def global_nav(request):
    user = getattr(request, 'user', None)
    notifications = []
    unread_count = 0
    profile_id = None

    if not user or not getattr(user, 'is_authenticated', False):
        return {
            'nav_notifications': [],
            'nav_unread_count': 0,
            'nav_pending_count': 0,
            'nav_is_client': False,
            'nav_is_reviewer': False,
            'nav_is_thirdparty': False,
            'nav_user_profile_id': None,
        }

    # attempt to find a linked profile id for client-based linking
    try:
        profile_id = user.kyc_profile.id
    except Exception:
        profile_id = None

    # Client: build actionable notifications from AuditLog
    if user.groups.filter(name='Client').exists():
        logs = AuditLog.objects.filter(
            Q(actor=user) | Q(object_type='KYCProfile', object_id=str(profile_id))
        ).order_by('-created_at')[:5]

        seen_raw = request.session.get('nav_notifications_seen_client')
        seen_at = None
        if seen_raw:
            try:
                seen_at = timezone.datetime.fromisoformat(seen_raw)
                if timezone.is_naive(seen_at):
                    seen_at = timezone.make_aware(seen_at, timezone.get_current_timezone())
            except Exception:
                seen_at = None

        for l in logs:
            label = l.action.replace('_', ' ').title()
            # append reference code when present
            ref = l.metadata.get('reference_code') if isinstance(l.metadata, dict) else None
            if ref:
                label = f"{label} · {ref}"

            url = None
            if l.object_type == 'KYCProfile' and l.object_id and profile_id and str(l.object_id) == str(profile_id):
                try:
                    url = reverse('client_kyc_detail', args=[profile_id])
                except Exception:
                    url = None
            elif l.object_type == 'KYCDocument' and l.object_id:
                try:
                    url = reverse('client_document_detail', args=[int(l.object_id)])
                except Exception:
                    url = None

            notifications.append({
                'label': label,
                'url': url,
                'created_at': l.created_at,
            })

        unread_count = AuditLog.objects.filter(
            Q(actor=user) | Q(object_type='KYCProfile', object_id=str(profile_id))
        ).filter(created_at__gt=seen_at).count() if seen_at else AuditLog.objects.filter(
            Q(actor=user) | Q(object_type='KYCProfile', object_id=str(profile_id))
        ).count()

    # Reviewer / Manager / Admin: show recently submitted profiles (actionable links)
    elif user.groups.filter(name__in=['Reviewer', 'Manager', 'Admin']).exists():
        pending_qs = KYCProfile.objects.filter(status='submitted').order_by('-submitted_at')
        seen_raw = request.session.get('nav_notifications_seen_reviewer')
        seen_at = None
        if seen_raw:
            try:
                seen_at = timezone.datetime.fromisoformat(seen_raw)
                if timezone.is_naive(seen_at):
                    seen_at = timezone.make_aware(seen_at, timezone.get_current_timezone())
            except Exception:
                seen_at = None

        unread_count = pending_qs.filter(submitted_at__gt=seen_at).count() if seen_at else pending_qs.count()
        notifications = []
        for p in pending_qs[:5]:
            notifications.append({
                'label': f"{p.full_name} · {p.reference_code}",
                'url': reverse('review_kyc_detail', args=[p.id]),
                'created_at': p.submitted_at,
            })

    # Third-party API: show audit events for the user (structured)
    elif user.groups.filter(name='ThirdPartyAPI').exists():
        logs = AuditLog.objects.filter(actor=user).order_by('-created_at')[:5]
        seen_raw = request.session.get('nav_notifications_seen_thirdparty')
        seen_at = None
        if seen_raw:
            try:
                seen_at = timezone.datetime.fromisoformat(seen_raw)
                if timezone.is_naive(seen_at):
                    seen_at = timezone.make_aware(seen_at, timezone.get_current_timezone())
            except Exception:
                seen_at = None

        for l in logs:
            label = l.action.replace('_', ' ').title()
            ref = l.metadata.get('reference_code') if isinstance(l.metadata, dict) else None
            if ref:
                label = f"{label} · {ref}"

            url = None
            if l.object_type == 'KYCProfile' and l.object_id:
                try:
                    url = reverse('client_kyc_detail', args=[int(l.object_id)])
                except Exception:
                    url = None
            elif l.object_type == 'KYCDocument' and l.object_id:
                try:
                    url = reverse('client_document_detail', args=[int(l.object_id)])
                except Exception:
                    url = None

            notifications.append({
                'label': label,
                'url': url,
                'created_at': l.created_at,
            })

        unread_count = AuditLog.objects.filter(actor=user).filter(created_at__gt=seen_at).count() if seen_at else AuditLog.objects.filter(actor=user).count()

    return {
        'nav_notifications': notifications,
        'nav_unread_count': unread_count,
        'nav_pending_count': unread_count,
        'nav_is_client': user.groups.filter(name='Client').exists(),
        'nav_is_reviewer': user.groups.filter(name__in=['Reviewer','Manager','Admin']).exists(),
        'nav_is_thirdparty': user.groups.filter(name='ThirdPartyAPI').exists(),
        'nav_user_profile_id': profile_id,
    }
