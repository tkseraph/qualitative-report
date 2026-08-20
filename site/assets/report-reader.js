(() => {
  const report = document.querySelector(".report-body");
  const reader = document.querySelector("[data-publication-reader]");
  const list = document.querySelector("[data-reader-list]");
  const toggle = document.querySelector("[data-reader-toggle]");
  const panel = document.querySelector("[data-reader-panel]");
  const progress = document.querySelector("[data-reader-progress]");
  const toTop = document.querySelector("[data-reader-top]");
  const count = document.querySelector("[data-reader-count]");

  if (!report || !reader || !list || !toggle || !panel || !progress || !toTop) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const headings = [...report.querySelectorAll("h2, h3")].filter((heading) =>
    heading.textContent.trim()
  );
  const usedIds = new Set([...document.querySelectorAll("[id]")].map((element) => element.id));
  const records = [];
  let parentId = "";

  const headingText = (heading) => {
    const copy = heading.cloneNode(true);
    copy.querySelectorAll(".tag, .status-tag").forEach((badge) => badge.remove());
    return copy.textContent.replace(/\s+/g, " ").trim();
  };

  const slugify = (value, index) => {
    const base = value
      .toLocaleLowerCase("zh-CN")
      .replace(/[\s/]+/g, "-")
      .replace(/[^\p{Letter}\p{Number}\-]+/gu, "")
      .replace(/-{2,}/g, "-")
      .replace(/^-|-$/g, "") || `section-${index + 1}`;
    let candidate = base;
    let suffix = 2;
    while (usedIds.has(candidate)) {
      candidate = `${base}-${suffix}`;
      suffix += 1;
    }
    usedIds.add(candidate);
    return candidate;
  };

  headings.forEach((heading, index) => {
    const text = headingText(heading);
    if (!heading.id) heading.id = slugify(text, index);
    if (heading.tagName === "H2") parentId = heading.id;

    const item = document.createElement("li");
    const link = document.createElement("a");
    item.className = `publication-toc-item is-depth-${heading.tagName === "H2" ? "2" : "3"}`;
    if (heading.tagName === "H3") item.dataset.parentId = parentId;
    link.className = "publication-toc-link";
    link.href = `#${encodeURIComponent(heading.id)}`;
    link.textContent = text;
    link.dataset.readerLink = heading.id;
    item.append(link);
    list.append(item);
    records.push({ heading, item, link, parentId: heading.tagName === "H2" ? heading.id : parentId });
  });

  if (count) count.textContent = `${headings.filter((heading) => heading.tagName === "H2").length} 章`;
  reader.classList.remove("is-pending");
  if (headings.length < 2) reader.classList.add("has-no-toc");

  const setOpen = (open) => {
    reader.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
  };

  toggle.addEventListener("click", () => setOpen(!reader.classList.contains("is-open")));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });
  document.addEventListener("click", (event) => {
    if (reader.classList.contains("is-open") && !reader.contains(event.target)) setOpen(false);
  });

  records.forEach(({ heading, link }) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      heading.scrollIntoView({ behavior: reducedMotion.matches ? "auto" : "smooth", block: "start" });
      window.history.replaceState(null, "", `#${encodeURIComponent(heading.id)}`);
      setOpen(false);
    });
  });

  let headingOffsets = [];
  const measureHeadings = () => {
    headingOffsets = records.map(({ heading }) => heading.getBoundingClientRect().top + window.scrollY);
  };

  let ticking = false;
  const update = () => {
    ticking = false;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const scrollMax = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    progress.style.transform = `scaleX(${Math.min(1, Math.max(0, scrollTop / scrollMax))})`;
    toTop.classList.toggle("is-visible", scrollTop > Math.min(760, window.innerHeight * 0.9));

    let activeIndex = 0;
    const readingLine = scrollTop + Math.min(190, window.innerHeight * 0.28);
    headingOffsets.forEach((offset, index) => {
      if (offset <= readingLine) activeIndex = index;
    });

    const active = records[activeIndex];
    records.forEach((record) => {
      const current = record === active;
      record.item.classList.toggle("is-active", current);
      record.item.classList.toggle("is-in-active-section", record.parentId === active?.parentId);
      record.link.classList.toggle("is-active", current);
      if (current) record.link.setAttribute("aria-current", "location");
      else record.link.removeAttribute("aria-current");
    });
  };

  const requestUpdate = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  };

  toTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: reducedMotion.matches ? "auto" : "smooth" });
  });

  window.addEventListener("scroll", requestUpdate, { passive: true });
  window.addEventListener("resize", () => {
    measureHeadings();
    requestUpdate();
  }, { passive: true });

  const revealTargets = [...report.querySelectorAll(
    ":scope > .sample-hero, :scope > h2, :scope > .grid, :scope > .callout, " +
    ":scope > .dimension-card, :scope > .research-article-section, :scope > .trend-chart-section, " +
    ":scope > .risk-panel, :scope > .footer"
  )];

  if (!reducedMotion.matches && "IntersectionObserver" in window) {
    revealTargets.forEach((target, index) => {
      target.classList.add("publication-reveal");
      target.style.setProperty("--publication-reveal-delay", `${Math.min(index % 4, 3) * 55}ms`);
    });
    document.documentElement.classList.add("publication-motion-enabled");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-revealed");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -7%", threshold: 0.05 });
    revealTargets.forEach((target) => observer.observe(target));
  } else {
    revealTargets.forEach((target) => target.classList.add("publication-reveal", "is-revealed"));
  }

  measureHeadings();
  update();
})();
