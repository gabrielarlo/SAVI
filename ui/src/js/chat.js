import { request } from "./documents.js";

const TOGGLE_ID = "chat-toggle";
const PANEL_ID = "chat-panel";
const FORM_ID = "chat-form";
const INPUT_ID = "chat-input";
const MESSAGES_ID = "chat-messages";

function appendMessage(container, text, className) {
  const div = document.createElement("div");
  div.className = className || "";
  div.textContent = text;
  container.appendChild(div);
}

function initChat() {
  const toggle = document.getElementById(TOGGLE_ID);
  const panel = document.getElementById(PANEL_ID);
  const form = document.getElementById(FORM_ID);
  const input = document.getElementById(INPUT_ID);
  const messages = document.getElementById(MESSAGES_ID);
  if (!toggle || !panel || !form || !input || !messages) return;

  toggle.addEventListener("click", () => panel.classList.toggle("hidden"));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    appendMessage(messages, message, "text-right");
    input.value = "";

    try {
      const body = await request("/admin/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      appendMessage(messages, body.response || "", "text-left");
      if (body.sources && body.sources.length) {
        appendMessage(
          messages,
          `Sources: ${body.sources.length} chunk(s)`,
          "text-xs text-gray-500",
        );
      }
    } catch (error) {
      appendMessage(messages, error.message, "text-red-500");
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initChat);
} else {
  initChat();
}

export { initChat };
