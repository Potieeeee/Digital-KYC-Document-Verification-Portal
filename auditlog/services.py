import hashlib
import json
from .models import AuditLog

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]

    return request.META.get("REMOTE_ADDR")


def create_audit_log(actor, action, object_type, object_id, metadata=None, request=None):
    metadata = metadata or {}

    last_log = AuditLog.objects.order_by("-created_at").first()
    previous_hash = last_log.event_hash if last_log else ""

    ip_address = get_client_ip(request) if request else None
    user_agent = request.META.get("HTTP_USER_AGENT", "") if request else ""

    payload = {
        "actor_id": actor.id if actor else None,
        "action": action,
        "object_type": object_type,
        "object_id": str(object_id),
        "metadata": metadata,
        "previous_hash": previous_hash,
    }

    event_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata,
        previous_hash=previous_hash,
        event_hash=event_hash,
    )