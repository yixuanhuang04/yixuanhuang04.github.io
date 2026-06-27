(function () {
  function updateNavbarHeight() {
    const navbar = document.querySelector(".navbar");

    if (!navbar) {
      return;
    }

    document.documentElement.style.setProperty(
      "--navbar-height",
      `${navbar.offsetHeight}px`,
    );
  }

  function initNavbar() {
    updateNavbarHeight();

    window.addEventListener("load", updateNavbarHeight);
    window.addEventListener("resize", updateNavbarHeight);

    const navbar = document.querySelector(".navbar");

    if (navbar && "ResizeObserver" in window) {
      new ResizeObserver(updateNavbarHeight).observe(navbar);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initNavbar, { once: true });
  } else {
    initNavbar();
  }
})();
