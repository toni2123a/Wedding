from django.urls import include, path

from apps.identity.views import SignInView, sign_out
from apps.tenancy.views import health, wedding_dashboard, wedding_list

from .views import landing

urlpatterns = [
    path("health/", health, name="health"),
    path("anmelden/", SignInView.as_view(), name="login"),
    path("abmelden/", sign_out, name="logout"),
    path("", landing, name="landing"),
    path("planung/", wedding_list, name="wedding-list"),
    path("hochzeiten/<uuid:wedding_id>/", wedding_dashboard, name="wedding-dashboard"),
    path("hochzeiten/<uuid:wedding_id>/aufgaben/", include("apps.planning.urls")),
]
