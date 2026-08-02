(() => {
  const input = document.querySelector("#report-search");
  const buttons = [...document.querySelectorAll("[data-filter]")];
  const cards = [...document.querySelectorAll("[data-report-card]")];
  const sections = [...document.querySelectorAll("[data-category-section]")];
  const status = document.querySelector("#result-status");
  const noResults = document.querySelector("#no-results");

  if (!input || !status || !noResults) return;

  let activeCategory = "all";

  const normalize = (value) => value.trim().toLocaleLowerCase("zh-CN");

  const refresh = () => {
    const query = normalize(input.value);
    let visibleCount = 0;

    cards.forEach((card) => {
      const matchesCategory = activeCategory === "all" || card.dataset.category === activeCategory;
      const matchesQuery = !query || normalize(card.dataset.search || "").includes(query);
      const visible = matchesCategory && matchesQuery;
      card.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    sections.forEach((section) => {
      const hasVisibleCard = Boolean(section.querySelector("[data-report-card]:not([hidden])"));
      const sectionMatches = activeCategory === "all" || section.dataset.categorySection === activeCategory;
      section.hidden = !sectionMatches || (cards.length > 0 && !hasVisibleCard);
    });

    status.textContent = query || activeCategory !== "all"
      ? `找到 ${visibleCount} 份匹配报告`
      : `共 ${visibleCount} 份已发布报告`;
    noResults.hidden = visibleCount !== 0;
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.filter || "all";
      buttons.forEach((item) => item.classList.toggle("is-active", item === button));
      refresh();
    });
  });

  input.addEventListener("input", refresh);
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      input.focus();
    }
    if (event.key === "Escape" && document.activeElement === input) {
      input.value = "";
      input.blur();
      refresh();
    }
  });
})();
