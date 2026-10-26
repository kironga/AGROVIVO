from django.contrib.auth.views import LoginView
from django.urls import reverse


class StaffAwareLoginView(LoginView):
    template_name = "registration/login.html"

    def get_default_redirect_url(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return reverse("dashboard_home")
        return reverse("account")
