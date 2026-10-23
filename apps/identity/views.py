import time

from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import SignInForm
from .throttling import allow_login_attempt


class SignInView(LoginView):
    template_name = "identity/login.html"
    authentication_form = SignInForm
    redirect_authenticated_user = False

    def post(self, request, *args, **kwargs):
        if not allow_login_attempt(
            request.POST.get("username", ""), request.META.get("REMOTE_ADDR", "unknown")
        ):
            return render(request, "identity/rate_limited.html", status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        now = int(time.time())
        self.request.session["authenticated_at"] = now
        self.request.session["last_activity_at"] = now
        return response


@require_POST
def sign_out(request):
    logout(request)
    return redirect("landing")
