import datetime as dt
import json
import os
import re
import socketserver
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DATA_FILE = Path("assistant_memory.json")
ENV_FILE = Path(".env")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.5-flash"
FALLBACK_GEMINI_MODELS = ("gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash")


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sabbir Personal AI</title>
  <style>
    :root {
      --bg: #0f1117;
      --surface: #131722;
      --surface-2: #1a2030;
      --surface-3: #222a3c;
      --text: #f4f7fb;
      --muted: #a8b3c7;
      --line: rgba(232, 238, 247, 0.11);
      --green: #13d38e;
      --blue: #7ca7ff;
      --pink: #ff7ab6;
      --gold: #ffd166;
    }

    * {
      box-sizing: border-box;
    }

    body {
      min-height: 100vh;
      min-height: 100dvh;
      margin: 0;
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, "Segoe UI", Arial, sans-serif;
      background:
        radial-gradient(circle at 14% 8%, rgba(124, 167, 255, 0.18), transparent 28%),
        radial-gradient(circle at 78% 12%, rgba(255, 122, 182, 0.14), transparent 26%),
        radial-gradient(circle at 54% 94%, rgba(19, 211, 142, 0.12), transparent 24%),
        linear-gradient(135deg, #0f1117 0%, #121622 48%, #0d1018 100%);
      overflow: hidden;
    }

    button, input, textarea {
      font: inherit;
    }

    .shell {
      height: 100vh;
      height: 100dvh;
      display: grid;
      grid-template-columns: 304px minmax(0, 1fr);
      gap: 14px;
      padding: 14px;
    }

    .sidebar, .chat {
      min-height: 0;
      border: 1px solid var(--line);
      background: rgba(19, 23, 34, 0.82);
      backdrop-filter: blur(22px);
      box-shadow: 0 28px 90px rgba(0, 0, 0, 0.34);
    }

    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 18px 16px;
      border-radius: 22px;
      overflow: auto;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo {
      width: 42px;
      height: 42px;
      display: grid;
      place-items: center;
      flex: 0 0 auto;
      border-radius: 15px;
      color: white;
      font-weight: 900;
      background: linear-gradient(135deg, #4285f4, #a142f4 48%, #24c6dc);
      box-shadow: 0 12px 34px rgba(66, 133, 244, 0.3);
    }

    .brand-copy {
      min-width: 0;
      flex: 1;
    }

    .brand h1 {
      margin: 0;
      font-size: 21px;
      line-height: 1.1;
      letter-spacing: 0;
    }

    .brand p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 12px;
    }

    .pulse {
      width: 10px;
      height: 10px;
      flex: 0 0 auto;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 22px var(--green);
      animation: pulse 1.6s infinite;
    }

    .api-state {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.04);
    }

    .section {
      padding-top: 14px;
      border-top: 1px solid var(--line);
    }

    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      color: #d8e2f3;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .quick {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .quick button, .mini-form button, .composer button {
      border: 0;
      border-radius: 999px;
      color: #07111f;
      background: var(--green);
      font-weight: 800;
      cursor: pointer;
      transition: transform 140ms ease, filter 140ms ease;
    }

    .quick button {
      min-height: 38px;
      padding: 0 13px;
      color: var(--text);
      background: rgba(255, 255, 255, 0.075);
      border: 1px solid var(--line);
      font-size: 13px;
    }

    button:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
    }

    button:active {
      transform: translateY(1px) scale(0.98);
    }

    .mini-form {
      display: grid;
      gap: 8px;
    }

    .mini-form input, .mini-form textarea, .composer textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      color: var(--text);
      background: rgba(7, 10, 18, 0.72);
      outline: none;
    }

    .mini-form input {
      min-height: 40px;
      padding: 0 11px;
    }

    .mini-form textarea {
      min-height: 72px;
      padding: 10px 11px;
      resize: vertical;
    }

    .mini-form button {
      min-height: 40px;
      border-radius: 14px;
    }

    .memory-list {
      display: grid;
      gap: 8px;
    }

    .memory-item {
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.045);
      color: #dce7f8;
      font-size: 13px;
      line-height: 1.4;
      word-break: break-word;
    }

    .chat {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      border-radius: 22px;
      overflow: hidden;
    }

    .chat-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.035);
    }

    .chat-header h2 {
      margin: 0;
      font-size: 20px;
      letter-spacing: 0;
    }

    .chat-header p {
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .model-pill {
      min-height: 34px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: #dfe8f7;
      background: rgba(255, 255, 255, 0.055);
      font-size: 13px;
      white-space: nowrap;
    }

    .model-pill::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 14px var(--green);
    }

    .clear {
      min-width: 96px;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--text);
      background: transparent;
      cursor: pointer;
    }

    .messages {
      min-height: 0;
      padding: 22px 20px 26px;
      overflow: auto;
      scroll-behavior: smooth;
    }

    .messages-inner {
      max-width: 980px;
      margin: 0 auto;
    }

    .message {
      width: fit-content;
      max-width: min(760px, 86%);
      margin-bottom: 18px;
      padding: 14px 16px;
      border-radius: 20px;
      line-height: 1.62;
      animation: rise 180ms ease-out;
      overflow-wrap: anywhere;
    }

    .user {
      margin-left: auto;
      color: #f8fbff;
      background: linear-gradient(135deg, rgba(66, 133, 244, 0.34), rgba(161, 66, 244, 0.22));
      border: 1px solid rgba(124, 167, 255, 0.25);
      box-shadow: 0 16px 42px rgba(66, 133, 244, 0.12);
    }

    .assistant {
      background: rgba(255, 255, 255, 0.045);
      border: 1px solid rgba(255, 255, 255, 0.09);
      box-shadow: 0 14px 44px rgba(0, 0, 0, 0.16);
    }

    .typing {
      color: var(--muted);
    }

    .typing::after {
      content: "";
      display: inline-block;
      width: 28px;
      height: 10px;
      margin-left: 8px;
      vertical-align: middle;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--blue), var(--pink), var(--green));
      animation: shimmer 1.1s infinite ease-in-out;
    }

    .assistant h1, .assistant h2, .assistant h3 {
      margin: 0 0 10px;
      line-height: 1.25;
      letter-spacing: 0;
    }

    .assistant h1 { font-size: 24px; }
    .assistant h2 { font-size: 20px; }
    .assistant h3 { font-size: 17px; }

    .assistant p {
      margin: 0 0 12px;
    }

    .assistant p:last-child {
      margin-bottom: 0;
    }

    .assistant ul, .assistant ol {
      margin: 8px 0 14px 22px;
      padding: 0;
    }

    .assistant li {
      margin: 7px 0;
      padding-left: 4px;
    }

    .assistant strong {
      color: #ffffff;
      font-weight: 800;
    }

    .assistant code {
      padding: 2px 6px;
      border-radius: 7px;
      color: #d8fff0;
      background: rgba(19, 211, 142, 0.12);
      font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
      font-size: 0.92em;
    }

    .assistant pre {
      margin: 12px 0;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: auto;
      background: rgba(5, 8, 14, 0.82);
    }

    .assistant pre code {
      padding: 0;
      background: transparent;
    }

    .assistant a {
      color: #9ec2ff;
    }

    .composer {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 96px;
      gap: 12px;
      padding: 16px;
      border-top: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.035);
    }

    .composer textarea {
      min-height: 54px;
      max-height: 150px;
      padding: 14px;
      resize: none;
      border-radius: 18px;
    }

    .composer button {
      min-height: 54px;
      font-size: 16px;
      border-radius: 18px;
      background: linear-gradient(135deg, #13d38e, #6ee7b7);
    }

    @keyframes pulse {
      0%, 100% { opacity: 0.72; transform: scale(0.96); }
      50% { opacity: 1; transform: scale(1.14); }
    }

    @keyframes rise {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes shimmer {
      0%, 100% { opacity: 0.45; transform: scaleX(0.8); }
      50% { opacity: 1; transform: scaleX(1); }
    }

    @media (max-width: 850px) {
      body {
        overflow: hidden;
      }

      .shell {
        height: 100vh;
        height: 100dvh;
        min-height: 0;
        grid-template-columns: 1fr;
        grid-template-rows: auto minmax(0, 1fr);
        gap: 10px;
        padding: 10px;
      }

      .sidebar {
        max-height: 248px;
        padding: 12px;
        border-radius: 18px;
      }

      .chat {
        min-height: 0;
        border-radius: 18px;
      }

      .header-actions {
        align-items: flex-end;
        flex-direction: column;
      }

      .brand {
        gap: 10px;
      }

      .logo {
        width: 36px;
        height: 36px;
        border-radius: 13px;
      }

      .brand h1 {
        font-size: 19px;
      }

      .api-state {
        padding: 8px 10px;
        font-size: 12px;
      }

      .section {
        padding-top: 10px;
      }

      .quick {
        flex-wrap: nowrap;
        overflow-x: auto;
        padding-bottom: 3px;
        scrollbar-width: none;
      }

      .quick::-webkit-scrollbar {
        display: none;
      }

      .quick button {
        flex: 0 0 auto;
        min-height: 36px;
      }

      .mini-form input {
        min-height: 38px;
      }

      .mini-form textarea {
        min-height: 58px;
      }

      .memory-list {
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      }

      .memory-item {
        min-height: 38px;
      }

      .chat-header {
        padding: 14px;
      }

      .messages {
        padding: 16px 14px 18px;
      }

      .message {
        max-width: 92%;
        margin-bottom: 14px;
      }

      .composer {
        padding: 12px;
      }
    }

    @media (max-width: 520px) {
      .shell {
        gap: 8px;
        padding: 8px;
      }

      .sidebar {
        max-height: 210px;
        gap: 10px;
      }

      .sidebar .section:nth-of-type(2),
      .sidebar .section:nth-of-type(3),
      .sidebar .section:nth-of-type(4) {
        display: none;
      }

      .chat-header {
        align-items: flex-start;
        flex-direction: column;
        gap: 10px;
      }

      .chat-header h2 {
        font-size: 18px;
      }

      .chat-header p {
        font-size: 12px;
      }

      .header-actions {
        width: 100%;
        align-items: center;
        flex-direction: row;
        justify-content: space-between;
      }

      .model-pill {
        max-width: calc(100vw - 124px);
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .clear {
        min-width: 76px;
      }

      .messages {
        padding: 14px 10px 16px;
      }

      .message {
        max-width: 98%;
        padding: 12px 13px;
        border-radius: 17px;
        font-size: 14px;
        line-height: 1.58;
      }

      .assistant h1 { font-size: 21px; }
      .assistant h2 { font-size: 18px; }
      .assistant h3 { font-size: 16px; }

      .assistant ul, .assistant ol {
        margin-left: 18px;
      }

      .composer {
        grid-template-columns: minmax(0, 1fr) 68px;
        gap: 8px;
        padding: 10px;
        padding-bottom: max(10px, env(safe-area-inset-bottom));
      }

      .composer textarea {
        min-height: 48px;
        max-height: 112px;
        padding: 12px;
        border-radius: 16px;
        font-size: 14px;
      }

      .composer button {
        min-height: 48px;
        border-radius: 16px;
        font-size: 14px;
      }
    }

    @media (max-width: 380px) {
      .sidebar {
        max-height: 188px;
      }

      .brand p,
      .api-state {
        display: none;
      }

      .quick button {
        min-height: 34px;
        padding: 0 11px;
        font-size: 12px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="logo">S</div>
        <div class="brand-copy">
          <h1>Sabbir AI</h1>
          <p>Personal Gemini assistant</p>
        </div>
        <span class="pulse"></span>
      </div>
      <div class="api-state" id="apiState">Checking assistant status...</div>

      <section class="section">
        <div class="section-title">Quick Actions</div>
        <div class="quick">
          <button data-prompt="Plan my day based on my saved tasks and notes.">Plan Day</button>
          <button data-prompt="Show my pending tasks.">Tasks</button>
          <button data-prompt="Summarize my saved notes.">Notes</button>
          <button data-prompt="Give me a focused 3-step productivity plan.">Focus</button>
        </div>
      </section>

      <section class="section">
        <div class="section-title">Add Task</div>
        <form class="mini-form" id="taskForm">
          <input id="taskInput" placeholder="Finish chatbot UI">
          <button type="submit">Save Task</button>
        </form>
      </section>

      <section class="section">
        <div class="section-title">Add Note</div>
        <form class="mini-form" id="noteForm">
          <textarea id="noteInput" placeholder="Remember an idea, preference, or detail."></textarea>
          <button type="submit">Save Note</button>
        </form>
      </section>

      <section class="section">
        <div class="section-title">Memory</div>
        <div class="memory-list" id="memoryList"></div>
      </section>
    </aside>

    <section class="chat">
      <header class="chat-header">
        <div>
          <h2>Personal Assistant</h2>
          <p>Ask for plans, reminders, drafts, summaries, ideas, or task help.</p>
        </div>
        <div class="header-actions">
          <span class="model-pill" id="modelPill">Checking model</span>
          <button class="clear" id="clearChat">Clear</button>
        </div>
      </header>

      <div class="messages" id="messages">
        <div class="messages-inner" id="messagesInner"></div>
      </div>

      <form class="composer" id="chatForm">
        <textarea id="messageInput" placeholder="Ask Sabbir AI anything..."></textarea>
        <button type="submit">Send</button>
      </form>
    </section>
  </main>

  <script>
    const messages = document.querySelector("#messages");
    const messagesInner = document.querySelector("#messagesInner");
    const form = document.querySelector("#chatForm");
    const input = document.querySelector("#messageInput");
    const memoryList = document.querySelector("#memoryList");
    const apiState = document.querySelector("#apiState");
    const modelPill = document.querySelector("#modelPill");
    const taskForm = document.querySelector("#taskForm");
    const noteForm = document.querySelector("#noteForm");
    const taskInput = document.querySelector("#taskInput");
    const noteInput = document.querySelector("#noteInput");
    const clearChat = document.querySelector("#clearChat");

    let chat = [];
    const userId = localStorage.getItem("sabbir_ai_user_id") || crypto.randomUUID();
    localStorage.setItem("sabbir_ai_user_id", userId);

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function formatInline(value) {
      let safe = escapeHtml(value);
      safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
      safe = safe.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
      safe = safe.replace(/\*([^*]+)\*/g, "<em>$1</em>");
      safe = safe.replace(
        /(https?:\/\/[^\s<]+)/g,
        '<a href="$1" target="_blank" rel="noreferrer">$1</a>'
      );
      return safe;
    }

    function closeList(parts, state) {
      if (state.listType) {
        parts.push(`</${state.listType}>`);
        state.listType = "";
      }
    }

    function renderMarkdown(text) {
      const lines = String(text).replace(/\r\n/g, "\n").split("\n");
      const parts = [];
      const state = {listType: "", inCode: false, codeLines: []};

      for (const line of lines) {
        if (line.trim().startsWith("```")) {
          closeList(parts, state);
          if (state.inCode) {
            parts.push(`<pre><code>${escapeHtml(state.codeLines.join("\n"))}</code></pre>`);
            state.codeLines = [];
            state.inCode = false;
          } else {
            state.inCode = true;
          }
          continue;
        }

        if (state.inCode) {
          state.codeLines.push(line);
          continue;
        }

        if (!line.trim()) {
          closeList(parts, state);
          continue;
        }

        const heading = line.match(/^(#{1,3})\s+(.+)$/);
        if (heading) {
          closeList(parts, state);
          const level = heading[1].length;
          parts.push(`<h${level}>${formatInline(heading[2])}</h${level}>`);
          continue;
        }

        const bullet = line.match(/^\s*[-*]\s+(.+)$/);
        if (bullet) {
          if (state.listType !== "ul") {
            closeList(parts, state);
            parts.push("<ul>");
            state.listType = "ul";
          }
          parts.push(`<li>${formatInline(bullet[1])}</li>`);
          continue;
        }

        const numbered = line.match(/^\s*\d+\.\s+(.+)$/);
        if (numbered) {
          if (state.listType !== "ol") {
            closeList(parts, state);
            parts.push("<ol>");
            state.listType = "ol";
          }
          parts.push(`<li>${formatInline(numbered[1])}</li>`);
          continue;
        }

        closeList(parts, state);
        parts.push(`<p>${formatInline(line)}</p>`);
      }

      if (state.inCode) {
        parts.push(`<pre><code>${escapeHtml(state.codeLines.join("\n"))}</code></pre>`);
      }
      closeList(parts, state);
      return parts.join("");
    }

    function addMessage(role, text, extraClass = "") {
      const bubble = document.createElement("div");
      bubble.className = `message ${role} ${extraClass}`.trim();
      if (role === "assistant" && !extraClass.includes("typing")) {
        bubble.innerHTML = renderMarkdown(text);
      } else {
        bubble.textContent = text;
      }
      messagesInner.appendChild(bubble);
      messages.scrollTop = messages.scrollHeight;
      return bubble;
    }

    function renderMemory(memory) {
      apiState.textContent = memory.api_enabled
        ? `AI mode: Gemini ${memory.model}`
        : "Offline mode: set GEMINI_API_KEY for full AI replies.";
      modelPill.textContent = memory.api_enabled ? memory.model : "Offline";

      const items = [];
      if (memory.profile) {
        Object.entries(memory.profile).forEach(([key, value]) => {
          if (value) items.push(`${key}: ${value}`);
        });
      }
      memory.tasks.slice(-4).forEach((task) => items.push(`Task: ${task.text}`));
      memory.notes.slice(-4).forEach((note) => items.push(`Note: ${note.text}`));
      memory.facts.slice(-4).forEach((fact) => items.push(`Memory: ${fact}`));

      memoryList.innerHTML = "";
      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "memory-item";
        empty.textContent = "No saved memory yet.";
        memoryList.appendChild(empty);
        return;
      }

      items.reverse().forEach((text) => {
        const item = document.createElement("div");
        item.className = "memory-item";
        item.textContent = text;
        memoryList.appendChild(item);
      });
    }

    async function api(path, payload = null) {
      const url = payload ? path : `${path}?user_id=${encodeURIComponent(userId)}`;
      const options = payload
        ? {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({...payload, user_id: userId}),
          }
        : {};

      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      return response.json();
    }

    async function refreshMemory() {
      const data = await api("/api/memory");
      renderMemory(data);
    }

    async function sendMessage(text) {
      const clean = text.trim();
      if (!clean) return;

      input.value = "";
      addMessage("user", clean);
      const typing = addMessage("assistant", "Thinking...", "typing");

      try {
        const data = await api("/api/chat", {message: clean, chat});
        typing.remove();
        addMessage("assistant", data.reply);
        chat.push({role: "user", content: clean});
        chat.push({role: "assistant", content: data.reply});
        chat = chat.slice(-16);
        renderMemory(data.memory);
      } catch (error) {
        typing.remove();
        addMessage("assistant", `I hit an error: ${error.message}`);
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      sendMessage(input.value);
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    document.querySelectorAll("[data-prompt]").forEach((button) => {
      button.addEventListener("click", () => sendMessage(button.dataset.prompt));
    });

    taskForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = taskInput.value.trim();
      if (!text) return;
      await api("/api/memory", {type: "task", text});
      taskInput.value = "";
      refreshMemory();
    });

    noteForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = noteInput.value.trim();
      if (!text) return;
      await api("/api/memory", {type: "note", text});
      noteInput.value = "";
      refreshMemory();
    });

    clearChat.addEventListener("click", () => {
      chat = [];
      messagesInner.innerHTML = "";
      addMessage("assistant", "Chat cleared. I still remember saved notes and tasks.");
    });

    addMessage("assistant", "Hi. I am ready to help like a personal assistant. Tell me how you want me to talk with you: friendly, professional, big-brother style, sisterly style, Bangla, English, or mixed. If you want, also tell me your pronouns or gender preference so I do not guess.");
    refreshMemory().catch(() => {
      apiState.textContent = "Assistant is starting...";
    });
  </script>
</body>
</html>
"""


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def load_env_file():
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_host():
    return os.environ.get("HOST", DEFAULT_HOST)


def get_port():
    try:
        return int(os.environ.get("PORT", DEFAULT_PORT))
    except ValueError:
        return DEFAULT_PORT


def should_open_browser(host):
    if os.environ.get("NO_BROWSER"):
        return False
    hosted_flags = ("RENDER", "RAILWAY_ENVIRONMENT", "FLY_APP_NAME")
    if any(os.environ.get(flag) for flag in hosted_flags):
        return False
    return host in {"127.0.0.1", "localhost"}


def blank_memory():
    return {"facts": [], "tasks": [], "notes": [], "profile": {}}


def clean_user_id(user_id):
    value = str(user_id or "default")
    value = re.sub(r"[^a-zA-Z0-9_-]", "", value)
    return value[:80] or "default"


def load_store():
    if not DATA_FILE.exists():
        return {"users": {}}
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"users": {}}

    if "users" not in data:
        old_memory = blank_memory()
        old_memory["facts"] = data.get("facts", [])
        old_memory["tasks"] = data.get("tasks", [])
        old_memory["notes"] = data.get("notes", [])
        return {"users": {"default": old_memory}}

    data.setdefault("users", {})
    return data


def save_store(store):
    DATA_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def load_memory(user_id="default"):
    store = load_store()
    uid = clean_user_id(user_id)
    memory = store["users"].get(uid, blank_memory())
    memory.setdefault("facts", [])
    memory.setdefault("tasks", [])
    memory.setdefault("notes", [])
    memory.setdefault("profile", {})
    return memory


def save_memory(user_id, memory):
    store = load_store()
    uid = clean_user_id(user_id)
    store["users"][uid] = memory
    save_store(store)


def public_memory(memory):
    data = dict(memory)
    data["api_enabled"] = bool(get_gemini_key())
    data["model"] = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    return data


def add_memory(kind, text, user_id="default"):
    memory = load_memory(user_id)
    text = text.strip()
    if not text:
        return memory

    item = {"text": text, "created_at": now_iso()}
    if kind == "task":
        memory["tasks"].append(item)
    elif kind == "note":
        memory["notes"].append(item)
    elif kind == "fact":
        memory["facts"].append(text)

    memory["tasks"] = memory["tasks"][-50:]
    memory["notes"] = memory["notes"][-50:]
    memory["facts"] = memory["facts"][-50:]
    save_memory(user_id, memory)
    return memory


def memory_summary(memory):
    tasks = [f"- {task['text']}" for task in memory["tasks"][-10:]]
    notes = [f"- {note['text']}" for note in memory["notes"][-10:]]
    facts = [f"- {fact}" for fact in memory["facts"][-10:]]
    profile = memory.get("profile", {})
    profile_lines = [f"- {key}: {value}" for key, value in profile.items() if value]
    return "\n".join(
        [
            "User profile and communication preferences:",
            "\n".join(profile_lines) or "- unknown; ask briefly if useful, never guess gender",
            "Saved facts:",
            "\n".join(facts) or "- none",
            "Saved tasks:",
            "\n".join(tasks) or "- none",
            "Saved notes:",
            "\n".join(notes) or "- none",
        ]
    )


def update_profile_from_message(message, memory):
    lowered = message.lower()
    profile = memory.setdefault("profile", {})
    changed = False

    patterns = [
        ("gender", r"\b(i am|i'm|ami)\s+(a\s+)?(male|man|boy|chele|female|woman|girl|meye)\b"),
        ("pronouns", r"\b(my pronouns are|pronouns:?)\s+([a-z/ ]{2,30})"),
        ("tone", r"\b(talk|speak|reply|answer)\s+(to me\s+)?(like|in|with)\s+(.{3,80})"),
        ("language", r"\b(bangla|bengali|english|mixed|banglish)\b"),
    ]

    for key, pattern in patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if not match:
            continue
        value = match.group(match.lastindex).strip()
        if key == "gender":
            gender_word = value
            if gender_word in {"chele", "male", "man", "boy"}:
                value = "male"
            elif gender_word in {"meye", "female", "woman", "girl"}:
                value = "female"
        if profile.get(key) != value:
            profile[key] = value
            changed = True

    if any(word in lowered for word in ["bhai", "bro", "brother"]):
        profile["tone"] = "friendly brother style"
        changed = True
    if any(word in lowered for word in ["apu", "sis", "sister"]):
        profile["tone"] = "friendly sister style"
        changed = True
    if "bangla" in lowered or "bengali" in lowered or "বাংলা" in message:
        profile["language"] = "Bangla"
        changed = True
    if "english" in lowered:
        profile["language"] = "English"
        changed = True
    if "banglish" in lowered or "mixed" in lowered:
        profile["language"] = "Bangla-English mixed"
        changed = True

    return changed


def profile_ack(memory):
    profile = memory.get("profile", {})
    pieces = []
    if profile.get("gender"):
        pieces.append(f"gender preference: {profile['gender']}")
    if profile.get("pronouns"):
        pieces.append(f"pronouns: {profile['pronouns']}")
    if profile.get("tone"):
        pieces.append(f"style: {profile['tone']}")
    if profile.get("language"):
        pieces.append(f"language: {profile['language']}")
    detail = ", ".join(pieces) if pieces else "your preference"
    return f"Got it. I saved {detail}. I will use that while talking with you."


def extract_output_text(payload):
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()

    parts = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts).strip()


def extract_gemini_text(payload):
    parts = []
    for candidate in payload.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts).strip()


def get_gemini_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def gemini_model_choices():
    configured = os.environ.get("GEMINI_MODEL", "").strip()
    choices = []
    if configured:
        choices.append(configured)
    for model in FALLBACK_GEMINI_MODELS:
        if model not in choices:
            choices.append(model)
    return choices


def friendly_api_error(details):
    try:
        payload = json.loads(details)
    except json.JSONDecodeError:
        return None

    error = payload.get("error", {})
    code = error.get("status") or error.get("code") or error.get("type")
    message = error.get("message")
    if code in {"insufficient_quota", "RESOURCE_EXHAUSTED"}:
        return (
            "Your API account has no remaining credits or quota. "
            "Add billing or credits, then try again."
        )
    if code in {"invalid_api_key", "PERMISSION_DENIED", "UNAUTHENTICATED"}:
        return "That API key is invalid. Double-check the value in your .env file."
    if isinstance(message, str) and "API key" in message:
        return "That API key is invalid. Double-check the value in your .env file."
    if isinstance(message, str) and message.strip():
        return f"API error: {message.strip()}"
    return None


def ask_openai(message, chat, memory):
    api_key = get_gemini_key()
    if not api_key:
        return None

    recent = "\n".join(
        f"{item.get('role', 'user')}: {item.get('content', '')}" for item in chat[-10:]
    )
    instructions = (
        "You are a realistic, emotionally intelligent personal AI assistant. "
        "Your replies should feel human, grounded, and useful, not robotic. "
        "First understand the user's mood and intent, then answer with empathy and practical help. "
        "Use saved memory and the user's profile when relevant. Match the user's language and tone "
        "naturally: Bangla, English, or mixed if they use it. Do not guess gender from name, voice, "
        "or writing style. If gender, pronouns, or preferred style is unknown and relevant, ask once "
        "in a short, friendly way. If the user explicitly shares male/female/pronouns/style, respect it "
        "without stereotypes. Be honest about uncertainty, give realistic steps, and avoid fake promises. "
        "For emotional messages, validate the feeling first, then offer calm next steps. For plans, be clear "
        "and concrete. Keep normal answers concise, but go deeper when the user asks."
    )
    prompt = (
        f"{memory_summary(memory)}\n\n"
        f"Recent chat:\n{recent or 'none'}\n\n"
        f"Sabbir says: {message}"
    )
    body = json.dumps(
        {
            "systemInstruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        }
    ).encode("utf-8")

    last_error = ""
    for model in gemini_model_choices():
        request = urllib.request.Request(
            GEMINI_URL.format(model=model),
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return extract_gemini_text(payload) or "I received an empty AI response."
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            last_error = details
            if error.code == 404 and "not found for API version" in details:
                continue
            friendly = friendly_api_error(details)
            if friendly:
                return friendly
            return f"API error: {details}"
        except urllib.error.URLError as error:
            return f"I could not reach the AI service: {error.reason}"

    return (
        "Gemini could not find a supported text model for your API key. "
        "Open Google AI Studio and check which models your key can use, then set "
        "GEMINI_MODEL in .env. Last API error: "
        f"{last_error}"
    )


def offline_reply(message, memory, user_id="default"):
    lowered = message.lower().strip()

    if update_profile_from_message(message, memory):
        save_memory(user_id, memory)
        return profile_ack(memory)

    remember_match = re.search(r"remember(?: that)? (.+)", message, re.IGNORECASE)
    if remember_match:
        fact = remember_match.group(1).strip()
        add_memory("fact", fact, user_id)
        return f"Saved to memory: {fact}"

    task_match = re.search(r"(?:add|save) task(?:\:| to)? (.+)", message, re.IGNORECASE)
    if task_match:
        task = task_match.group(1).strip()
        add_memory("task", task, user_id)
        return f"Task saved: {task}"

    note_match = re.search(r"(?:add|save) note(?:\:| to)? (.+)", message, re.IGNORECASE)
    if note_match:
        note = note_match.group(1).strip()
        add_memory("note", note, user_id)
        return f"Note saved: {note}"

    if "task" in lowered:
        if not memory["tasks"]:
            return "You do not have saved tasks yet. Add one from the sidebar or say: add task finish my project."
        lines = [f"{index}. {task['text']}" for index, task in enumerate(memory["tasks"], start=1)]
        return "Your saved tasks:\n" + "\n".join(lines)

    if "note" in lowered:
        if not memory["notes"]:
            return "You do not have saved notes yet."
        lines = [f"{index}. {note['text']}" for index, note in enumerate(memory["notes"], start=1)]
        return "Your saved notes:\n" + "\n".join(lines)

    if "plan" in lowered or "day" in lowered or "focus" in lowered:
        task_text = memory["tasks"][-3:]
        steps = [
            "1. Pick the single most important task and work on it for 45 minutes.",
            "2. Handle one small admin task so it stops taking mental space.",
            "3. Review your notes, then write the next concrete action.",
        ]
        if task_text:
            steps.insert(1, f"Top saved task: {task_text[-1]['text']}")
        return "\n".join(steps)

    if "hello" in lowered or "hi" in lowered:
        return (
            "Hi. I can help with planning, tasks, notes, writing, decisions, and emotional support. "
            "Tell me your preferred style if you want: friendly, professional, brother-style, sister-style, "
            "Bangla, English, or mixed."
        )

    return (
        "I am running in offline assistant mode right now. I can save notes, save tasks, "
        "show your memory, and make simple plans. For full AI answers, set GEMINI_API_KEY "
        "before running this script."
    )


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class AssistantHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/memory":
            user_id = self.query_value("user_id")
            self.send_json(public_memory(load_memory(user_id)))
            return
        if path == "/healthz":
            self.send_text("ok")
            return
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        self.send_html(HTML)

    def do_POST(self):
        if self.path == "/api/chat":
            payload = self.read_json()
            user_id = clean_user_id(payload.get("user_id"))
            message = str(payload.get("message", "")).strip()
            chat = payload.get("chat", [])
            memory = load_memory(user_id)
            profile_changed = update_profile_from_message(message, memory)
            if profile_changed:
                save_memory(user_id, memory)
            reply = ask_openai(message, chat, memory)
            if not reply:
                reply = profile_ack(memory) if profile_changed else offline_reply(message, memory, user_id)
            self.send_json({"reply": reply, "memory": public_memory(load_memory(user_id))})
            return

        if self.path == "/api/memory":
            payload = self.read_json()
            user_id = clean_user_id(payload.get("user_id"))
            kind = str(payload.get("type", "note"))
            text = str(payload.get("text", ""))
            memory = add_memory(kind, text, user_id)
            self.send_json(public_memory(memory))
            return

        self.send_error(404)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def query_value(self, name):
        if "?" not in self.path:
            return ""
        query = self.path.split("?", 1)[1]
        for pair in query.split("&"):
            key, _, value = pair.partition("=")
            if key == name:
                return urllib.parse.unquote_plus(value)
        return ""

    def send_html(self, html):
        encoded = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def send_json(self, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def send_text(self, text):
        encoded = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


def make_server():
    host = get_host()
    port = get_port()
    try:
        return ThreadingTCPServer((host, port), AssistantHandler)
    except OSError:
        return ThreadingTCPServer((host, 0), AssistantHandler)


def main():
    load_env_file()
    with make_server() as server:
        host = get_host()
        actual_port = server.server_address[1]
        shown_host = "127.0.0.1" if host == "0.0.0.0" else host
        url = f"http://{shown_host}:{actual_port}"
        print(f"Sabbir Personal AI is running at {url}")
        print("Set GEMINI_API_KEY before running for full AI answers.")
        print("Press Ctrl+C to stop.")
        if should_open_browser(host):
            webbrowser.open(url)
        server.serve_forever()


if __name__ == "__main__":
    main()
