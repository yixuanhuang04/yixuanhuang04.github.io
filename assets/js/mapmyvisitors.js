(function () {
  const MAP_CONTAINER_ID = "mapmyvisitors-container";

  const MAP_BASE_URL = "https://mapmyvisitors.com/map.js";

  const MAP_COMMON_PARAMS = {
    t: "tt",
    d: "H9R_6PTXQeo1FcQAZCn20MT8cfzFCTSOm7Y_0bze6eg",
    cmo: "e01f7c",
    cmn: "ffcb05",
  };

  const MAP_THEME_PARAMS = {
    light: {
      cl: "000000",
      co: "ffffff",
      ct: "000000",
    },

    dark: {
      cl: "ffffff",
      co: "1d1d1f",
      ct: "ffffff",
    },
  };

  let currentTheme = null;
  let currentMapWidth = null;
  let resizeTimer = null;
  let initialized = false;

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

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

  function getMapWidth() {
    const viewportWidth = window.innerWidth;

    if (viewportWidth <= 400) {
      return 320;
    }

    if (viewportWidth <= 600) {
      return 360;
    }

    if (viewportWidth <= 900) {
      return 420;
    }

    return 480;
  }

  function buildMapUrl(theme, width) {
    const normalizedTheme = theme === "dark" ? "dark" : "light";

    const params = new URLSearchParams({
      cl: MAP_THEME_PARAMS[normalizedTheme].cl,
      w: String(width),
      t: MAP_COMMON_PARAMS.t,
      d: MAP_COMMON_PARAMS.d,
      co: MAP_THEME_PARAMS[normalizedTheme].co,
      ct: MAP_THEME_PARAMS[normalizedTheme].ct,
      cmo: MAP_COMMON_PARAMS.cmo,
      cmn: MAP_COMMON_PARAMS.cmn,
    });

    return `${MAP_BASE_URL}?${params.toString()}`;
  }

  function loadMapMyVisitors(theme) {
    const container = document.getElementById(MAP_CONTAINER_ID);

    if (!container) {
      return;
    }

    const normalizedTheme = theme === "dark" ? "dark" : "light";
    const mapWidth = getMapWidth();

    if (normalizedTheme === currentTheme && mapWidth === currentMapWidth) {
      return;
    }

    currentTheme = normalizedTheme;
    currentMapWidth = mapWidth;

    container.innerHTML = "";

    const script = document.createElement("script");
    script.type = "text/javascript";
    script.id = "mapmyvisitors";
    script.src = buildMapUrl(normalizedTheme, mapWidth);

    container.appendChild(script);
  }

  function refreshMapMyVisitors() {
    const theme = getCurrentTheme();
    loadMapMyVisitors(theme);
  }

  function refreshMapMyVisitorsOnResize() {
    clearTimeout(resizeTimer);

    resizeTimer = setTimeout(function () {
      const nextMapWidth = getMapWidth();

      if (nextMapWidth !== currentMapWidth) {
        refreshMapMyVisitors();
      }
    }, 200);
  }

  function initMapMyVisitors() {
    const container = document.getElementById(MAP_CONTAINER_ID);

    if (!container || initialized) {
      return;
    }

    initialized = true;

    refreshMapMyVisitors();

    const darkModeMediaQuery = window.matchMedia(
      "(prefers-color-scheme: dark)",
    );

    if (typeof darkModeMediaQuery.addEventListener === "function") {
      darkModeMediaQuery.addEventListener("change", function () {
        const savedTheme = localStorage.getItem("theme");

        if (savedTheme !== "dark" && savedTheme !== "light") {
          refreshMapMyVisitors();
        }
      });
    } else if (typeof darkModeMediaQuery.addListener === "function") {
      darkModeMediaQuery.addListener(function () {
        const savedTheme = localStorage.getItem("theme");

        if (savedTheme !== "dark" && savedTheme !== "light") {
          refreshMapMyVisitors();
        }
      });
    }

    window.addEventListener("resize", refreshMapMyVisitorsOnResize);

    const themeObserver = new MutationObserver(function () {
      refreshMapMyVisitors();
    });

    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "data-theme"],
    });

    window.setMapMyVisitorsTheme = function (theme) {
      loadMapMyVisitors(theme);
    };

    window.refreshMapMyVisitors = refreshMapMyVisitors;
  }

  ready(initMapMyVisitors);
})();
