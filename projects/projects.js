function loadProjects(jsonPath, containerId) {
  fetch(jsonPath)
    .then((res) => res.json())
    .then((projects) => {
      const container = document.getElementById(containerId);

      projects.forEach((p) => {
        const item = document.createElement("article");
        item.className = "project-item";

        const linksHTML = (p.links || [])
          .map(
            (l) => `
                        <a href="${l.url}" target="_blank">
                            ${l.label}
                        </a>
                    `,
          )
          .join(" ");

        item.innerHTML = `
                    <div class="project-media">
                        <img src="${p.image}" alt="${p.title}">
                    </div>

                    <div class="project-content">

                        <p class="project-title">
                            ${p.title}
                        </p>

                        <div class="project-meta">
                            <span class="project-year">
                                ${p.year}
                            </span>
                        </div>

                        <div class="project-desc">
                            ${p.description}
                        </div>

                        ${
                          linksHTML
                            ? `<div class="project-links">${linksHTML}</div>`
                            : ""
                        }

                    </div>
                `;

        container.appendChild(item);
      });
    });
}
