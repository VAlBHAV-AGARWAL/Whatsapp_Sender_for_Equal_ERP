const state = {
  queue: [],
};

const csvFileInput = document.getElementById("csvFile");
const templateInput = document.getElementById("messageTemplate");
const countryCodeInput = document.getElementById("countryCode");
const minDelayInput = document.getElementById("minDelay");
const maxDelayInput = document.getElementById("maxDelay");
const queueCount = document.getElementById("queueCount");
const previewList = document.getElementById("previewList");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");

init();

function init() {
  csvFileInput.addEventListener("change", handleCsvUpload);
  templateInput.addEventListener("input", renderPreview);
  startButton.addEventListener("click", startQueue);
  stopButton.addEventListener("click", stopQueue);
  restoreDraft();
  refreshStatus();
  window.setInterval(refreshStatus, 1500);
}

async function restoreDraft() {
  const saved = await chrome.storage.local.get([
    "draftTemplate",
    "draftCountryCode",
    "draftMinDelay",
    "draftMaxDelay",
  ]);

  if (saved.draftTemplate) templateInput.value = saved.draftTemplate;
  if (saved.draftCountryCode) countryCodeInput.value = saved.draftCountryCode;
  if (saved.draftMinDelay) minDelayInput.value = saved.draftMinDelay;
  if (saved.draftMaxDelay) maxDelayInput.value = saved.draftMaxDelay;
}

async function handleCsvUpload(event) {
  const [file] = event.target.files || [];
  if (!file) return;

  const text = await file.text();
  const rows = parseCsv(text);
  const defaultCountryCode = countryCodeInput.value.trim() || "+91";

  state.queue = rows
    .filter((row) => row.phone)
    .map((row) => {
      const normalized = normalizePhone(row.phone, defaultCountryCode);
      return {
        row,
        phone: normalized,
        message: applyTemplate(templateInput.value, row),
      };
    });

  await saveDraft();
  renderPreview();
}

async function saveDraft() {
  await chrome.storage.local.set({
    draftTemplate: templateInput.value,
    draftCountryCode: countryCodeInput.value,
    draftMinDelay: minDelayInput.value,
    draftMaxDelay: maxDelayInput.value,
  });
}

function parseCsv(text) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) return [];

  const headers = splitCsvLine(lines[0]).map((value) => value.trim().toLowerCase());
  return lines.slice(1).map((line) => {
    const cells = splitCsvLine(line);
    const row = {};
    headers.forEach((header, index) => {
      row[header] = (cells[index] || "").trim();
    });
    return row;
  });
}

function splitCsvLine(line) {
  const cells = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (char === "," && !inQuotes) {
      cells.push(current);
      current = "";
      continue;
    }
    current += char;
  }

  cells.push(current);
  return cells;
}

function normalizePhone(phone, defaultCountryCode) {
  const digits = String(phone).replace(/[^\d+]/g, "");
  if (digits.startsWith("+")) return digits;
  return `${defaultCountryCode}${digits}`;
}

function applyTemplate(template, row) {
  return template.replace(/\{([^}]+)\}/g, (_, key) => row[key.toLowerCase()] || row[key] || "");
}

function renderPreview() {
  queueCount.textContent = `${state.queue.length} recipient${state.queue.length === 1 ? "" : "s"}`;

  if (!state.queue.length) {
    previewList.textContent = "Load a CSV to preview recipients here.";
    return;
  }

  previewList.innerHTML = state.queue
    .slice(0, 8)
    .map((item) => `
      <div class="preview-item">
        <strong>${escapeHtml(item.row.name || item.phone)}</strong>
        <div>${escapeHtml(item.phone)}</div>
        <div>${escapeHtml(item.message.slice(0, 90))}${item.message.length > 90 ? "..." : ""}</div>
      </div>
    `)
    .join("");
}

async function startQueue() {
  await saveDraft();

  if (!state.queue.length) {
    setPopupStatus("error", "Load a CSV with at least one phone number before starting.");
    return;
  }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id || !tab.url || !tab.url.startsWith("https://web.whatsapp.com/")) {
    setPopupStatus("error", "Open the logged-in WhatsApp Web tab first, then start the queue from there.");
    return;
  }

  const settings = {
    minDelayMs: Number(minDelayInput.value || 18) * 1000,
    maxDelayMs: Number(maxDelayInput.value || 35) * 1000,
  };

  const payload = {
    queue: state.queue,
    settings,
  };

  try {
    await chrome.tabs.sendMessage(tab.id, { type: "WA_QUEUE_START", payload });
    setPopupStatus("ok", `Queue sent to WhatsApp tab: ${state.queue.length} recipients ready.`);
  } catch (error) {
    setPopupStatus("error", `Could not reach the WhatsApp tab. Refresh the tab once and try again. ${error.message || ""}`.trim());
  }
}

async function stopQueue() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id || !tab.url || !tab.url.startsWith("https://web.whatsapp.com/")) {
    setPopupStatus("error", "Open the WhatsApp Web tab before sending a stop signal.");
    return;
  }

  try {
    await chrome.tabs.sendMessage(tab.id, { type: "WA_QUEUE_STOP" });
    setPopupStatus("ok", "Stop signal sent to the WhatsApp tab.");
  } catch (error) {
    setPopupStatus("error", `Could not send stop signal. ${error.message || ""}`.trim());
  }
}

async function refreshStatus() {
  const { waQueueState } = await chrome.storage.local.get("waQueueState");
  if (!waQueueState) return;

  statusBadge.textContent = waQueueState.phase || "idle";
  statusText.textContent = waQueueState.message || "Waiting for queue activity.";
  statusBadge.className = waQueueState.error ? "status-error" : "status-ok";
}

function setPopupStatus(kind, message) {
  statusBadge.textContent = kind;
  statusText.textContent = message;
  statusBadge.className = kind === "error" ? "status-error" : "status-ok";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
