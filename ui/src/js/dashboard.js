import { getSecret, getSessionToken, request } from "./documents.js";

const LABELS = {
  tenants: "Tenants",
  tenants_active: "Active tenants",
  tenants_archived: "Archived tenants",
  documents: "Documents",
  chunks: "Chunks",
  users: "Users",
  users_active: "Active users",
  users_archived: "Archived users",
  inquiries: "Inquiries",
  api_keys_blue: "API keys (healthy)",
  api_keys_orange: "API keys (expiring soon)",
  api_keys_red: "API keys (urgent)",
};

const COLORS = {
  api_keys_blue: "text-blue-600 dark:text-blue-400",
  api_keys_orange: "text-orange-500 dark:text-orange-400",
  api_keys_red: "text-red-600 dark:text-red-400",
};

const SECTIONS = {
  tenants: "section-overview",
  documents: "section-overview",
  chunks: "section-overview",
  tenants_active: "section-tenants",
  tenants_archived: "section-tenants",
  users: "section-users",
  users_active: "section-users",
  users_archived: "section-users",
  inquiries: "section-activity",
  api_keys_blue: "section-apikeys",
  api_keys_orange: "section-apikeys",
  api_keys_red: "section-apikeys",
};

const LINKS = {
  tenants: "/console/tenants",
  tenants_active: "/console/tenants",
  tenants_archived: "/console/tenants?filter=archived",
  documents: "/console/documents",
  chunks: "/console/documents",
  users: "/console/users",
  users_active: "/console/users",
  users_archived: "/console/users",
  inquiries: "/console",
  api_keys_blue: "/console/tenants",
  api_keys_orange: "/console/tenants?filter=expiring",
  api_keys_red: "/console/tenants?filter=expiring",
};

const ICONS = {
  tenants: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  documents: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
  chunks: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
  users: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  inquiries: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  api_keys_blue: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
  api_keys_orange: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
  api_keys_red: '<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
};

function card(label, value, colorClass, key) {
  const href = LINKS[key];
  const wrap = href ? document.createElement("a") : document.createElement("div");
  if (href) wrap.href = href;
  wrap.className =
    "group block rounded-2xl border border-gray-200 bg-white p-6 transition-shadow hover:shadow-md dark:border-gray-800 dark:bg-white/[0.03]";

  const top = document.createElement("div");
  top.className = "flex items-center justify-between";

  const labelEl = document.createElement("p");
  labelEl.className = "text-sm text-gray-500 dark:text-gray-400";
  labelEl.textContent = label;

  const iconWrap = document.createElement("span");
  iconWrap.className = "text-gray-400 group-hover:text-brand-500";
  iconWrap.innerHTML = ICONS[key] || "";

  top.append(labelEl, iconWrap);

  const valueEl = document.createElement("p");
  valueEl.className = `mt-2 text-2xl font-semibold ${colorClass || "text-gray-800 dark:text-white/90"}`;
  valueEl.textContent = String(value);

  wrap.append(top, valueEl);
  return wrap;
}

function initDashboard() {
  if (!getSecret() && !getSessionToken()) {
    window.location.replace("/auth/signin");
    return;
  }

  const error = document.getElementById("stats-error");
  const containers = {
    "section-overview": document.getElementById("section-overview"),
    "section-tenants": document.getElementById("section-tenants"),
    "section-users": document.getElementById("section-users"),
    "section-activity": document.getElementById("section-activity"),
    "section-apikeys": document.getElementById("section-apikeys"),
  };

  let timer = null;

  function skeleton() {
    for (const c of Object.values(containers)) {
      if (!c) continue;
      c.replaceChildren();
      for (let i = 0; i < 2; i++) {
        const wrap = document.createElement("div");
        wrap.className =
          "rounded-2xl border border-gray-200 bg-white p-6 animate-pulse dark:border-gray-800 dark:bg-white/[0.03]";
        const bar = document.createElement("div");
        bar.className = "h-4 w-24 rounded bg-gray-200 dark:bg-gray-700";
        const num = document.createElement("div");
        num.className = "mt-4 h-8 w-16 rounded bg-gray-200 dark:bg-gray-700";
        wrap.append(bar, num);
        c.append(wrap);
      }
    }
  }

  async function load() {
    try {
      const stats = await request("/admin/stats");
      for (const c of Object.values(containers)) if (c) c.replaceChildren();
      for (const key of Object.keys(LABELS)) {
        if (!Object.prototype.hasOwnProperty.call(stats, key)) continue;
        const section = SECTIONS[key];
        const container = containers[section];
        if (!container) continue;
        container.append(card(LABELS[key], stats[key], COLORS[key], key));
      }
      // Inquiry per day: show latest day's count as a card.
      const perDay = Array.isArray(stats.inquiries_per_day)
        ? stats.inquiries_per_day
        : [];
      if (perDay.length) {
        const latest = perDay[perDay.length - 1];
        const container = containers["section-activity"];
        if (container) container.append(card("Inquiries today", latest.count, null, "inquiries"));
      }
      if (error) error.classList.add("hidden");
    } catch (failure) {
      if (error) {
        error.textContent = failure.message;
        error.classList.remove("hidden");
      }
    }
  }

  function start() {
    if (timer) return;
    skeleton();
    load();
    timer = setInterval(load, 4000);
  }

  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
    else start();
  });

  start();
}

function init() {
  if (document.getElementById("section-overview")) initDashboard();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}