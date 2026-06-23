(function () {
  const MAP_CONTAINER_ID = "mapmyvisitors-container";

  const MAP_URLS = {
    light: "https://mapmyvisitors.com/map.js?cl=000000&w=480&t=tt&d=BCxcZyc2gIdIT2h-kBeW4cYemyIr_LC9eH-inbjv1O4&co=ffffff&ct=000000&cmo=2f65a7&cmn=ffcb05",

    dark: "https://mapmyvisitors.com/map.js?cl=ffffff&w=480&t=tt&d=BCxcZyc2gIdIT2h-kBeW4cYemyIr_LC9eH-inbjv1O4&co=1d1d1f&ct=ffffff&cmo=2f65a7&cmn=ffcb05",
  };

  let currentTheme = null;

  function getCurrentTheme() {
    const html = document.documentElement;

    const dataTheme = html.getAttribute("data-theme");
    if (dataTheme === "dark") return "dark";
    if (dataTheme === "light") return "light";

    if (html.classList.contains("dark")) {
      return "dark";
    }

    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") return "dark";
    if (savedTheme === "light") return "light";

    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }

    return "light";
  }

  function loadMapMyVisitors(theme) {
    const normalizedTheme = theme === "dark" ? "dark" : "light";

    if (normalizedTheme === currentTheme) {
      return;
    }

    const container = document.getElementById(MAP_CONTAINER_ID);

    if (!container) {
      console.warn(
        `[MapMyVisitors] Cannot find #${MAP_CONTAINER_ID}. Please add <div id="${MAP_CONTAINER_ID}"></div> to your HTML.`,
      );
      return;
    }

    currentTheme = normalizedTheme;

    container.innerHTML = "";

    const script = document.createElement("script");
    script.type = "text/javascript";
    script.id = "mapmyvisitors";
    script.src = MAP_URLS[normalizedTheme];

    container.appendChild(script);
  }

  function refreshMapMyVisitors() {
    const theme = getCurrentTheme();
    loadMapMyVisitors(theme);
  }

  document.addEventListener("DOMContentLoaded", function () {
    refreshMapMyVisitors();
  });

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", function () {
      const savedTheme = localStorage.getItem("theme");

      if (savedTheme !== "dark" && savedTheme !== "light") {
        refreshMapMyVisitors();
      }
    });

  const observer = new MutationObserver(function () {
    refreshMapMyVisitors();
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class", "data-theme"],
  });

  window.setMapMyVisitorsTheme = function (theme) {
    loadMapMyVisitors(theme);
  };

  window.refreshMapMyVisitors = refreshMapMyVisitors;
})();
