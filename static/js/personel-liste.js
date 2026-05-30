(function () {
  const modal = document.getElementById("personel-modal");
  const modalContent = document.getElementById("modal-content");
  const modalLoading = document.getElementById("modal-loading");
  const searchInput = document.getElementById("personel-search");
  const personelCount = document.getElementById("personel-count");
  const emptySearch = document.getElementById("empty-search");
  const table = document.getElementById("personel-table");

  let lastFocus = null;

  function openModal() {
    if (!modal) return;
    lastFocus = document.activeElement;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
  }

  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    modalContent.innerHTML = "";
    if (lastFocus && typeof lastFocus.focus === "function") {
      lastFocus.focus();
    }
  }

  function showLoading(show) {
    if (modalLoading) {
      modalLoading.hidden = !show;
    }
    if (modalContent) {
      modalContent.hidden = show;
    }
  }

  async function loadPersonelDetail(url, title) {
    openModal();
    showLoading(true);

    try {
      const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!response.ok) {
        throw new Error("Yüklenemedi");
      }
      const html = await response.text();
      modalContent.innerHTML = html;
      showLoading(false);

      const closeBtn = modalContent.querySelector("[data-modal-close]");
      closeBtn?.focus();
    } catch {
      modalContent.innerHTML =
        '<div class="modal-error"><p>Detay yüklenirken bir hata oluştu.</p><button type="button" class="btn btn-primary" data-modal-close>Kapat</button></div>';
      showLoading(false);
    }
  }

  document.querySelectorAll("[data-personel-modal]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const url = btn.dataset.url;
      if (url) {
        loadPersonelDetail(url, btn.dataset.title);
      }
    });
  });

  modal?.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-backdrop")) {
      closeModal();
      return;
    }
    if (e.target.closest(".modal-close")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && !modal.hidden) {
      closeModal();
    }
  });

  if (searchInput && table) {
    const rows = () => table.querySelectorAll("tbody .personel-row");

    searchInput.addEventListener("input", () => {
      const q = searchInput.value.trim().toLowerCase();
      let visible = 0;

      rows().forEach((row) => {
        const text = row.dataset.search || "";
        const match = !q || text.includes(q);
        row.hidden = !match;
        if (match) visible += 1;
      });

      if (personelCount) {
        personelCount.textContent = String(visible);
      }
      if (emptySearch) {
        emptySearch.hidden = visible > 0 || !q;
      }
    });
  }
})();
