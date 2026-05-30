from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .forms import (
    MESAI_ONAYARLARI,
    AvansForm,
    MaasOdemeForm,
    MuhasebeIslemForm,
    OdemeKayitForm,
    PersonelForm,
)
from .audit import islem_kaydi_ozeti
from .models import IslemTipi, MuhasebeIslem, Personel
from .services import (
    maas_tarihi_hesapla,
    maasa_kalan_gun,
    mesai_gorsel_bilgi,
    personel_detay_context,
    son_islemler,
    yaklasan_maas_personelleri,
)


class AnasayfaView(View):
    def get(self, request):
        aktif_sayisi = Personel.objects.filter(aktif=True).count()
        uyarılar = yaklasan_maas_personelleri()
        context = {
            "aktif_personel_sayisi": aktif_sayisi,
            "maas_uyarilari": uyarılar,
            "maas_uyari_gun": getattr(settings, "MAAS_UYARI_GUN", 3),
            "son_islemler": son_islemler(),
            "bugun": timezone.localdate(),
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


class MuhasebeIslemlerView(View):
    template_name = "personel/muhasebe_islemler.html"
    sayfa_boyutu = 25

    def get(self, request):
        qs = (
            MuhasebeIslem.objects.exclude(tip=IslemTipi.MASRAF)
            .select_related("personel", "kaydeden", "guncelleyen")
            .order_by("-tarih", "-olusturulma")
        )

        tip = request.GET.get("tip", "")
        if tip in (IslemTipi.AVANS, IslemTipi.MAAS):
            qs = qs.filter(tip=tip)

        personel_id = request.GET.get("personel", "")
        secili_personel_pk = None
        if personel_id.isdigit():
            secili_personel_pk = int(personel_id)
            qs = qs.filter(personel_id=secili_personel_pk)

        arama = request.GET.get("q", "").strip()
        if arama:
            qs = qs.filter(
                Q(personel__ad_soyad__icontains=arama)
                | Q(aciklama__icontains=arama)
            )

        sayim = qs.aggregate(
            toplam=Count("id"),
            avans_adet=Count("id", filter=Q(tip=IslemTipi.AVANS)),
            maas_adet=Count("id", filter=Q(tip=IslemTipi.MAAS)),
            toplam_avans=Sum("tutar", filter=Q(tip=IslemTipi.AVANS)),
            toplam_maas=Sum("tutar", filter=Q(tip=IslemTipi.MAAS)),
        )

        paginator = Paginator(qs, self.sayfa_boyutu)
        sayfa = paginator.get_page(request.GET.get("page"))

        querystring = request.GET.copy()
        if "page" in querystring:
            del querystring["page"]

        return render(
            request,
            self.template_name,
            {
                "islemler": sayfa,
                "personeller": Personel.objects.order_by("ad_soyad"),
                "secili_tip": tip,
                "secili_personel": secili_personel_pk,
                "arama": arama,
                "toplam_kayit": sayim["toplam"],
                "avans_adet": sayim["avans_adet"],
                "maas_adet": sayim["maas_adet"],
                "toplam_avans": sayim["toplam_avans"] or 0,
                "toplam_maas": sayim["toplam_maas"] or 0,
                "filtre_toplam": (sayim["toplam_avans"] or 0) + (sayim["toplam_maas"] or 0),
                "querystring": querystring.urlencode(),
            },
        )


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

        return render(
            request,
            self.get_template(tip),
            {
                "form": form,
                "baslik": self.get_baslik(tip),
                "iptal_url": "muhasebe_islemler",
            },
        )

    def post(self, request, tip, **kwargs):
        form_class = self.get_form_class(tip)
        form = form_class(request.POST)
        if form.is_valid():
            islem = form.save(commit=False)
            islem.kaydeden = request.user
            islem.guncelleyen = request.user
            islem.save()
            messages.success(request, _islem_basarili_mesaj(islem))
            return _islem_yonlendir(request, islem)
        return render(
            request,
            self.get_template(tip),
            {
                "form": form,
                "baslik": self.get_baslik(tip),
                "iptal_url": "muhasebe_islemler",
            },
        )


class MasraflarView(View):
    template_name = "personel/masraflar.html"
    sayfa_boyutu = 25

    def get(self, request):
        qs = MuhasebeIslem.objects.select_related(
            "personel", "kaydeden", "guncelleyen"
        ).order_by("-tarih", "-olusturulma")

        tip = request.GET.get("tip", "")
        if tip in dict(IslemTipi.choices):
            qs = qs.filter(tip=tip)

        personel_id = request.GET.get("personel", "")
        secili_personel_pk = None
        if personel_id.isdigit():
            secili_personel_pk = int(personel_id)
            qs = qs.filter(personel_id=secili_personel_pk)

        arama = request.GET.get("q", "").strip()
        if arama:
            qs = qs.filter(
                Q(personel__ad_soyad__icontains=arama)
                | Q(alici_adi__icontains=arama)
                | Q(aciklama__icontains=arama)
            )

        sayim = qs.aggregate(
            toplam=Count("id"),
            masraf_adet=Count("id", filter=Q(tip=IslemTipi.MASRAF)),
            avans_adet=Count("id", filter=Q(tip=IslemTipi.AVANS)),
            maas_adet=Count("id", filter=Q(tip=IslemTipi.MAAS)),
            toplam_masraf=Sum("tutar", filter=Q(tip=IslemTipi.MASRAF)),
            toplam_avans=Sum("tutar", filter=Q(tip=IslemTipi.AVANS)),
            toplam_maas=Sum("tutar", filter=Q(tip=IslemTipi.MAAS)),
        )

        paginator = Paginator(qs, self.sayfa_boyutu)
        sayfa = paginator.get_page(request.GET.get("page"))

        querystring = request.GET.copy()
        if "page" in querystring:
            del querystring["page"]

        toplam_masraf = sayim["toplam_masraf"] or 0
        toplam_avans = sayim["toplam_avans"] or 0
        toplam_maas = sayim["toplam_maas"] or 0

        return render(
            request,
            self.template_name,
            {
                "islemler": sayfa,
                "personeller": Personel.objects.order_by("ad_soyad"),
                "secili_tip": tip,
                "secili_personel": secili_personel_pk,
                "arama": arama,
                "toplam_kayit": sayim["toplam"],
                "masraf_adet": sayim["masraf_adet"],
                "avans_adet": sayim["avans_adet"],
                "maas_adet": sayim["maas_adet"],
                "toplam_masraf": toplam_masraf,
                "toplam_avans": toplam_avans,
                "toplam_maas": toplam_maas,
                "filtre_toplam": toplam_masraf + toplam_avans + toplam_maas,
                "querystring": querystring.urlencode(),
            },
        )


class OdemeKayitView(View):
    template_name = "personel/odeme_kayit_form.html"

    def _form_context(self, form):
        return {
            "form": form,
            "baslik": "Ödeme / Masraf Kaydı",
            "personel_maaslari": list(
                Personel.objects.filter(aktif=True).values_list("pk", "maas")
            ),
        }

    def get(self, request):
        personel_pk = request.GET.get("personel")
        personel = Personel.objects.filter(pk=personel_pk).first() if personel_pk else None
        tip = request.GET.get("tip", "")
        if tip not in dict(IslemTipi.choices):
            tip = None

        form = OdemeKayitForm(
            initial={"tarih": timezone.localdate()},
            personel=personel,
            tip=tip,
        )
        return render(request, self.template_name, self._form_context(form))

    def post(self, request):
        form = OdemeKayitForm(request.POST)
        if form.is_valid():
            islem = form.save(commit=False)
            islem.kaydeden = request.user
            islem.guncelleyen = request.user
            islem.save()
            messages.success(request, _islem_basarili_mesaj(islem))
            return redirect("masraflar")
        return render(request, self.template_name, self._form_context(form))
