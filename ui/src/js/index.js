import "../css/style.css";

import Alpine from "alpinejs";

import "./documents.js";
import { signOut } from "./documents.js";
import "./tenants.js";
import "./users.js";
import "./dashboard.js";
import "./chat.js";

// TailAdmin Theme Manager: reads from localStorage, falls back to light
(function () {
  var stored = localStorage.getItem("darkMode");
  var isDark = stored !== null ? JSON.parse(stored) : false;

  if (isDark) {
    document.documentElement.classList.add("dark");
    document.documentElement.setAttribute("data-color-scheme", "dark");
  } else {
    document.documentElement.classList.remove("dark");
    document.documentElement.setAttribute("data-color-scheme", "light");
  }
})();

document.addEventListener("DOMContentLoaded", function () {
  var btn = document.getElementById("sign-out");
  if (btn) {
    btn.addEventListener("click", function (event) {
      event.preventDefault();
      signOut();
    });
  }
});

window.Alpine = Alpine;
Alpine.start();
