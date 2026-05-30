from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .forms import (
    MESAI_ONAYARLARI,
    AvansForm,
    MaasOdemeForm,
    MasrafKayitForm,
    MuhasebeIslemForm,
    OdemeKayitForm,
    PersonelForm,
)
from .audit import islem_kaydi_ozeti
from .models import IslemTipi, MuhasebeIslem, Personel
from .services import (
    DONEM_AYLIK,
    DONEM_TUMU,
    anasayfa_ozet,
    donem_dogrula,
    islem_liste_filtrele,
    islem_liste_query,
    islem_tip_liste_url,
    maas_tarihi_hesapla,
    maasa_kalan_gun,
    mesai_gorsel_bilgi,
    personel_detay_context,
    son_islemler,
    yaklasan_maas_personelleri,
)


class AnasayfaView(View):
    def get(self, request):
        bugun = timezone.localdate()
        aktif_sayisi = Personel.objects.filter(aktif=True).count()
        toplam_personel = Personel.objects.count()
        uyarılar = yaklasan_maas_personelleri()
        ozet = anasayfa_ozet(bugun)
        context = {
            "aktif_personel_sayisi": aktif_sayisi,
            "toplam_personel_sayisi": toplam_personel,
            "maas_uyarilari": uyarılar,
            "maas_uyari_gun": getattr(settings, "MAAS_UYARI_GUN", 3),
            "son_islemler": son_islemler(),
            "bugun": bugun,
            "ozet": ozet,
        }
        return render(request, "personel/anasayfa.html", context)


class PersonelListeView(View):
    def get(self, request):
        personeller = Personel.objects.all()
        bugun = timezone.localdate()
        uyari_gun = getattr(settings, "MAAS_UYARI_GUN", 3)
        liste = []
        for p in personeller:
            kalan = maasa_kalan_gun(p, bugun) if p.aktif else None
            liste.append(
                {
                    "personel": p,
                    "mesai": mesai_gorsel_bilgi(p),
                    "sonraki_maas": maas_tarihi_hesapla(p, bugun) if p.aktif else None,
                    "kalan_gun": kalan,
                    "yaklasiyor": p.aktif and kalan is not None and 0 <= kalan <= uyari_gun,
                }
            )
        return render(
            request,
            "personel/personel_liste.html",
            {"personeller": liste, "bugun": bugun},
        )


class PersonelDetayView(View):
    def get(self, request, pk):
        personel = get_object_or_404(Personel, pk=pk)
        return render(
            request,
            "personel/personel_detay.html",
            personel_detay_context(personel),
        )


class PersonelDetayModalView(View):
    """Liste sayfası pop-up için HTML parçası döner."""

    def get(self, request, pk):
        personel = get_object_or_404(Personel, pk=pk)
        return render(
            request,
            "personel/partials/personel_detay_modal.html",
            personel_detay_context(personel),
        )


class PersonelFormView(View):
    template_name = "personel/personel_form.html"

    def get(self, request, pk=None):
        if pk:
            personel = get_object_or_404(Personel, pk=pk)
            form = PersonelForm(instance=personel)
            baslik = "Personel Düzenle"
        else:
            form = PersonelForm()
            baslik = "Yeni Personel"
        return render(
            request,
            self.template_name,
            self._form_context(form, baslik),
        )

    def _form_context(self, form, baslik):
        return {
            "form": form,
            "baslik": baslik,
            "mesai_onayarlari": MESAI_ONAYARLARI,
        }

    def post(self, request, pk=None):
        if pk:
            personel = get_object_or_404(Personel, pk=pk)
            form = PersonelForm(request.POST, instance=personel)
            baslik = "Personel Düzenle"
        else:
            form = PersonelForm(request.POST)
            baslik = "Yeni Personel"

        if form.is_valid():
            personel = form.save(commit=False)
            if pk:
                personel.guncelleyen = request.user
            else:
                personel.olusturan = request.user
                personel.guncelleyen = request.user
            personel.save()
            messages.success(request, f"{personel.ad_soyad} kaydedildi.")
            return redirect("personel_detay", pk=personel.pk)

        return render(
            request,
            self.template_name,
            self._form_context(form, baslik),
        )


def _islem_basarili_mesaj(islem, eylem="kaydedildi"):
    return f"{islem.alici_goster} — {islem.get_tip_display()} {eylem}."


def _islem_yonlendir(request, islem, varsayilan="muhasebe_islemler"):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
    ):
        return redirect(next_url)
    return redirect(varsayilan)


def _yonlendir_next(request, varsayilan="masraflar"):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
    ):
        return redirect(next_url)
    return redirect(varsayilan)


class MuhasebeIslemlerView(View):
    template_name = "personel/muhasebe_islemler.html"

    def get(self, request):
        context = islem_liste_filtrele(request, varsayilan_donem=DONEM_TUMU)
        return render(request, self.template_name, context)


