import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import LoginBucket

WINDOW = timedelta(minutes=15)


def _key(kind, value):
    return hmac.new(
        settings.SECRET_KEY.encode(),
        f"wedding-login-v1:{kind}:{value}".encode(),
        hashlib.sha256,
    ).hexdigest()


def allow_login_attempt(email, ip):
    now = timezone.now()
    limits = [(_key("account", email.strip().casefold()), 10), (_key("ip", ip), 30)]
    # Eine feste Reihenfolge vermeidet gegensätzlich gesperrte Zeilen.
    with transaction.atomic():
        buckets = []
        for key, limit in sorted(limits):
            bucket, _ = LoginBucket.objects.get_or_create(key=key, defaults={"started_at": now})
            bucket = LoginBucket.objects.select_for_update().get(pk=bucket.pk)
            if now - bucket.started_at >= WINDOW:
                bucket.attempts = 0
                bucket.started_at = now
            buckets.append((bucket, limit))
        if any(bucket.attempts >= limit for bucket, limit in buckets):
            return False
        for bucket, _ in buckets:
            bucket.attempts += 1
            bucket.save(update_fields=["attempts", "started_at"])
    return True
