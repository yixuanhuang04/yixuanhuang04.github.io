(function () {
  function loadFooter() {
    const footerContent = document.getElementById("footer-content");

    if (!footerContent) {
      document.dispatchEvent(new CustomEvent("site:footer-missing"));
      return;
    }

    fetch("/footer/index.html")
      .then(function (res) {
        return res.text();
      })
      .then(function (html) {
        footerContent.innerHTML = html;

        const footer = document.querySelector(".site-footer");
        const updated = footerContent.querySelector("[data-footer-updated]");

        if (footer && footer.dataset.showUpdated === "true" && updated) {
          updated.hidden = false;
        }

        document.dispatchEvent(new CustomEvent("site:footer-loaded"));
      })
      .catch(function (error) {
        console.warn("[Footer] Failed to load footer:", error);
        document.dispatchEvent(new CustomEvent("site:footer-error"));
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadFooter, { once: true });
  } else {
    loadFooter();
  }
})();
