import pytest
from django.conf import settings
from django.test import Client

from apps.identity.models import LoginBucket


def test_sign_in_is_required():
    response = Client().get("/planung/")
    assert response.status_code == 302
    assert response.url.startswith("/anmelden/?next=")


def test_successful_login_uses_argon2_and_server_session(client_for):
    client = client_for("mara@demo.invalid")
    response = client.get("/planung/")
    assert response.status_code == 200
    assert "Mara &amp; Jonas" in response.content.decode()
    cookie = client.cookies[settings.SESSION_COOKIE_NAME]
    assert cookie["httponly"]
    assert not cookie["domain"]
    assert cookie["samesite"] == "Lax"


def test_credentials_are_case_insensitive_for_email(demo_password):
    response = Client().post(
        "/anmelden/",
        {
            "username": "MARA@DEMO.INVALID",
            "password": demo_password,
        },
    )
    assert response.status_code == 302


@pytest.mark.parametrize("email", ["mara@demo.invalid", "nicht-vorhanden@demo.invalid"])
def test_invalid_credentials_have_the_same_public_message(email):
    response = Client().post("/anmelden/", {"username": email, "password": "falsches-passwort"})
    assert response.status_code == 200
    assert "E-Mail-Adresse oder Passwort ist nicht korrekt." in response.content.decode()


def test_external_return_url_does_not_create_an_open_redirect(demo_password):
    response = Client().post(
        "/anmelden/",
        {
            "username": "mara@demo.invalid",
            "password": demo_password,
            "next": "https://evil.invalid/",
        },
    )
    assert response.status_code == 302
    assert response.url == "/planung/"


def test_login_rate_limit_is_persistent_and_does_not_store_email_addresses():
    client = Client()
    for _ in range(10):
        assert (
            client.post(
                "/anmelden/",
                {
                    "username": "mara@demo.invalid",
                    "password": "falsches-passwort",
                },
            ).status_code
            == 200
        )
    assert (
        client.post(
            "/anmelden/",
            {
                "username": "mara@demo.invalid",
                "password": "falsches-passwort",
            },
        ).status_code
        == 429
    )
    assert LoginBucket.objects.count() == 2
    assert all(
        len(key) == 64 and "@" not in key
        for key in LoginBucket.objects.values_list("key", flat=True)
    )


def test_login_rejects_missing_csrf_token(demo_password):
    client = Client(enforce_csrf_checks=True)
    response = client.post(
        "/anmelden/", {"username": "mara@demo.invalid", "password": demo_password}
    )
    assert response.status_code == 403


def test_cross_origin_login_is_rejected_even_with_a_valid_csrf_token(demo_password):
    client = Client(enforce_csrf_checks=True)
    client.get("/anmelden/")
    token = client.cookies[settings.CSRF_COOKIE_NAME].value
    response = client.post(
        "/anmelden/",
        {
            "username": "mara@demo.invalid",
            "password": demo_password,
            "csrfmiddlewaretoken": token,
        },
        HTTP_ORIGIN="https://andere-subdomain.invalid",
    )
    assert response.status_code == 403


def test_logout_requires_post(client_for):
    client = client_for("mara@demo.invalid")
    assert client.get("/abmelden/").status_code == 405
    assert client.post("/abmelden/").status_code == 302
    assert client.get("/planung/").status_code == 302


@pytest.mark.parametrize("age,idle", [(12 * 3600 + 1, 0), (0, 3601)])
def test_expired_sessions_cannot_continue(client_for, expire_session, age, idle):
    client = client_for("mara@demo.invalid")
    expire_session(client, age=age, idle=idle)
    assert client.get("/planung/").status_code == 302


def test_security_headers_and_no_public_cache():
    response = Client().get("/anmelden/")
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert "no-store" in response["Cache-Control"]
    assert "frame-ancestors 'none'" in response["Content-Security-Policy"]
    assert "unsafe-inline" not in response["Content-Security-Policy"]


def test_untrusted_host_is_rejected():
    assert Client().get("/health/", HTTP_HOST="evil.invalid").status_code == 400
