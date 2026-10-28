/**
 * LocalRAG admin UI: tenant management (create, rename, archive — no delete).
 *
 * Shares the sign-in/fetch helpers from documents.js; same secret and
 * textContent-only rendering rules apply.
 */

import {
  getSecret,
  getSessionToken,
  request,
  setTenants,
  signOut,
  tenantLabel,
  formatDate,
} from "./documents.js";function statusBadge(tenant) {
  const badge = document.createElement("span");
  if (tenant.archived_at) {
    badge.className =
      "rounded-full bg-gray-100 px-2.5 py-0.5 text-sm text-gray-600 dark:bg-gray-800 dark:text-gray-400";
    badge.textContent = "Archived";
  } else {
    badge.className =
      "rounded-full bg-green-100 px-2.5 py-0.5 text-sm text-green-700 dark:bg-green-500/15 dark:text-green-500";
    badge.textContent = "Active";
  }
  return badge;
}

function button(label, classes) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = classes;
  return button;
}

const QUIET_BUTTON =
  "rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-white/5";
const WARN_BUTTON =
  "rounded-lg border border-red-500 px-3 py-1.5 text-sm font-medium text-red-500 transition hover:bg-red-50 dark:border-red-500/40 dark:hover:bg-red-500/15";

function initTenants() {
  if (!getSecret() && !getSessionToken()) {
    window.location.replace("/auth/signin");
    return;
  }

  const body = document.getElementById("tenants-body");
  const empty = document.getElementById("tenants-empty");
  const filter = document.getElementById("filter-status");
  const createForm = document.getElementById("create-form");
  const createName = document.getElementById("create-name");
  const createMessage = document.getElementById("create-message");
  const createDialog = document.getElementById("create-dialog");
  const keyDialog = document.getElementById("key-dialog");
  const keyName = document.getElementById("key-name");
  const keyValue = document.getElementById("key-value");
  const editDialog = document.getElementById("edit-dialog");
  const editForm = document.getElementById("edit-form");
  const editName = document.getElementById("edit-name");
  const editMessage = document.getElementById("edit-message");

  let tenantRows = [];

  async function load() {
    const tenants = await request("/admin/tenants?include_archived=true");
    setTenants(tenants);
    tenantRows = tenants;
    render();
  }

  function matchesFilter(tenant) {
    if (filter.value === "active") return !tenant.archived_at;
    if (filter.value === "archived") return Boolean(tenant.archived_at);
    return true;
  }

  function render() {
    body.replaceChildren();
    const visible = tenantRows.filter(matchesFilter);
    empty.classList.toggle("hidden", visible.length > 0);

    for (const tenant of visible) {
      const row = document.createElement("tr");
      row.className = "border-b border-gray-100 last:border-0 dark:border-gray-800";

      const name = document.createElement("td");
      name.className =
        "px-5 py-4 text-sm font-medium text-gray-800 dark:text-white/90";
      name.textContent = tenantLabel(tenant.id);

      const shortId = document.createElement("td");
      shortId.className =
        "px-5 py-4 font-mono text-xs text-gray-500 dark:text-gray-400";
      shortId.textContent = tenant.id.slice(0, 8);

      const created = document.createElement("td");
      created.className =
        "px-5 py-4 text-sm whitespace-nowrap text-gray-500 dark:text-gray-400";
      created.textContent = formatDate(tenant.created_at);

      const status = document.createElement("td");
      status.className = "px-5 py-4";
      status.append(statusBadge(tenant));

      const actions = document.createElement("td");
      actions.className = "px-5 py-4 text-right text-sm whitespace-nowrap";

      const rename = button("Edit", `mr-2 ${QUIET_BUTTON}`);
      rename.addEventListener("click", () => openEdit(tenant));

      actions.append(rename);
      if (!tenant.archived_at) {
        const archive = button("Archive", WARN_BUTTON);
        archive.addEventListener("click", () => archiveTenant(tenant));
        actions.append(archive);
      }

      row.append(name, shortId, created, status, actions);
      body.append(row);
    }
  }

  function openEdit(tenant) {
    editName.value = tenant.name;
    editMessage.classList.add("hidden");
    editDialog.dataset.tenantId = tenant.id;
    editDialog.showModal();
  }

  async function archiveTenant(tenant) {
    if (!window.confirm(`Archive "${tenant.name}"? Its API key will stop working.`)) {
      return;
    }
    try {
      await request(
        `/admin/tenants/${encodeURIComponent(tenant.id)}/archive`,
        { method: "POST" },
      );
      await load();
    } catch (failure) {
      window.alert(failure.message);
    }
  }

  async function copyKey() {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(keyValue.textContent);
      }
    } catch {
      // Non-secure origins block the clipboard API; the key stays selectable.
    }
  }

  createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.confirm("Create this tenant?")) return;
    const name = createName.value.trim();
    if (!name) {
      showMessage(createMessage, "Enter a tenant name.", true);
      return;
    }
    createMessage.classList.add("hidden");
    try {
      const created = await request("/admin/tenants", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name }),
      });
      createForm.reset();
      createDialog.close();
      // The key is shown exactly once, in this dialog only.
      keyName.textContent = created.name;
      keyValue.textContent = created.api_key;
      keyDialog.showModal();
      await load();
    } catch (failure) {
      showMessage(createMessage, failure.message, true);
    }
  });

  editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.confirm("Save changes to this tenant?")) return;
    const name = editName.value.trim();
    const id = editDialog.dataset.tenantId;
    if (!name) {
      showMessage(editMessage, "Enter a tenant name.", true);
      return;
    }
    try {
      await request(`/admin/tenants/${encodeURIComponent(id)}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name }),
      });
      editForm.reset();
      editDialog.close();
      await load();
    } catch (failure) {
      showMessage(editMessage, failure.message, true);
    }
  });

  filter.addEventListener("change", render);
  document
    .getElementById("create-open")
    .addEventListener("click", () => createDialog.showModal());
  document
    .getElementById("create-dialog-close")
    .addEventListener("click", () => createDialog.close());
  document
    .getElementById("key-dialog-close")
    .addEventListener("click", () => keyDialog.close());
  document
    .getElementById("edit-dialog-close")
    .addEventListener("click", () => editDialog.close());
  document
    .getElementById("copy-key")
    .addEventListener("click", () => void copyKey());
  document.getElementById("refresh").addEventListener("click", () => {
    load().catch((failure) => window.alert(failure.message));
  });
  document.getElementById("sign-out").addEventListener("click", signOut);

  load().catch((failure) => window.alert(failure.message));
}

function init() {
  if (document.getElementById("tenants-body")) {
    initTenants();
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
