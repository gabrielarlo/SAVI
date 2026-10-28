/**
 * LocalRAG admin UI: sign-in, document table, upload, chunk preview, delete.
 *
 * The admin secret lives in sessionStorage only and travels as X-Admin-Secret.
 * Every piece of document or chunk text is rendered with textContent.
 */

const SECRET_KEY = "localrag.adminSecret";

export const getSecret = () => sessionStorage.getItem(SECRET_KEY);

export function signOut() {
  sessionStorage.removeItem(SECRET_KEY);
  window.location.replace("/console/signin");
}

export async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...(options.headers || {}), "X-Admin-Secret": getSecret() || "" },
  });

  if (response.status === 401) {
    signOut();
    throw new Error("Your session expired. Sign in again.");
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.error?.message || `Request failed (${response.status})`);
  }
  return body;
}

export function showMessage(element, text, isError) {
  element.textContent = text;
  element.className = isError
    ? "text-sm text-red-500"
    : "text-sm text-green-500";
}

export function formatDate(value) {
  if (!value) return "";
  const date = new Date(`${value.replace(" ", "T")}Z`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

// Operators see tenant names, never raw ids. Names that collide keep a short
// id suffix so two tenants called "acme" stay distinguishable.
let tenantLabels = new Map();

export function setTenants(tenants) {
  const counts = new Map();
  for (const tenant of tenants) {
    counts.set(tenant.name, (counts.get(tenant.name) || 0) + 1);
  }
  tenantLabels = new Map(
    tenants.map((tenant) => [
      tenant.id,
      counts.get(tenant.name) > 1
        ? `${tenant.name} (${tenant.id.slice(0, 8)})`
        : tenant.name,
    ]),
  );
}

export const tenantLabel = (id) => tenantLabels.get(id) || "Unknown tenant";

function fillTenantSelect(select, tenants, emptyLabel) {
  const current = select.value;
  select.replaceChildren(new Option(emptyLabel, ""));
  for (const tenant of tenants) {
    select.append(new Option(tenantLabel(tenant.id), tenant.id));
  }
  select.value = tenants.some((tenant) => tenant.id === current) ? current : "";
}

function initSignin() {
  const form = document.getElementById("signin-form");
  const input = document.getElementById("secret");
  const submit = document.getElementById("signin-submit");
  const error = document.getElementById("signin-error");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const secret = input.value.trim();
    if (!secret) {
      error.textContent = "Enter the admin secret.";
      error.classList.remove("hidden");
      return;
    }

    submit.disabled = true;
    error.classList.add("hidden");
    try {
      const response = await fetch("/admin/tenants", {
        headers: { "X-Admin-Secret": secret },
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(
          body?.error?.message || `Request failed (${response.status})`,
        );
      }
      sessionStorage.setItem(SECRET_KEY, secret);
      window.location.replace("/console/documents");
    } catch (failure) {
      error.textContent = failure.message;
      error.classList.remove("hidden");
      submit.disabled = false;
    }
  });
}

function initDocuments() {
  if (!getSecret()) {
    window.location.replace("/console/signin");
    return;
  }

  const body = document.getElementById("documents-body");
  const empty = document.getElementById("documents-empty");
  const filter = document.getElementById("filter-tenant");
  const uploadForm = document.getElementById("upload-form");
  const uploadTenant = document.getElementById("upload-tenant");
  const uploadTitle = document.getElementById("upload-title");
  const uploadFile = document.getElementById("upload-file");
  const uploadSubmit = document.getElementById("upload-submit");
  const uploadMessage = document.getElementById("upload-message");
  const dialog = document.getElementById("chunk-dialog");

  async function load() {
    // Archived tenants' documents keep their label; selects offer active only.
    const tenants = await request("/admin/tenants?include_archived=true");
    setTenants(tenants);
    const active = tenants.filter((tenant) => !tenant.archived_at);
    fillTenantSelect(filter, active, "All tenants");
    fillTenantSelect(uploadTenant, active, "Select a tenant");

    const query = filter.value
      ? `?tenant_id=${encodeURIComponent(filter.value)}`
      : "";
    const documents = await request(`/admin/documents${query}`);
    render(documents);
  }

  function render(documents) {
    body.replaceChildren();
    empty.classList.toggle("hidden", documents.length > 0);

    for (const doc of documents) {
      const row = document.createElement("tr");
      row.className = "border-b border-gray-100 last:border-0 dark:border-gray-800";

      const title = document.createElement("td");
      title.className = "px-5 py-4 text-sm font-medium text-gray-800 dark:text-white/90";
      title.textContent = doc.title;

      const tenant = document.createElement("td");
      tenant.className = "px-5 py-4 text-sm text-gray-500 dark:text-gray-400";
      tenant.textContent = tenantLabel(doc.tenant_id);

      const chunks = document.createElement("td");
      chunks.className = "px-5 py-4 text-sm text-gray-800 dark:text-white/90";
      chunks.textContent = String(doc.chunk_count);

      const created = document.createElement("td");
      created.className = "px-5 py-4 text-sm whitespace-nowrap text-gray-500 dark:text-gray-400";
      created.textContent = formatDate(doc.created_at);

      const actions = document.createElement("td");
      actions.className = "px-5 py-4 text-right text-sm whitespace-nowrap";

      const view = document.createElement("button");
      view.type = "button";
      view.textContent = "View";
      view.className =
        "mr-2 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-white/5";
      view.addEventListener("click", () => openDocument(doc.id));

      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Delete";
      remove.className =
        "rounded-lg border border-red-500 px-3 py-1.5 text-sm font-medium text-red-500 transition hover:bg-red-50 dark:border-red-500/40 dark:hover:bg-red-500/15";
      remove.addEventListener("click", () => deleteDocument(doc));

      actions.append(view, remove);
      row.append(title, tenant, chunks, created, actions);
      body.append(row);
    }
  }

  async function openDocument(id) {
    try {
      const doc = await request(`/admin/documents/${encodeURIComponent(id)}`);
      document.getElementById("chunk-dialog-title").textContent = doc.title;
      document.getElementById("chunk-dialog-meta").textContent =
        `${doc.chunks.length} chunk(s) · ${tenantLabel(doc.tenant_id)}`;

      const list = document.getElementById("chunk-list");
      list.replaceChildren();
      for (const chunk of doc.chunks) {
        const card = document.createElement("div");
        card.className =
          "rounded-lg border border-gray-200 p-3 dark:border-gray-800";

        const heading = document.createElement("p");
        heading.className =
          "mb-2 text-xs font-medium tracking-wide text-gray-500 uppercase dark:text-gray-400";
        heading.textContent = `Chunk ${chunk.chunk_index}`;

        const text = document.createElement("p");
        text.className =
          "text-sm whitespace-pre-wrap text-gray-700 dark:text-gray-300";
        text.textContent = chunk.content;

        card.append(heading, text);
        list.append(card);
      }
      document
        .getElementById("chunk-empty")
        .classList.toggle("hidden", doc.chunks.length > 0);
      dialog.showModal();
    } catch (failure) {
      window.alert(failure.message);
    }
  }

  async function deleteDocument(doc) {
    if (!window.confirm(`Delete "${doc.title}" and all of its chunks?`)) {
      return;
    }
    try {
      await request(`/admin/documents/${encodeURIComponent(doc.id)}`, {
        method: "DELETE",
      });
      await load();
    } catch (failure) {
      window.alert(failure.message);
    }
  }

  filter.addEventListener("change", () => {
    load().catch((failure) => window.alert(failure.message));
  });

  document.getElementById("refresh").addEventListener("click", () => {
    load().catch((failure) => window.alert(failure.message));
  });

  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!uploadTenant.value) {
      showMessage(uploadMessage, "Select a tenant first.", true);
      return;
    }
    if (!uploadFile.files.length) {
      showMessage(uploadMessage, "Choose a file to upload.", true);
      return;
    }

    const form = new FormData();
    form.append("tenant_id", uploadTenant.value);
    if (uploadTitle.value.trim()) form.append("title", uploadTitle.value.trim());
    form.append("file", uploadFile.files[0]);

    uploadSubmit.disabled = true;
    showMessage(uploadMessage, "Uploading…", false);
    try {
      const created = await request("/admin/documents/upload", {
        method: "POST",
        body: form,
      });
      showMessage(uploadMessage, `Ingested with ${created.chunks} chunk(s).`, false);
      uploadForm.reset();
      await load();
    } catch (failure) {
      showMessage(uploadMessage, failure.message, true);
    } finally {
      uploadSubmit.disabled = false;
    }
  });

  document.getElementById("chunk-dialog-close").addEventListener("click", () => {
    dialog.close();
  });

  document.getElementById("sign-out").addEventListener("click", () => {
    sessionStorage.removeItem(SECRET_KEY);
  });

  load().catch((failure) => window.alert(failure.message));
}

function init() {
  if (document.getElementById("signin-form")) {
    initSignin();
  } else if (document.getElementById("documents-body")) {
    initDocuments();
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
