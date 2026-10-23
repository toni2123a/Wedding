from html.parser import HTMLParser

from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))


def test_home_is_public_product_page_not_login_redirect():
    response = Client().get("/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Mehr Vorfreude." in body
    assert 'href="/planung/"' in body
    assert 'href="/anmelden/"' in body
    assert 'name="password"' not in body


def test_public_page_queries_no_private_wedding_tables_even_when_signed_in(client_for):
    client = client_for("mara@demo.invalid")
    with CaptureQueriesContext(connection) as queries:
        response = client.get("/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Mara" not in body
    assert "Jonas" not in body
    assert "demo.invalid" not in body
    private_tables = ("tenancy_weddings", "tenancy_memberships", "planning_tasks", "audit_events")
    assert not any(table in query["sql"] for query in queries for table in private_tables)


def test_all_marketing_anchors_and_internal_calls_to_action_are_valid():
    client = Client()
    parser = PageLinks()
    parser.feed(client.get("/").content.decode())
    assert parser.links
    assert all(parser.links)
    for link in parser.links:
        if link.startswith("#"):
            assert link[1:] in parser.ids
        elif link.startswith("/"):
            assert client.get(link).status_code in {200, 302}


def test_marketing_future_features_are_identified_as_not_yet_available():
    body = Client().get("/").content.decode()
    assert "geplant und noch nicht verfügbar" in body
    assert "Darstellung mit Beispieldaten" in body


def test_landing_keeps_security_headers_and_does_not_set_a_session():
    response = Client().get("/")
    assert "no-store" in response["Cache-Control"]
    assert "frame-ancestors 'none'" in response["Content-Security-Policy"]
    assert response["X-Content-Type-Options"] == "nosniff"
    assert not response.cookies


def test_logout_returns_to_public_home_and_planning_stays_private(client_for):
    client = client_for("mara@demo.invalid")
    response = client.post("/abmelden/")
    assert response.status_code == 302
    assert response.url == "/"
    assert client.get("/").status_code == 200
    assert client.get("/planung/").status_code == 302
