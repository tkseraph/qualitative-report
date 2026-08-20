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

(() => {
  const masthead = document.querySelector(".masthead");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const heroItems = [
    ...document.querySelectorAll(".hero-copy > *, .hero-stats > div"),
  ];
  const pageItems = [
    ...document.querySelectorAll(
      ".catalog-heading, .catalog-tools, .result-status, .category-header, .report-row, .footer-brand, .footer-legal"
    ),
  ];
  const targets = [...heroItems, ...pageItems];

  const syncMasthead = () => masthead?.classList.toggle("is-scrolled", window.scrollY > 18);
  syncMasthead();
  window.addEventListener("scroll", syncMasthead, { passive: true });

  if (reducedMotion.matches || !("IntersectionObserver" in window)) {
    targets.forEach((target) => target.classList.add("motion-reveal", "is-revealed"));
    return;
  }

  targets.forEach((target, index) => {
    target.classList.add("motion-reveal");
    const heroIndex = heroItems.indexOf(target);
    const delay = heroIndex >= 0 ? Math.min(heroIndex, 6) * 70 : Math.min(index % 4, 3) * 55;
    target.style.setProperty("--motion-delay", `${delay}ms`);
  });
  document.documentElement.classList.add("motion-ready");

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-revealed");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -6%", threshold: 0.04 });

  targets.forEach((target) => observer.observe(target));
})();
