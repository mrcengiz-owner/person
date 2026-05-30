from django.urls import path

from . import views

urlpatterns = [
    path("giris/", views.GirisView.as_view(), name="giris"),
    path("cikis/", views.cikis_view, name="cikis"),
    path("kullanicilar/", views.KullaniciListeView.as_view(), name="kullanicilar"),
]
