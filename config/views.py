from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def landing(request):
    """Öffentliche Produktseite ohne Daten aus einer Hochzeit."""
    return render(request, "marketing/landing.html")
