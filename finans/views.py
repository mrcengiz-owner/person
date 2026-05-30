from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from .forms import KasaForm, KasaHareketForm
from .kur import kur_bilgisi
from .models import Kasa, KasaHareket
from .services import kasa_detay_context, kasa_liste_ozet


class KasalarView(View):
    def get(self, request):
        ozet = kasa_liste_ozet()
        return render(
            request,
            "finans/kasalar.html",
            {
                "ozet": ozet,
                "kasalar": ozet["kasalar"],
                "toplam_try": ozet["toplam_try"],
            },
        )


class KasaYeniView(View):
    template_name = "finans/kasa_form.html"

    def get(self, request):
        form = KasaForm()
        return render(
            request,
            self.template_name,
            {"form": form, "baslik": "Yeni Kasa"},
        )

    def post(self, request):
        form = KasaForm(request.POST)
        if form.is_valid():
            kasa = form.save(commit=False)
            kasa.olusturan = request.user
            kasa.guncelleyen = request.user
            kasa.save()
            messages.success(request, f"“{kasa.ad}” kasası oluşturuldu.")
            return redirect("kasa_detay", pk=kasa.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "baslik": "Yeni Kasa"},
        )


class KasaDuzenleView(View):
    template_name = "finans/kasa_form.html"

    def get(self, request, pk):
        kasa = get_object_or_404(Kasa, pk=pk)
        form = KasaForm(instance=kasa)
        return render(
            request,
            self.template_name,
            {"form": form, "baslik": "Kasa Düzenle", "kasa": kasa},
        )

    def post(self, request, pk):
        kasa = get_object_or_404(Kasa, pk=pk)
        form = KasaForm(request.POST, instance=kasa)
        if form.is_valid():
            kasa = form.save(commit=False)
            kasa.guncelleyen = request.user
            kasa.save()
            messages.success(request, "Kasa bilgileri güncellendi.")
            return redirect("kasa_detay", pk=kasa.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "baslik": "Kasa Düzenle", "kasa": kasa},
        )


class KasaDetayView(View):
    def get(self, request, pk):
        kasa = get_object_or_404(Kasa, pk=pk)
        return render(
            request,
            "finans/kasa_detay.html",
            kasa_detay_context(kasa),
        )


class KasaHareketYeniView(View):
    template_name = "finans/kasa_hareket_form.html"

    def get(self, request, pk):
        kasa = get_object_or_404(Kasa, pk=pk)
        form = KasaHareketForm(kasa=kasa)
        kur_info = kur_bilgisi(kasa.para_birimi, timezone.localdate())
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "kasa": kasa,
                "kur_info": kur_info,
                "baslik": "Para Ekle / Çıkar",
            },
        )

    def post(self, request, pk):
        kasa = get_object_or_404(Kasa, pk=pk)
        form = KasaHareketForm(kasa=kasa, data=request.POST)
        if form.is_valid():
            hareket = form.save(commit=False)
            hareket.kaydeden = request.user
            hareket.guncelleyen = request.user
            hareket.save()
            tip = hareket.get_tip_display()
            messages.success(request, f"{tip} kaydı eklendi.")
            return redirect("kasa_detay", pk=kasa.pk)
        kur_info = kur_bilgisi(
            kasa.para_birimi,
            form.cleaned_data.get("tarih") if form.is_bound else timezone.localdate(),
        )
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "kasa": kasa,
                "kur_info": kur_info,
                "baslik": "Para Ekle / Çıkar",
            },
        )


class KasaHareketSilView(View):
    def post(self, request, pk):
        hareket = get_object_or_404(KasaHareket, pk=pk)
        kasa_pk = hareket.kasa_id
        hareket.delete()
        messages.success(request, "Hareket silindi.")
        return redirect("kasa_detay", pk=kasa_pk)


class KurOnizlemeView(View):
    """AJAX: tarih + para birimi için kur ve TL karşılığı."""

    def get(self, request):
        para_birimi = request.GET.get("para_birimi", "")
        tarih_str = request.GET.get("tarih", "")
        tutar_str = request.GET.get("tutar", "")

        if not para_birimi:
            return JsonResponse({"basari": False, "hata": "Para birimi gerekli."}, status=400)

        try:
            tarih = datetime.strptime(tarih_str, "%Y-%m-%d").date() if tarih_str else timezone.localdate()
        except ValueError:
            return JsonResponse({"basari": False, "hata": "Geçersiz tarih."}, status=400)

        info = kur_bilgisi(para_birimi, tarih)
        tutar_try = None
        if info["kur_try"] and tutar_str:
            try:
                tutar = Decimal(tutar_str.replace(",", "."))
                tutar_try = str((tutar * Decimal(info["kur_try"])).quantize(Decimal("0.01")))
            except (InvalidOperation, ValueError):
                pass

        info["tutar_try"] = tutar_try
        return JsonResponse(info)


class MutabakatlarView(View):
    """Müşteri mutabakatları — şablon formatına göre genişletilecek."""

    def get(self, request):
        return render(
            request,
            "finans/mutabakatlar.html",
            {
                "beklenen_alanlar": [
                    "Müşteri / firma bilgisi",
                    "Yapılan iş / proje tanımı",
                    "Dönem veya tarih aralığı",
                    "Tutarlar (borç, alacak, bakiye)",
                    "Ödeme durumu",
                    "İlişkili kasa",
                ],
            },
        )
