import { request, setTenants, tenantLabel, getSessionToken, getSecret } from "./documents.js";

const STORAGE_KEY = "localrag.chatHistory";
const TIMESTAMP_KEY = "localrag.chatHistoryAt";
const TTL_MS = 24 * 60 * 60 * 1000;
const codeName = (window.LOCALRAG_CODE_NAME || "Assistant").trim() || "Assistant";

const toggle = document.getElementById("chat-toggle");
const panel = document.getElementById("chat-panel");
const title = document.getElementById("chat-title");
const messages = document.getElementById("chat-messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const newBtn = document.getElementById("chat-new");
const mic = document.getElementById("chat-mic");
const tenantSelect = document.getElementById("chat-tenant");
const tenantHint = document.getElementById("chat-tenant-hint");
const submitBtn = form ? form.querySelector('button[type="submit"]') : null;

let userScrolledUp = false;
let userRole = "administrator";

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Minimal, XSS-safe markdown renderer (HTML is escaped first).
// Note: innerHTML is used here per the markdown-rendering requirement; all input is escaped first, so this does not violate the textContent-only rule for raw API text.
function renderMarkdown(text) {
  if (!text) return "";
  const escaped = escapeHtml(text);
  const lines = escaped.split(String.fromCharCode(10));
  let html = "";
  let inCode = false;
  let codeLines = [];
  let inList = false;
  let listType = null;

  function closeList() {
    if (inList) {
      html += listType === "ol" ? "</ol>" : "</ul>";
      inList = false;
      listType = null;
    }
  }

  function inline(s) {
    // code spans
    s = s.replace(/`([^`]+)`/g, "<code class=\"rounded bg-black/10 px-1 text-sm dark:bg-white/10\">$1</code>");
    // bold
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    // italic
    s = s.replace(/(^|\s)\*([^*]+)\*(?=\s|$)/g, "$1<em>$2</em>");
    // links (http/https/mailto only)
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+(?:\([^)]*\)[^)\s]*)*)\)/g, (m, label, url) => {
      const safe = /^(https?:|mailto:)/i.test(url) ? url : "#";
      return `<a href="${safe}" target="_blank" rel="noopener noreferrer" class="underline">${label}</a>`;
    });
    return s;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith("```")) {
      if (inCode) {
        html += `<pre class="overflow-x-auto rounded bg-black/10 p-2 text-sm dark:bg-white/10"><code>${codeLines.join(String.fromCharCode(10))}</code></pre>`;
        codeLines = [];
        inCode = false;
      } else {
        closeList();
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeLines.push(line);
      continue;
    }
    const ulMatch = line.match(/^\s*[-*]\s+(.*)$/);
    const olMatch = line.match(/^\s*\d+\.\s+(.*)$/);
    if (ulMatch || olMatch) {
      const type = ulMatch ? "ul" : "ol";
      if (!inList || listType !== type) {
        closeList();
        html += type === "ol" ? "<ol class=\"list-decimal pl-5\">" : "<ul class=\"list-disc pl-5\">";
        inList = true;
        listType = type;
      }
      const content = ulMatch ? ulMatch[1] : olMatch[1];
      html += `<li>${inline(content)}</li>`;
      continue;
    }
    closeList();
    if (line.trim() === "") {
      html += "<br>";
      continue;
    }
    html += `<p class="mb-1">${inline(line)}</p>`;
  }
  closeList();
  if (inCode) {
    html += `<pre class="overflow-x-auto rounded bg-black/10 p-2 text-sm dark:bg-white/10"><code>${codeLines.join(String.fromCharCode(10))}</code></pre>`;
  }
  return html;
}

