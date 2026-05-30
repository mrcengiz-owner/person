from django.urls import path
from django.views.generic import RedirectView

from finans import views as finans_views

from . import views
from .models import IslemTipi

urlpatterns = [
    path("", views.AnasayfaView.as_view(), name="anasayfa"),
    path("personel/", views.PersonelListeView.as_view(), name="personel_liste"),
    path("personel/yeni/", views.PersonelFormView.as_view(), name="personel_yeni"),
    path("personel/<int:pk>/", views.PersonelDetayView.as_view(), name="personel_detay"),
    path(
        "personel/<int:pk>/modal/",
        views.PersonelDetayModalView.as_view(),
        name="personel_detay_modal",
    ),
    path("personel/<int:pk>/duzenle/", views.PersonelFormView.as_view(), name="personel_duzenle"),
    path(
        "muhasebe/",
        RedirectView.as_view(pattern_name="muhasebe_islemler", permanent=False),
    ),
    path("muhasebe/islemler/", views.MuhasebeIslemlerView.as_view(), name="muhasebe_islemler"),
    path("muhasebe/masraflar/", views.MasraflarView.as_view(), name="masraflar"),
    path("muhasebe/masraflar/yeni/", views.OdemeKayitView.as_view(), name="odeme_kayit"),
    path(
        "muhasebe/islem/<int:pk>/duzenle/",
        views.IslemDuzenleView.as_view(),
        name="islem_duzenle",
    ),
    path(
        "muhasebe/avans/",
        views.IslemFormView.as_view(),
        {"tip": IslemTipi.AVANS},
        name="muhasebe_avans",
    ),
    path(
        "muhasebe/maas/",
        views.IslemFormView.as_view(),
        {"tip": IslemTipi.MAAS},
        name="muhasebe_maas",
    ),
    path(
        "muhasebe/mutabakatlar/",
        finans_views.MutabakatlarView.as_view(),
        name="mutabakatlar",
    ),
    path("muhasebe/kasalar/", finans_views.KasalarView.as_view(), name="kasalar"),
]
