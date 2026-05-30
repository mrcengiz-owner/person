from django.conf import settings
from django.shortcuts import redirect


class GirisZorunluMiddleware:
    """Giriş yapılmamış istekleri login sayfasına yönlendirir."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.login_path = settings.LOGIN_URL

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        if path.startswith("/admin"):
            return self.get_response(request)

        static_url = settings.STATIC_URL
        if static_url and path.startswith(static_url):
            return self.get_response(request)

        login_paths = {self.login_path, self.login_path.rstrip("/")}
        if path in login_paths or path.rstrip("/") in login_paths:
            return self.get_response(request)

        next_param = request.get_full_path()
        return redirect(f"{self.login_path}?next={next_param}")
