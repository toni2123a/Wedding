import time

from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.urls import Resolver404, resolve

from .context import tenant_context
from .models import Membership


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            wedding_id = resolve(request.path_info).kwargs.get("wedding_id")
        except Resolver404:
            wedding_id = None

        if request.user.is_authenticated:
            now = int(time.time())
            started = request.session.get("authenticated_at")
            last = request.session.get("last_activity_at")
            if (
                started is None
                or last is None
                or now - started >= settings.SESSION_ABSOLUTE_TIMEOUT
                or now - last >= settings.SESSION_IDLE_TIMEOUT
            ):
                logout(request)
            elif now - last >= 60:
                request.session["last_activity_at"] = now

        user_id = request.user.pk if request.user.is_authenticated else None
        with tenant_context(user_id=user_id, wedding_id=wedding_id):
            request.membership = None
            request.wedding = None
            if user_id is not None and wedding_id is not None:
                membership = (
                    Membership.objects.select_related("wedding")
                    .filter(wedding_id=wedding_id, user_id=user_id, is_active=True)
                    .first()
                )
                if membership is None:
                    raise Http404("Diese Hochzeit ist nicht verfügbar.")
                request.membership = membership
                request.wedding = membership.wedding
            response = self.get_response(request)
            if response.streaming:
                raise ImproperlyConfigured(
                    "Streaming benötigt eine gesonderte, vorab geprüfte Berechtigungsgrenze."
                )
            return response
