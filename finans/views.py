from django.views import View
from django.shortcuts import render


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


class KasalarView(View):
    """Kasa tanımları ve bakiyeler — şablon formatına göre genişletilecek."""

    def get(self, request):
        return render(
            request,
            "finans/kasalar.html",
            {
                "beklenen_alanlar": [
                    "Kasa adı (ör. Ana Kasa, Banka)",
                    "Para birimi",
                    "Güncel bakiye",
                    "Giriş / çıkış hareketleri",
                    "Mutabakat ile bağlantı",
                ],
            },
        )