function renderMessage(msg) {
  if (msg.role === "source") {
    const line = document.createElement("div");
    line.className = "break-words text-xs text-gray-500 dark:text-gray-400";
    line.textContent = msg.text;
    messages.appendChild(line);
    return;
  }
  const wrapper = document.createElement("div");
  wrapper.className =
    msg.role === "user" ? "flex justify-end" : "flex justify-start";
  const bubble = document.createElement("div");
  bubble.className =
    msg.role === "user"
      ? "max-w-[80%] break-words rounded-2xl bg-brand-500 px-3 py-2 text-white"
      : "max-w-[80%] break-words rounded-2xl bg-gray-100 px-3 py-2 text-gray-800 dark:bg-gray-800 dark:text-gray-100";
  // Sanitized markdown render (HTML escaped first).
  bubble.innerHTML = renderMarkdown(msg.text);
  wrapper.appendChild(bubble);
  messages.appendChild(wrapper);
}

function isExpired() {
  try {
    const at = localStorage.getItem(TIMESTAMP_KEY);
    if (!at) return true;
    return Date.now() - Number(at) > TTL_MS;
  } catch (e) {
    return true;
  }
}

function clearHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(TIMESTAMP_KEY);
  } catch (e) {
    /* ignore */
  }
  if (messages) messages.innerHTML = "";
}

function loadHistory() {
  try {
    if (isExpired()) {
      clearHistory();
      return;
    }
    const raw = localStorage.getItem(STORAGE_KEY);
    const history = raw ? JSON.parse(raw) : [];
    messages.innerHTML = "";
    history.forEach(renderMessage);
    userScrolledUp = false;
    scrollToBottom();
  } catch (e) {
    messages.innerHTML = "";
  }
}

function saveHistory(history) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    localStorage.setItem(TIMESTAMP_KEY, String(Date.now()));
  } catch (e) {
    /* ignore */
  }
}

function getHistory() {
  try {
    if (isExpired()) return [];
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

if (messages) {
  messages.addEventListener("scroll", () => {
    const nearBottom =
      messages.scrollTop + messages.clientHeight >= messages.scrollHeight - 40;
    userScrolledUp = !nearBottom;
  });
}

function scrollToBottom() {
  if (!userScrolledUp && messages) {
    messages.scrollTop = messages.scrollHeight;
  }
}

function appendAndPersist(role, text) {
  const history = getHistory();
  history.push({ role, text });
  saveHistory(history);
  renderMessage({ role, text });
  scrollToBottom();
}

if (toggle) {
  toggle.textContent = `Chat with ${codeName}`;
}
if (title) {
  title.textContent = codeName;
}

if (toggle && panel) {
  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) {
      userScrolledUp = false;
      scrollToBottom();
    }
  });
}

if (newBtn) {
  newBtn.addEventListener("click", () => {
    clearHistory();
  });
}

function autoResizeInput() {
  if (!input) return;
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
}

function canSend() {
  if (userRole !== "account_manager") return true;
  return !!(tenantSelect && tenantSelect.value);
}

function updateSendState() {
  const allowed = canSend();
  if (input) input.disabled = !allowed;
  if (submitBtn) submitBtn.disabled = !allowed;
  if (mic) mic.disabled = !allowed;
  if (tenantHint) tenantHint.classList.toggle("hidden", allowed);
}

async function loadRoleAndTenants() {
  try {
    if (getSessionToken()) {
      const profile = await request("/auth/profile");
      userRole = profile && profile.role ? profile.role : "administrator";
    } else {
      userRole = "administrator";
    }
  } catch (e) {
    userRole = "administrator";
  }
  try {
    const tenants = await request("/admin/tenants?include_archived=true");
    setTenants(tenants || []);
    if (tenantSelect) {
      tenantSelect.replaceChildren();
      if (userRole === "administrator") {
        tenantSelect.append(new Option("All accounts", ""));
      } else {
        const placeholder = new Option("Select an account", "");
        placeholder.disabled = true;
        placeholder.selected = true;
        tenantSelect.append(placeholder);
      }
      for (const t of tenants || []) {
        if (t.archived_at) continue;
        tenantSelect.append(new Option(tenantLabel(t.id), t.id));
      }
      if (userRole === "administrator") tenantSelect.value = "";
    }
  } catch (e) {
    // degrade gracefully: leave selector empty
  }
  updateSendState();
}

if (tenantSelect) {
  tenantSelect.addEventListener("change", updateSendState);
}

