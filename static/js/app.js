if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  });
}

document.addEventListener("submit", (event) => {
  const form = event.target.closest("form[data-confirm-message]");
  if (form && !window.confirm(form.dataset.confirmMessage)) {
    event.preventDefault();
  }
});
