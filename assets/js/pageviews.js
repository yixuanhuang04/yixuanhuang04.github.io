(function () {
  function initPageViews() {
    const pageViewCounter = document.getElementById("busuanzi_value_page_pv");

    if (!pageViewCounter) {
      return;
    }

    if (document.getElementById("busuanzi-script")) {
      return;
    }

    const script = document.createElement("script");
    script.id = "busuanzi-script";
    script.async = true;
    script.src = "//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";

    document.body.appendChild(script);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPageViews, { once: true });
  } else {
    initPageViews();
  }
})();
