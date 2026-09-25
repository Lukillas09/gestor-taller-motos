if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  });
}

const loadingBar = document.querySelector("#global-loading");

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    const search = document.querySelector("#global-search");
    if (search) {
      event.preventDefault();
      search.focus();
    }
  }
});

document.addEventListener("submit", (event) => {
  const form = event.target.closest("form");
  if (!form) return;

  if (
    form.matches("[data-confirm-message]") &&
    !window.confirm(form.dataset.confirmMessage)
  ) {
    event.preventDefault();
    return;
  }

  if ((form.method || "get").toLowerCase() !== "post") return;

  const button = event.submitter || form.querySelector("button[type='submit']");
  if (!button || button.disabled) return;

  button.dataset.originalText = button.innerHTML;
  button.setAttribute("aria-busy", "true");
  button.classList.add("is-submitting");
  window.setTimeout(() => {
    button.disabled = true;
  }, 0);
});

document.body.addEventListener("htmx:beforeRequest", () => {
  loadingBar?.classList.add("is-visible");
});

const finishHtmxRequest = (event) => {
  loadingBar?.classList.remove("is-visible");
  const form = event.detail?.elt?.closest?.("form");
  const button = form?.querySelector("button.is-submitting");
  if (button) {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.classList.remove("is-submitting");
    if (button.dataset.originalText) button.innerHTML = button.dataset.originalText;
  }
};

document.body.addEventListener("htmx:afterRequest", finishHtmxRequest);
document.body.addEventListener("htmx:responseError", finishHtmxRequest);

window.addEventListener("load", () => {
  document.querySelectorAll(".app-toast").forEach((toast) => {
    const tags = toast.dataset.messageTags || "";
    if (tags.includes("error")) return;
    window.setTimeout(() => {
      if (window.bootstrap?.Alert) {
        window.bootstrap.Alert.getOrCreateInstance(toast).close();
      }
    }, 6500);
  });
});
