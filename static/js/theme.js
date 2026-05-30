(function () {
  const STORAGE_KEY = "pt-theme";

  function getPreferredTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") {
      return saved;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function updateMetaThemeColor(theme) {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", theme === "dark" ? "#0c0f1a" : "#6366f1");
    }
  }

  function updateToggle(theme) {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    const isDark = theme === "dark";
    btn.setAttribute("aria-pressed", isDark ? "true" : "false");
    btn.setAttribute("aria-label", isDark ? "Açık temaya geç" : "Koyu temaya geç");
    btn.setAttribute("title", isDark ? "Açık mod" : "Koyu mod");
  }

  window.setTheme = function (theme) {
    if (theme !== "light" && theme !== "dark") return;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    updateMetaThemeColor(theme);
    updateToggle(theme);
  };

  window.toggleTheme = function () {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    window.setTheme(next);
  };

  document.addEventListener("DOMContentLoaded", () => {
    const theme = document.documentElement.getAttribute("data-theme") || getPreferredTheme();
    window.setTheme(theme);

    document.getElementById("theme-toggle")?.addEventListener("click", window.toggleTheme);
  });
})();
