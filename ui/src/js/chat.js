import { request } from "./documents.js";

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

let userScrolledUp = false;

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
  bubble.textContent = msg.text;
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

if (form && input && messages) {
  loadHistory();
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
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
    messages.appendChild(loading);
    scrollToBottom();

    try {
      const body = await request("/admin/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
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
