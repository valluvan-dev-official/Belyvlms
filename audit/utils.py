import uuid
from django.db import transaction
from django.utils import timezone
from .models import AuditLog


def _meta_from_request(request):
    ip = None
    ua = None
    cid = None
    try:
        ip = request.META.get("REMOTE_ADDR")
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip = xff.split(",")[0].strip()
        ua = request.META.get("HTTP_USER_AGENT")
        cid = request.META.get("HTTP_X_CORRELATION_ID") or request.META.get("HTTP_X_REQUEST_ID")
    except Exception:
        pass
    return ip, ua, cid


def log_event(actor_user_id, actor_role, action_type, entity_type, entity_id=None, old_value=None, new_value=None, source="API", request=None):
    def _create():
        ip, ua, cid = _meta_from_request(request) if request else (None, None, None)
        try:
            AuditLog.objects.create(
                timestamp=timezone.now(),
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                old_value=old_value,
                new_value=new_value,
                source=source,
                ip_address=ip,
                user_agent=ua,
                correlation_id=cid or str(uuid.uuid4()),
            )
        except Exception:
            pass

    try:
        transaction.on_commit(_create)
    except Exception:
        _create()
