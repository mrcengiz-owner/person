from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View

from .forms import KullaniciOlusturForm


class GirisView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        from django.utils.http import url_has_allowed_host_and_scheme

        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
        ):
            return next_url
        return str(reverse_lazy("anasayfa"))


def cikis_view(request):
    logout(request)
    messages.info(request, "Oturumunuz kapatıldı.")
    return redirect("giris")


@method_decorator(user_passes_test(lambda u: u.is_superuser), name="dispatch")
class KullaniciListeView(View):
    template_name = "accounts/kullanicilar.html"

    def get(self, request):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return render(
            request,
            self.template_name,
            {
                "kullanicilar": User.objects.order_by("username"),
                "form": KullaniciOlusturForm(),
            },
        )

    def post(self, request):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        form = KullaniciOlusturForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Kullanıcı «{form.cleaned_data['username']}» oluşturuldu.")
            return redirect("kullanicilar")
        return render(
            request,
            self.template_name,
            {
                "kullanicilar": User.objects.order_by("username"),
                "form": form,
            },
        )
