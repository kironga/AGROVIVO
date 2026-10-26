document.addEventListener("DOMContentLoaded", () => {
  const menu = document.querySelector(".menu");
  const nav = document.querySelector("#main-nav");

  if (menu && nav) {
    menu.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("open");
      menu.setAttribute("aria-expanded", String(isOpen));
      menu.textContent = isOpen ? "Close" : "Menu";
    });
    nav.addEventListener("click", (event) => {
      if (!event.target.closest("a")) return;
      nav.classList.remove("open");
      menu.setAttribute("aria-expanded", "false");
      menu.textContent = "Menu";
    });
  }

  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const wrapper = document.createElement("span");
    wrapper.className = "password-input-wrap";
    input.before(wrapper);
    wrapper.append(input);
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "password-visibility-toggle";
    toggle.setAttribute("aria-label", "Show password");
    toggle.setAttribute("aria-pressed", "false");
    toggle.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
    wrapper.append(toggle);
    toggle.addEventListener("click", () => {
      const visible = input.type === "password";
      input.type = visible ? "text" : "password";
      toggle.setAttribute("aria-pressed", String(visible));
      toggle.setAttribute("aria-label", visible ? "Hide password" : "Show password");
    });
  });

  const staticImage = document.querySelector("#id_static_image");
  const imageSource = document.querySelector("#id_image_source");
  const imageUpload = document.querySelector("#id_image_upload");
  const imagePreview = document.querySelector("#product-image-preview");
  const setImagePreview = (src) => {
    if (!imagePreview) return;
    const box = imagePreview.closest(".current-product-image");
    if (!src) {
      if (box) box.hidden = true;
      return;
    }
    imagePreview.src = src;
    if (box) box.hidden = false;
  };
  staticImage?.addEventListener("change", () => {
    if (staticImage.value) {
      if (imageSource) imageSource.value = "";
      setImagePreview(staticImage.value);
    }
  });
  imageSource?.addEventListener("input", () => {
    if (imageSource.value) {
      if (staticImage) staticImage.value = "";
      setImagePreview(imageSource.value);
    }
  });
  imageUpload?.addEventListener("change", () => {
    const file = imageUpload.files?.[0];
    if (file) setImagePreview(URL.createObjectURL(file));
  });

  const search = document.querySelector("#product-search");
  const products = [...document.querySelectorAll(".catalog-product")];
  const visibleCount = document.querySelector("#visible-count");
  const noResults = document.querySelector(".no-search-results");

  if (search) {
    search.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      let visible = 0;
      products.forEach((product) => {
        const matches = product.dataset.search.includes(query);
        product.hidden = !matches;
        if (matches) visible += 1;
      });
      if (visibleCount) visibleCount.textContent = visible;
      if (noResults) noResults.hidden = visible !== 0;
    });
  }

  const revealItems = document.querySelectorAll(
    ".section, .product-card, .focus-card, .crop-tile"
  );
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.08 });
    revealItems.forEach((item) => item.classList.add("reveal"));
    revealItems.forEach((item) => observer.observe(item));
  }

  const showToast = (message, isError = false) => {
    document.querySelector(".cart-toast")?.remove();
    const toast = document.createElement("div");
    toast.className = "cart-toast" + (isError ? " cart-toast-error" : "");
    if (isError) toast.style.backgroundColor = "#853f32";
    toast.setAttribute("role", "status");
    toast.textContent = message;
    document.body.append(toast);
    requestAnimationFrame(() => toast.classList.add("show"));
    window.setTimeout(() => {
      toast.classList.remove("show");
      window.setTimeout(() => toast.remove(), 250);
    }, 2600);
  };

  document.querySelectorAll(".js-cart-add").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button");
      const originalLabel = button.innerHTML;
      button.disabled = true;
      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (response.redirected) {
          window.location.assign(response.url);
          return;
        }
        const page = new DOMParser().parseFromString(await response.text(), "text/html");
        const updatedCount = page.querySelector(".nav-cart b");
        const cartCount = document.querySelector(".nav-cart b");
        if (updatedCount && cartCount) cartCount.textContent = updatedCount.textContent;
        const error = page.querySelector(".messages .error");
        const success = page.querySelector(".messages .success");
        if (!response.ok || error) {
          showToast(error?.textContent.trim() || "Could not add this item.", true);
        } else {
          showToast(success?.textContent.trim() || "Added to your cart.");
          button.textContent = "✓";
        }
      } catch {
        form.submit();
        return;
      } finally {
        window.setTimeout(() => {
          button.disabled = false;
          button.innerHTML = originalLabel;
        }, 1200);
      }
    });
  });
});
