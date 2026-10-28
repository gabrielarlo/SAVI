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
  const editRotate = document.getElementById("edit-rotate");
  const editMessage = document.getElementById("edit-message");

  let tenantRows = [];

  async function load() {
    const tenants = await request("/admin/tenants?include_archived=true");
    await Promise.all(
      tenants.map(async (tenant) => {
        try {
          const res = await request(`/admin/tenants/${encodeURIComponent(tenant.id)}/api-key`);
          tenant.api_key = res.api_key;
        } catch (e) {
          tenant.api_key = null;
        }
      }),
    );
    setTenants(tenants);
    tenantRows = tenants;
    render();
  }

  function isExpiring(tenant) {
    if (!tenant.api_key_expires_at) return false;
    const exp = new Date(String(tenant.api_key_expires_at).replace(" ", "T") + "Z");
    if (Number.isNaN(exp.getTime())) return false;
    const now = new Date();
    const in30 = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    return exp <= in30;
  }

  function matchesFilter(tenant) {
    if (filter.value === "active") return !tenant.archived_at;
    if (filter.value === "archived") return Boolean(tenant.archived_at);
    if (filter.value === "expiring") return isExpiring(tenant);
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

      const apiKeyCell = document.createElement("td");
      apiKeyCell.className = "px-5 py-4 font-mono text-xs text-gray-500 dark:text-gray-400";
      const masked = document.createElement("span");
      masked.textContent = tenant.api_key
        ? tenant.api_key.slice(0, 8) + "..." + tenant.api_key.slice(-4)
        : "—";
      apiKeyCell.append(masked);

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

      const copyKey = button("Copy key", `mr-2 ${QUIET_BUTTON}`);
      copyKey.addEventListener("click", async () => {
        try {
          const res = await request(`/admin/tenants/${encodeURIComponent(tenant.id)}/api-key`);
          if (navigator.clipboard) await navigator.clipboard.writeText(res.api_key);
          window.alert("API key copied.");
        } catch (e) {
          window.alert(e.message);
        }
      });

      actions.append(rename, copyKey);

      if (!tenant.archived_at) {
        const regen = button("Regenerate", `mr-2 ${QUIET_BUTTON}`);
        regen.addEventListener("click", async () => {
          if (!window.confirm(`Regenerate API key for "${tenant.name}"? The old key stops working.`)) return;
          try {
            const res = await request(`/admin/tenants/${encodeURIComponent(tenant.id)}/regenerate-key`, { method: "POST" });
            keyName.textContent = tenant.name;
            keyValue.textContent = res.api_key;
            keyDialog.showModal();
            load();
          } catch (e) {
            window.alert(e.message);
          }
        });
        actions.append(regen);

        const archive = button("Archive", WARN_BUTTON);
        archive.addEventListener("click", () => archiveTenant(tenant));
        actions.append(archive);
      }

      row.append(name, shortId, apiKeyCell, created, status, actions);
      body.append(row);
    }
  }

  function openEdit(tenant) {
    editName.value = tenant.name;
    if (editRotate) {
      editRotate.value = tenant.rotate_days == null ? "" : String(tenant.rotate_days);
    }
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
      const rotateRaw = editRotate ? editRotate.value : "";
      const rotateDays = rotateRaw === "" ? null : Number(rotateRaw);
      await request(`/admin/tenants/${encodeURIComponent(id)}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, rotate_days: rotateDays }),
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

  const params = new URLSearchParams(window.location.search);
  const initialFilter = params.get("filter");
  if (initialFilter && ["all", "active", "archived", "expiring"].includes(initialFilter)) {
    filter.value = initialFilter;
  }

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
