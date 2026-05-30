(function () {
  const panel = document.getElementById("kur-onizleme");
  if (!panel) return;

  const kurUrl = panel.dataset.kurUrl;
  const paraBirimi = panel.dataset.paraBirimi;
  const kurEl = document.getElementById("kur-deger");
  const tutarTryEl = document.getElementById("tutar-try-deger");
  const kaynakEl = document.getElementById("kur-kaynak");
  const tarihInput = document.querySelector('input[name="tarih"]');
  const tutarInput = document.querySelector('input[name="tutar"]');
  const kurInput = document.querySelector('input[name="kur_try"]');

  function formatTry(value) {
    if (value === null || value === undefined || value === "") return "—";
    const num = Number(String(value).replace(",", "."));
    if (Number.isNaN(num)) return "—";
    return num.toLocaleString("tr-TR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }) + " ₺";
  }

  function formatKur(value) {
    if (!value) return "Kur alınamadı";
    const num = Number(String(value).replace(",", "."));
    if (Number.isNaN(num)) return "Kur alınamadı";
    return (
      "1 " +
      paraBirimi.toUpperCase() +
      " = " +
      num.toLocaleString("tr-TR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4,
      }) +
      " ₺"
    );
  }

  let timer = null;

  function guncelle() {
    const tarih = tarihInput ? tarihInput.value : "";
    const tutar = tutarInput ? tutarInput.value : "";
    const params = new URLSearchParams({
      para_birimi: paraBirimi,
      tarih: tarih,
      tutar: tutar,
    });

    fetch(kurUrl + "?" + params.toString(), {
      headers: { Accept: "application/json" },
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data.basari && data.kur_try) {
          kurEl.textContent = formatKur(data.kur_try);
          if (kurInput && !kurInput.value) {
            kurInput.placeholder = data.kur_try;
          }
          kaynakEl.textContent = "Kaynak: " + (data.kaynak || "—");
        } else {
          kurEl.textContent = "Kur alınamadı";
          kaynakEl.textContent = data.hata || "Manuel kur girebilirsiniz.";
        }
        tutarTryEl.textContent = formatTry(data.tutar_try);
      })
      .catch(function () {
        kurEl.textContent = "Kur alınamadı";
        tutarTryEl.textContent = "—";
      });
  }

  function planla() {
    clearTimeout(timer);
    timer = setTimeout(guncelle, 350);
  }

  if (tarihInput) tarihInput.addEventListener("change", planla);
  if (tutarInput) {
    tutarInput.addEventListener("input", planla);
    tutarInput.addEventListener("change", planla);
  }

  guncelle();
})();
