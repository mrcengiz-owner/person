(function () {
  const girisInput = document.getElementById("id_mesai_giris");
  const cikisInput = document.getElementById("id_mesai_cikis");
  const sureText = document.getElementById("mesai-sure-text");
  const timelineTrack = document.getElementById("mesai-timeline-track");
  const timelineCaption = document.getElementById("mesai-timeline-caption");
  const timelineWrap = document.querySelector(".mesai-timeline-preview");
  const presetBtns = document.querySelectorAll(".mesai-preset-btn");

  const GUN_DK = 24 * 60;

  if (!girisInput || !cikisInput) return;

  function parseTime(value) {
    if (!value || !value.includes(":")) return null;
    const [h, m] = value.split(":").map(Number);
    if (Number.isNaN(h) || Number.isNaN(m)) return null;
    return h * 60 + m;
  }

  function formatClock(mins) {
    const h = Math.floor(mins / 60) % 24;
    const m = mins % 60;
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
  }

  function durationMinutes(girisMins, cikisMins) {
    if (girisMins === null || cikisMins === null) return null;
    let end = cikisMins;
    if (end <= girisMins) end += GUN_DK;
    return end - girisMins;
  }

  function durationText(girisMins, cikisMins) {
    const total = durationMinutes(girisMins, cikisMins);
    if (total === null) return "—";
    if (total === GUN_DK) return "24 saat";
    const saat = Math.floor(total / 60);
    const dk = total % 60;
    if (dk) return `${saat} saat ${dk} dk`;
    return `${saat} saat`;
  }

  function isGeceVardiyasi(girisMins, cikisMins) {
    if (girisMins === null || cikisMins === null) return false;
    return cikisMins <= girisMins;
  }

  function timelineSegments(girisMins, cikisMins) {
    if (girisMins === null || cikisMins === null) return [];

    if (girisMins === cikisMins) {
      return [{ left: 0, width: 100 }];
    }

    if (cikisMins > girisMins) {
      return [
        {
          left: (girisMins / GUN_DK) * 100,
          width: Math.max(((cikisMins - girisMins) / GUN_DK) * 100, 1.5),
        },
      ];
    }

    return [
      {
        left: (girisMins / GUN_DK) * 100,
        width: Math.max(((GUN_DK - girisMins) / GUN_DK) * 100, 1.5),
      },
      {
        left: 0,
        width: Math.max((cikisMins / GUN_DK) * 100, 1.5),
      },
    ];
  }

  function aralikText(girisMins, cikisMins) {
    if (girisMins === null || cikisMins === null) return "";
    const g = formatClock(girisMins);
    const c = formatClock(cikisMins);
    if (isGeceVardiyasi(girisMins, cikisMins)) return `${g} – ${c} (+1 gün)`;
    return `${g} – ${c}`;
  }

  function renderTimeline(girisMins, cikisMins) {
    if (!timelineTrack) return;

    timelineTrack.innerHTML = "";
    const segments = timelineSegments(girisMins, cikisMins);

    segments.forEach((seg, index) => {
      const bar = document.createElement("div");
      bar.className =
        "mesai-timeline-bar" + (index > 0 ? " mesai-timeline-bar-alt" : "");
      bar.style.left = `${seg.left}%`;
      bar.style.width = `${seg.width}%`;
      timelineTrack.appendChild(bar);
    });

    if (timelineWrap) {
      timelineWrap.classList.toggle(
        "mesai-timeline-gece",
        isGeceVardiyasi(girisMins, cikisMins)
      );
    }
  }

  function updatePresetsActive() {
    const g = girisInput.value;
    const c = cikisInput.value;
    presetBtns.forEach((btn) => {
      const match = btn.dataset.giris === g && btn.dataset.cikis === c;
      btn.setAttribute("aria-pressed", match ? "true" : "false");
      btn.classList.toggle("active", match);
    });
  }

  function updatePreview() {
    const girisMins = parseTime(girisInput.value);
    const cikisMins = parseTime(cikisInput.value);
    const valid = durationMinutes(girisMins, cikisMins) !== null;

    if (sureText) {
      sureText.textContent = durationText(girisMins, cikisMins);
      sureText.parentElement?.classList.toggle("mesai-duration-invalid", !valid);
    }

    if (valid) {
      renderTimeline(girisMins, cikisMins);
      if (timelineCaption) {
        timelineCaption.textContent = `${aralikText(girisMins, cikisMins)} · ${durationText(girisMins, cikisMins)}`;
      }
    } else {
      if (timelineTrack) timelineTrack.innerHTML = "";
      if (timelineCaption) {
        timelineCaption.textContent = "Giriş ve çıkış saatlerini seçin (24 saatlik periyot)";
      }
      timelineWrap?.classList.remove("mesai-timeline-gece");
    }

    updatePresetsActive();
  }

  presetBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      girisInput.value = btn.dataset.giris;
      cikisInput.value = btn.dataset.cikis;
      updatePreview();
      girisInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });

  girisInput.addEventListener("input", updatePreview);
  cikisInput.addEventListener("input", updatePreview);
  girisInput.addEventListener("change", updatePreview);
  cikisInput.addEventListener("change", updatePreview);

  updatePreview();
})();
