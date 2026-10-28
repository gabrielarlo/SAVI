import { getSecret, request, signOut, wirePasswordToggle } from "./documents.js";

function badge(user) {
  const el = document.createElement("span");
  if (user.archived_at) {
    el.className = "rounded-full bg-gray-100 px-2.5 py-0.5 text-sm text-gray-600 dark:bg-gray-800 dark:text-gray-400";
    el.textContent = "Archived";
  } else {
    el.className = "rounded-full bg-green-100 px-2.5 py-0.5 text-sm text-green-700 dark:bg-green-500/15 dark:text-green-500";
    el.textContent = "Active";
  }
  return el;
}

function button(label, cls) {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = label;
  b.className = cls;
  return b;
}

const Q = "rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-white/5";
const W = "rounded-lg border border-red-500 px-3 py-1.5 text-sm font-medium text-red-500 transition hover:bg-red-50 dark:border-red-500/40 dark:hover:bg-red-500/15";

function initUsers() {
  if (!getSecret() && !sessionStorage.getItem("localrag.sessionToken")) {
    window.location.replace("/auth/signin");
    return;
  }

  const body = document.getElementById("users-body");
  const empty = document.getElementById("users-empty");
  const createDialog = document.getElementById("create-dialog");
  const editDialog = document.getElementById("edit-dialog");
  const createForm = document.getElementById("create-form");
  const editForm = document.getElementById("edit-form");
  const createMessage = document.getElementById("create-message");
  const editMessage = document.getElementById("edit-message");

  wirePasswordToggle(
    document.getElementById("create-password"),
    document.getElementById("create-password-toggle"),
    document.getElementById("create-password-toggle-icon"),
  );
  wirePasswordToggle(
    document.getElementById("edit-password"),
    document.getElementById("edit-password-toggle"),
    document.getElementById("edit-password-toggle-icon"),
  );

  let rows = [];

  async function load() {
    rows = await request("/admin/users?include_archived=true");
    render();
  }

  function render() {
    body.replaceChildren();
    empty.classList.toggle("hidden", rows.length > 0);
    for (const user of rows) {
      const tr = document.createElement("tr");
      tr.className = "border-b border-gray-100 last:border-0 dark:border-gray-800";

      const name = document.createElement("td");
      name.className = "px-5 py-4 text-sm font-medium text-gray-800 dark:text-white/90";
      name.textContent = user.username;

      const role = document.createElement("td");
      role.className = "px-5 py-4 text-sm text-gray-500 dark:text-gray-400";
      role.textContent = user.role === "account_manager" ? "Account Manager (Tenant Manager)" : "Administrator";

      const created = document.createElement("td");
      created.className = "px-5 py-4 text-sm whitespace-nowrap text-gray-500 dark:text-gray-400";
      created.textContent = user.created_at;

      const status = document.createElement("td");
      status.className = "px-5 py-4";
      status.append(badge(user));

      const actions = document.createElement("td");
      actions.className = "px-5 py-4 text-right text-sm whitespace-nowrap";
      const edit = button("Edit", `mr-2 ${Q}`);
      edit.addEventListener("click", () => openEdit(user));
      actions.append(edit);
      if (!user.archived_at) {
        const archive = button("Archive", W);
        archive.addEventListener("click", () => archiveUser(user));
        actions.append(archive);
      }
      tr.append(name, role, created, status, actions);
      body.append(tr);
    }
  }

  function openEdit(user) {
    document.getElementById("edit-username").value = user.username;
    document.getElementById("edit-role").value = user.role;
    document.getElementById("edit-password").value = "";
    editDialog.dataset.userId = user.id;
    editMessage.classList.add("hidden");
    editDialog.showModal();
  }

  async function archiveUser(user) {
    if (!window.confirm(`Archive "${user.username}"? They will no longer be able to sign in.`)) return;
    try {
      await request(`/admin/users/${encodeURIComponent(user.id)}/archive`, { method: "POST" });
      await load();
    } catch (e) { window.alert(e.message); }
  }

  createForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      username: document.getElementById("create-username").value.trim(),
      password: document.getElementById("create-password").value,
      role: document.getElementById("create-role").value,
    };
    createMessage.classList.add("hidden");
    try {
      await request("/admin/users", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      createForm.reset();
      createDialog.close();
      await load();
    } catch (err) { createMessage.textContent = err.message; createMessage.classList.remove("hidden"); }
  });

  editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = editDialog.dataset.userId;
    const payload = {
      username: document.getElementById("edit-username").value.trim(),
      role: document.getElementById("edit-role").value,
    };
    const pw = document.getElementById("edit-password").value;
    if (pw) payload.password = pw;
    editMessage.classList.add("hidden");
    try {
      await request(`/admin/users/${encodeURIComponent(id)}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      editForm.reset();
      editDialog.close();
      await load();
    } catch (err) { editMessage.textContent = err.message; editMessage.classList.remove("hidden"); }
  });

  document.getElementById("create-open").addEventListener("click", () => createDialog.showModal());
  document.getElementById("create-dialog-close").addEventListener("click", () => createDialog.close());
  document.getElementById("edit-dialog-close").addEventListener("click", () => editDialog.close());
  document.getElementById("refresh").addEventListener("click", () => load().catch(e => window.alert(e.message)));
  document.getElementById("sign-out").addEventListener("click", signOut);

  load().catch(e => window.alert(e.message));
}

function init() {
  if (document.getElementById("users-body")) initUsers();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