class IslemDuzenleView(View):
    template_name = "personel/islem_duzenle.html"

    def get(self, request, pk):
        islem = get_object_or_404(
            MuhasebeIslem.objects.select_related("personel", "kaydeden", "guncelleyen"),
            pk=pk,
        )
        form = MuhasebeIslemForm(instance=islem)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "islem": islem,
                "kayit_ozeti": islem_kaydi_ozeti(islem.kaydeden, islem.olusturulma),
                "guncelleme_ozeti": islem_kaydi_ozeti(
                    islem.guncelleyen, islem.guncellenme, "Son güncelleyen"
                ),
                "baslik": "İşlem Düzenle",
                "next": request.GET.get("next", ""),
                "iptal_url": "muhasebe_islemler",
            },
        )

    def post(self, request, pk):
        islem = get_object_or_404(MuhasebeIslem, pk=pk)
        form = MuhasebeIslemForm(request.POST, instance=islem)
        if form.is_valid():
            islem = form.save(commit=False)
            islem.guncelleyen = request.user
            islem.save()
            messages.success(request, _islem_basarili_mesaj(islem, "güncellendi"))
            return _islem_yonlendir(request, islem)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "islem": islem,
                "kayit_ozeti": islem_kaydi_ozeti(islem.kaydeden, islem.olusturulma),
                "guncelleme_ozeti": islem_kaydi_ozeti(
                    islem.guncelleyen, islem.guncellenme, "Son güncelleyen"
                ),
                "baslik": "İşlem Düzenle",
                "next": request.POST.get("next", ""),
                "iptal_url": "muhasebe_islemler",
            },
        )


class IslemFormView(View):
    def get_form_class(self, tip):
        if tip == IslemTipi.AVANS:
            return AvansForm
        if tip == IslemTipi.MAAS:
            return MaasOdemeForm
        return MuhasebeIslemForm

    def get_template(self, tip):
        if tip == IslemTipi.AVANS:
            return "personel/avans_form.html"
        return "personel/maas_form.html"

    def get_baslik(self, tip):
        return "Avans Kaydı" if tip == IslemTipi.AVANS else "Maaş Ödemesi"

    def _form_context(self, form, tip, donem):
        return {
            "form": form,
            "baslik": self.get_baslik(tip),
            "iptal_url": islem_tip_liste_url(tip),
            "secili_donem": donem,
        }

    def get(self, request, tip, **kwargs):
        personel_pk = request.GET.get("personel")
        personel = None
        if personel_pk:
            personel = Personel.objects.filter(pk=personel_pk).first()

        form_class = self.get_form_class(tip)
        form_kwargs = {}
        if personel and tip == IslemTipi.MAAS:
            form_kwargs["personel"] = personel
        form = form_class(initial={"tarih": timezone.localdate()}, **form_kwargs)
        if personel:
            form.fields["personel"].initial = personel

        donem = donem_dogrula(request.GET.get("donem"), varsayilan=DONEM_AYLIK)
        return render(
            request,
            self.get_template(tip),
            self._form_context(form, tip, donem),
        )

    def post(self, request, tip, **kwargs):
        form_class = self.get_form_class(tip)
        form = form_class(request.POST)
        donem = donem_dogrula(
            request.POST.get("donem") or request.GET.get("donem"),
            varsayilan=DONEM_AYLIK,
        )
        if form.is_valid():
            islem = form.save(commit=False)
            islem.kaydeden = request.user
            islem.guncelleyen = request.user
            islem.save()
            messages.success(request, _islem_basarili_mesaj(islem))
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)
            liste_url = islem_tip_liste_url(tip)
            return redirect(f"{reverse(liste_url)}?{islem_liste_query(request, donem=donem)}")
        return render(
            request,
            self.get_template(tip),
            self._form_context(form, tip, donem),
        )


class MasraflarView(View):
    template_name = "personel/masraflar.html"

    def get(self, request):
        context = islem_liste_filtrele(
            request,
            varsayilan_donem=DONEM_AYLIK,
            sabit_tip=IslemTipi.MASRAF,
        )
        return render(request, self.template_name, context)


class AvanslarView(View):
    template_name = "personel/avanslar.html"

    def get(self, request):
        context = islem_liste_filtrele(
            request,
            varsayilan_donem=DONEM_AYLIK,
            sabit_tip=IslemTipi.AVANS,
        )
        return render(request, self.template_name, context)


class MaaslarView(View):
    template_name = "personel/maaslar.html"

    def get(self, request):
        context = islem_liste_filtrele(
            request,
            varsayilan_donem=DONEM_AYLIK,
            sabit_tip=IslemTipi.MAAS,
        )
        context["maas_uyarilari"] = yaklasan_maas_personelleri()
        context["maas_uyari_gun"] = getattr(settings, "MAAS_UYARI_GUN", 3)
        return render(request, self.template_name, context)


class IslemSilView(View):
    def post(self, request, pk):
        islem = get_object_or_404(MuhasebeIslem, pk=pk)
        mesaj = f"{islem.alici_goster} — {islem.get_tip_display()} silindi."
        varsayilan = islem_tip_liste_url(islem.tip)
        islem.delete()
        messages.success(request, mesaj)
        return _yonlendir_next(request, varsayilan=varsayilan)


class OdemeKayitView(View):
    template_name = "personel/odeme_kayit_form.html"

    def _form_context(self, form, donem):
        return {
            "form": form,
            "baslik": "Masraf Kaydı",
            "secili_donem": donem,
        }

    def get(self, request):
        donem = donem_dogrula(request.GET.get("donem"), varsayilan=DONEM_AYLIK)
        form = MasrafKayitForm(initial={"tarih": timezone.localdate()})
        return render(request, self.template_name, self._form_context(form, donem))

    def post(self, request):
        donem = donem_dogrula(
            request.POST.get("donem") or request.GET.get("donem"),
            varsayilan=DONEM_AYLIK,
        )
        form = MasrafKayitForm(request.POST)
        if form.is_valid():
            islem = form.save(commit=False)
            islem.kaydeden = request.user
            islem.guncelleyen = request.user
            islem.save()
            messages.success(request, _islem_basarili_mesaj(islem))
            return redirect(f"{reverse('masraflar')}?{islem_liste_query(request, donem=donem)}")
        return render(request, self.template_name, self._form_context(form, donem))
