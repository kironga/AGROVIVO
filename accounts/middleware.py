class RoleBasedSessionTimeoutMiddleware:
    """Refresh authenticated sessions with a role-specific idle timeout."""

    CUSTOMER_TIMEOUT_SECONDS = 20 * 60
    STAFF_TIMEOUT_SECONDS = 60 * 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            timeout = self.STAFF_TIMEOUT_SECONDS if user.is_staff else self.CUSTOMER_TIMEOUT_SECONDS
            request.session.set_expiry(timeout)
            request.session.modified = True
        return response
