(function () {
  var form = document.getElementById("odeme-kayit-form");
  if (!form) return;

  var tipSelect = form.querySelector('[name="tip"]');
  var personelSelect = form.querySelector('[name="personel"]');
  var aliciInput = form.querySelector('[name="alici_adi"]');
  var tutarInput = form.querySelector('[name="tutar"]');
  var fieldPersonel = document.getElementById("field-personel");
  var fieldAlici = document.getElementById("field-alici");
  var personelHint = document.getElementById("personel-hint");
  var aliciHint = document.getElementById("alici-hint");

  var maasMap = {};
  var dataEl = document.getElementById("personel-maaslari-data");
  var maasRows = dataEl ? JSON.parse(dataEl.textContent) : [];
  maasRows.forEach(function (row) {
    maasMap[String(row[0])] = row[1];
  });

  function setVisible(el, show) {
    if (!el) return;
    el.hidden = !show;
    el.style.display = show ? "" : "none";
  }

  function updateFields() {
    var tip = tipSelect ? tipSelect.value : "masraf";

    if (tip === "masraf") {
      setVisible(fieldPersonel, true);
      setVisible(fieldAlici, true);
      if (personelHint) personelHint.textContent = "İsteğe bağlı — personele yapılan masraflar için.";
      if (aliciHint) aliciHint.textContent = "Personel seçilmediyse alıcı adı girin.";
      if (personelSelect) personelSelect.required = false;
      if (aliciInput) aliciInput.required = false;
    } else {
      setVisible(fieldPersonel, true);
      setVisible(fieldAlici, false);
      if (personelHint) {
        personelHint.textContent =
          tip === "avans" ? "Avans verilecek personeli seçin." : "Maaş ödenecek personeli seçin.";
      }
      if (personelSelect) personelSelect.required = true;
      if (aliciInput) aliciInput.value = "";
    }

    if (tip === "maas" && personelSelect && tutarInput) {
      var pk = personelSelect.value;
      if (pk && maasMap[pk] && !tutarInput.dataset.userEdited) {
        tutarInput.value = maasMap[pk];
      }
    }
  }

  if (tutarInput) {
    tutarInput.addEventListener("input", function () {
      tutarInput.dataset.userEdited = "1";
    });
  }

  if (tipSelect) {
    tipSelect.addEventListener("change", function () {
      if (tutarInput) delete tutarInput.dataset.userEdited;
      updateFields();
    });
  }

  if (personelSelect) {
    personelSelect.addEventListener("change", function () {
      if (tipSelect && tipSelect.value === "maas" && tutarInput) {
        delete tutarInput.dataset.userEdited;
        var pk = personelSelect.value;
        if (pk && maasMap[pk]) {
          tutarInput.value = maasMap[pk];
        }
      }
    });
  }

  updateFields();
})();
