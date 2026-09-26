(() => {
  const search = document.querySelector("#guide-search");
  if (!search) return;
  const cards = [...document.querySelectorAll("[data-guide-topic]")];
  const normalize = (value) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
  const indexed = cards.map((card) => [card, normalize(card.dataset.guideKeywords)]);
  const filter = () => {
    const words = normalize(search.value).split(/\s+/).filter(Boolean);
    let count = 0;
    indexed.forEach(([card, keywords]) => {
      card.hidden = !words.every((word) => keywords.includes(word));
      if (!card.hidden) count += 1;
    });
    document.querySelector("#guide-empty").hidden = count !== 0;
    document.querySelector("#guide-results").textContent = `${count} ${count === 1 ? "categoría disponible" : "categorías disponibles"}.`;
  };
  search.disabled = false;
  search.addEventListener("input", filter);
  document.querySelector("#guide-reset").addEventListener("click", () => {
    search.value = "";
    filter();
    search.focus();
  });
  filter();
})();
