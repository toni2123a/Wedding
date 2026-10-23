"""Prüft den laufenden lokalen HTTP-Stack mit künstlichen Konten, ohne Daten anzulegen."""

import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://localhost:18080"


def get(opener, path):
    return opener.open(BASE + path, timeout=10)  # noqa: S310


def run():
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    with get(opener, "/") as response:
        body = response.read().decode()
        assert response.status == 200
        assert response.geturl() == BASE + "/"
        assert "Mehr Vorfreude." in body
        assert "Mara &amp; Jonas" not in body
        assert 'href="/planung/"' in body
    with get(opener, "/anmelden/") as response:
        assert response.status == 200
        assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
        assert "no-store" in response.headers["Cache-Control"]
    token = next(cookie.value for cookie in cookies if cookie.name == "wedding_local_csrf")
    password = (ROOT / "secrets" / "local" / "demo_password").read_text(encoding="utf-8").strip()
    form = urllib.parse.urlencode(
        {
            "username": "mara@demo.invalid",
            "password": password,
            "csrfmiddlewaretoken": token,
        }
    ).encode()
    with opener.open(BASE + "/anmelden/", data=form, timeout=10) as response:  # noqa: S310
        body = response.read().decode()
        assert response.status == 200
        assert response.geturl() == BASE + "/planung/"
        assert "Mara &amp; Jonas" in body
        assert "Lea &amp; Emil" not in body

    own_id = uuid5(NAMESPACE_URL, "https://example.invalid/wedding-local-demo/wedding-a")
    other_id = uuid5(NAMESPACE_URL, "https://example.invalid/wedding-local-demo/wedding-b")
    with get(opener, f"/hochzeiten/{own_id}/aufgaben/") as response:
        assert "Einladungen abstimmen" in response.read().decode()
    try:
        get(opener, f"/hochzeiten/{other_id}/")
    except urllib.error.HTTPError as error:
        assert error.code == 404
    else:
        raise AssertionError("Fremde Hochzeit war über HTTP sichtbar.")
    with get(opener, "/health/") as response:
        assert response.status == 200
    print("HTTP-Prüfung bestanden: Landingpage, Anmeldung, Planung und Mandantentrennung.")


if __name__ == "__main__":
    run()
