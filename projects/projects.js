(function () {
  function getLinkLabel(link) {
    return link.title || "Link";
  }

  function createLink(link) {
    const wrapper = document.createElement("div");
    wrapper.className = "project-link-line";

    const prefix = document.createElement("span");
    prefix.className = "project-link-platform";
    prefix.textContent = (link.platform || "link") + ": ";

    const a = document.createElement("a");
    a.href = link.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = getLinkLabel(link);
    a.className = "project-link";

    wrapper.appendChild(prefix);
    wrapper.appendChild(a);

    return wrapper;
  }

  function createProjectCard(project) {
    const item = document.createElement("div");
    item.className = "project-item";

    const media = document.createElement("div");
    media.className = "project-media";

    if (project.image) {
      const img = document.createElement("img");
      img.src = project.image;
      img.alt = project.title || "Project image";
      media.appendChild(img);
    }

    const content = document.createElement("div");
    content.className = "project-content";

    const title = document.createElement("div");
    title.className = "project-title";
    title.textContent = project.title || "Untitled Project";

    const year = document.createElement("div");
    year.className = "project-year";
    year.textContent = project.year || "";

    const desc = document.createElement("div");
    desc.className = "project-desc";
    desc.textContent = project.description || "";

    const linksWrap = document.createElement("div");
    linksWrap.className = "project-links";

    (project.links || []).forEach(function (link) {
      linksWrap.appendChild(createLink(link));
    });

    content.appendChild(title);

    if (project.year) {
      content.appendChild(year);
    }

    if (project.description) {
      content.appendChild(desc);
    }

    if ((project.links || []).length > 0) {
      content.appendChild(linksWrap);
    }

    item.appendChild(media);
    item.appendChild(content);

    return item;
  }

  function renderProjects(projects, containerId) {
    const container = document.getElementById(containerId);

    if (!container) {
      return;
    }

    container.innerHTML = "";

    projects.forEach(function (project) {
      container.appendChild(createProjectCard(project));
    });
  }

  function loadProjects(jsonPath, containerId) {
    fetch(jsonPath)
      .then(function (res) {
        if (!res.ok) {
          throw new Error(`Failed to fetch ${jsonPath}: ${res.status}`);
        }

        return res.json();
      })
      .then(function (data) {
        renderProjects(data, containerId);
      })
      .catch(function (error) {
        console.warn("[Projects] Failed to load projects:", error);
      });
  }

  function autoLoadProjects() {
    const container = document.getElementById("project-list");

    if (!container) {
      return;
    }

    const jsonPath = container.dataset.projectsSrc || "/projects/selected.json";

    loadProjects(jsonPath, "project-list");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoLoadProjects, {
      once: true,
    });
  } else {
    autoLoadProjects();
  }

  window.loadProjects = loadProjects;
  window.renderProjects = renderProjects;
})();
