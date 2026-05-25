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
  a.textContent = link.title || "Link";
  a.className = "project-link";

  wrapper.appendChild(prefix);
  wrapper.appendChild(a);

  return wrapper;
}

function createProjectCard(p) {
  const item = document.createElement("div");
  item.className = "project-item";

  // media
  const media = document.createElement("div");
  media.className = "project-media";

  const img = document.createElement("img");
  img.src = p.image;
  img.alt = p.title;

  media.appendChild(img);

  // content
  const content = document.createElement("div");
  content.className = "project-content";

  const title = document.createElement("div");
  title.className = "project-title";
  title.textContent = p.title;

  const year = document.createElement("div");
  year.className = "project-year";
  year.textContent = p.year;

  const desc = document.createElement("div");
  desc.className = "project-desc";
  desc.textContent = p.description;

  const linksWrap = document.createElement("div");
  linksWrap.className = "project-links";

  (p.links || []).forEach(link => {
    linksWrap.appendChild(createLink(link));
  });

  content.appendChild(title);
  content.appendChild(year);
  content.appendChild(desc);
  content.appendChild(linksWrap);

  item.appendChild(media);
  item.appendChild(content);

  return item;
}

function renderProjects(projects, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = "";

  projects.forEach(p => {
    container.appendChild(createProjectCard(p));
  });
}

function loadProjects(jsonPath, containerId) {
  fetch(jsonPath)
    .then(res => res.json())
    .then(data => {
      renderProjects(data, containerId);
    })
    .catch(err => {
      console.error("Failed to load projects:", err);
    });
}