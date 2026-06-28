(function () {
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }

      const script = document.createElement("script");
      script.src = src;
      script.defer = true;

      script.onload = resolve;
      script.onerror = function () {
        reject(new Error(`Failed to load script: ${src}`));
      };

      document.body.appendChild(script);
    });
  }

  // Navbar behavior
  loadScript("/assets/js/navbar.js").catch(function (error) {
    console.warn(error);
  });

  // Footer must load before visitor map, because the map container lives in footer.
  document.addEventListener(
    "site:footer-loaded",
    function () {
      loadScript("/assets/js/mapmyvisitors.js").catch(function (error) {
        console.warn(error);
      });
    },
    { once: true },
  );

  // Pageviews
  loadScript("/assets/js/pageviews.js").catch(function (error) {
    console.warn(error);
  });

  // Footer loader
  loadScript("/footer/footer.js").catch(function (error) {
    console.warn(error);
  });

  // Projects script: self-detects whether #project-list exists.
  loadScript("/projects/projects.js").catch(function (error) {
    console.warn(error);
  });
})();