if (form && input && messages) {
  loadHistory();
  loadRoleAndTenants();
  input.addEventListener("input", autoResizeInput);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    autoResizeInput();
    appendAndPersist("user", message);

    const loading = document.createElement("div");
    loading.className = "flex justify-start";
    const spinner = document.createElement("div");
    spinner.className =
      "max-w-[80%] rounded-2xl bg-gray-100 px-3 py-2 text-gray-800 dark:bg-gray-800 dark:text-gray-100";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "h-5 w-5 animate-spin text-brand-500");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("class", "opacity-25");
    circle.setAttribute("cx", "12");
    circle.setAttribute("cy", "12");
    circle.setAttribute("r", "10");
    circle.setAttribute("stroke", "currentColor");
    circle.setAttribute("stroke-width", "4");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("class", "opacity-75");
    path.setAttribute("fill", "currentColor");
    path.setAttribute("d", "M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z");
    svg.appendChild(circle);
    svg.appendChild(path);
    spinner.appendChild(svg);
    loading.appendChild(spinner);
    if (!canSend()) return;

    messages.appendChild(loading);
    scrollToBottom();

    try {
      const payload = { message };
      const selectedTenant = tenantSelect ? tenantSelect.value : "";
      if (selectedTenant) payload.tenant_id = selectedTenant;
      const body = await request("/admin/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      loading.remove();
      const reply = body.response || "";
      appendAndPersist("assistant", reply);
      if (body.sources && body.sources.length) {
        appendAndPersist("source", `Sources: ${body.sources.length} chunk(s)`);
      }
    } catch (error) {
      loading.remove();
      appendAndPersist("assistant", error.message || "Request failed");
    }
  });
}


let mediaRecorder = null;
let audioChunks = [];

function getAdminHeaders() {
  const token = sessionStorage.getItem("localrag.sessionToken");
  const secret = sessionStorage.getItem("localrag.adminSecret");
  const headers = {};
  if (token) headers["X-Session-Token"] = token;
  else if (secret) headers["X-Admin-Secret"] = secret;
  return headers;
}

async function sendVoice(blob) {
  if (!canSend()) throw new Error("Select an account first.");
  const form = new FormData();
  form.append("file", blob, "voice.webm");
  const selectedTenant = tenantSelect ? tenantSelect.value : "";
  if (selectedTenant) form.append("tenant_id", selectedTenant);
  const response = await fetch("/admin/chat/voice", {
    method: "POST",
    headers: getAdminHeaders(),
    body: form,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.error?.message || `Request failed (${response.status})`);
  return body;
}

if (mic) {
  mic.addEventListener("click", async () => {
    if (!canSend()) return;
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      const icon = document.getElementById("chat-mic-icon");
      if (icon) icon.classList.remove("animate-pulse", "text-red-500");
      return;
    }
    if (!navigator.mediaDevices || !window.MediaRecorder) {
      alert("Voice recording not supported in this browser.");
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunks.push(e.data);
    };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      const loading = document.createElement("div");
      loading.className = "flex justify-start";
      const spinner = document.createElement("div");
      spinner.className = "max-w-[80%] rounded-2xl bg-gray-100 px-3 py-2 text-gray-800 dark:bg-gray-800 dark:text-gray-100";
      spinner.textContent = "Transcribing...";
      loading.appendChild(spinner);
      if (messages) {
        messages.appendChild(loading);
        scrollToBottom();
      }
      try {
        const body = await sendVoice(blob);
        if (loading.parentNode) loading.remove();
        if (body.transcript) appendAndPersist("user", body.transcript);
        const reply = body.response || "";
        appendAndPersist("assistant", reply);
        if (body.audio) {
          const audio = new Audio(`data:audio/wav;base64,${body.audio}`);
          audio.play().catch(() => {});
        }
      } catch (error) {
        if (loading.parentNode) loading.remove();
        appendAndPersist("assistant", error.message || "Voice request failed");
      }
    };
    mediaRecorder.start();
    const icon = document.getElementById("chat-mic-icon");
    if (icon) icon.classList.add("animate-pulse", "text-red-500");
  });
}
