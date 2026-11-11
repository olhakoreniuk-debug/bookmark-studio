const STORAGE_KEY = "bookmark-studio:bookmarks";

const exampleBookmark = {
  id: "example-barcelona",
  url: "https://www.barcelonaturisme.com/wv3/en/",
  title: "Barcelona beyond the postcards: architecture, sea and quiet squares",
  description: "A practical city guide, from modernist neighbourhoods to local markets and walks along the sea.",
  cover: "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?auto=format&fit=crop&w=1200&q=80",
  note: "Revisit before the trip, especially the route through Gràcia and the list of smaller museums.",
  tags: ["Barcelona", "travel", "architecture"],
  createdAt: 0,
  example: true,
};

const form = document.querySelector("#bookmark-form");
const list = document.querySelector("#bookmark-list");
const template = document.querySelector("#bookmark-template");
const previewButton = document.querySelector("#preview-button");
const previewPanel = document.querySelector("#preview-panel");
const formMessage = document.querySelector("#form-message");

const validationMessages = {
  url: "Enter a complete URL, including https://",
  title: "Add a title for this bookmark.",
};

Object.entries(validationMessages).forEach(([fieldName, message]) => {
  const field = form.elements[fieldName];
  field.addEventListener("invalid", () => field.setCustomValidity(message));
  field.addEventListener("input", () => field.setCustomValidity(""));
});

function readBookmarks() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function domainFromUrl(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "link";
  }
}

function wordForBookmarks(count) {
  return count === 1 ? "bookmark" : "bookmarks";
}

function createCard(bookmark) {
  const card = template.content.cloneNode(true);
  const image = card.querySelector("img");
  const fallback = card.querySelector(".cover-fallback");
  const badge = card.querySelector(".example-badge");

  if (bookmark.cover) {
    image.src = bookmark.cover;
    image.alt = `Cover image: ${bookmark.title}`;
    image.addEventListener("error", () => {
      image.hidden = true;
      fallback.hidden = false;
    });
    fallback.hidden = true;
  } else {
    image.hidden = true;
  }

  badge.hidden = !bookmark.example;
  card.querySelector(".card-domain").textContent = domainFromUrl(bookmark.url);
  card.querySelector("h3").textContent = bookmark.title;
  card.querySelector(".card-description").textContent = bookmark.description || "Saved link without a description.";
  card.querySelector(".card-note p").textContent = bookmark.note || "";

  const tags = card.querySelector(".tag-list");
  bookmark.tags.forEach((tag) => {
    const element = document.createElement("span");
    element.className = "tag";
    element.textContent = `# ${tag}`;
    tags.append(element);
  });

  const link = card.querySelector(".source-link");
  link.href = bookmark.url;
  link.setAttribute("aria-label", `Open source: ${bookmark.title}`);
  return card;
}

function render() {
  const bookmarks = readBookmarks().sort((a, b) => b.createdAt - a.createdAt);
  const allBookmarks = [...bookmarks, exampleBookmark];
  list.replaceChildren(...allBookmarks.map(createCard));
  document.querySelector("#bookmark-count").textContent = allBookmarks.length;
  document.querySelector("#bookmark-word").textContent = wordForBookmarks(allBookmarks.length);
}

function showPreview() {
  const url = form.url.value.trim();
  if (!form.url.reportValidity()) return;

  const domain = domainFromUrl(url);
  document.querySelector("#preview-domain").textContent = domain;
  document.querySelector("#preview-copy").textContent = form.title.value.trim() || "Add a title, description and your own note below.";
  const cover = form.cover.value.trim();
  const previewCover = document.querySelector("#preview-cover");
  previewCover.style.backgroundImage = cover ? `linear-gradient(#17332733, #17332766), url("${cover.replaceAll('"', "%22")}")` : "";
  previewPanel.classList.remove("is-hidden");

  if (!form.title.value.trim()) {
    form.title.value = domain.charAt(0).toUpperCase() + domain.slice(1);
    form.title.focus();
    form.title.select();
  }
}

previewButton.addEventListener("click", showPreview);

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;

  const bookmark = {
    id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    url: form.url.value.trim(),
    title: form.title.value.trim(),
    description: form.description.value.trim(),
    cover: form.cover.value.trim(),
    note: form.note.value.trim(),
    tags: form.tags.value.split(",").map((tag) => tag.trim()).filter(Boolean),
    createdAt: Date.now(),
    example: false,
  };

  const bookmarks = readBookmarks();
  bookmarks.push(bookmark);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
  form.reset();
  previewPanel.classList.add("is-hidden");
  formMessage.textContent = "Bookmark saved — it is now at the top of your library.";
  render();
  document.querySelector("#library-title").scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => { formMessage.textContent = ""; }, 5000);
});

document.querySelectorAll("[data-focus-form]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector("#composer-title").scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => form.url.focus(), 400);
  });
});

render();
