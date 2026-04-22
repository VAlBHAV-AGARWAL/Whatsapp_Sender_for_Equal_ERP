const state = {
  rows: [],
  fileName: "",
  loading: false,
  searchTerm: "",
  filterFailed: false,
  templates: ["", "", ""], // Store 3 templates
  activeTemplateIdx: 0,
  stats: { sent: 0, skipped: 0 }
};

const fileInput = document.getElementById("csvFile");
const templateInput = document.getElementById("messageTemplate");
const templatePicker = document.getElementById("templatePicker");
const countryCodeInput = document.getElementById("countryCode");
const minDelayInput = document.getElementById("minDelay");
const maxDelayInput = document.getElementById("maxDelay");
const minDaysInput = document.getElementById("minDays");
const spamGuardInput = document.getElementById("spamGuard");
const previewList = document.getElementById("previewList");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const searchInput = document.getElementById("searchInput");

// Stats
const statTotalEl = document.getElementById("statTotal");
const statReadyEl = document.getElementById("statReady");
const statProcessedEl = document.getElementById("statProcessed");

// Bulk/Filter
const selectAllBtn = document.getElementById("selectAllBtn");
const selectNoneBtn = document.getElementById("selectNoneBtn");
const failedOnlyBtn = document.getElementById("failedOnlyBtn");

// Modal
const addPartyBtn = document.getElementById("addPartyBtn");
const addModal = document.getElementById("addModal");
const cancelAddBtn = document.getElementById("cancelAddBtn");
const confirmAddBtn = document.getElementById("confirmAddBtn");
const newPartyName = document.getElementById("newPartyName");
const newPartyPhone = document.getElementById("newPartyPhone");
const newPartyBalance = document.getElementById("newPartyBalance");

init();

function init() {
  fileInput.addEventListener("change", handleFileUpload);
  templateInput.addEventListener("input", handleTemplateChange);
  templatePicker.addEventListener("change", handleTemplateSwitch);
  
  countryCodeInput.addEventListener("input", handleCountryCodeChange);
  minDaysInput.addEventListener("input", () => { refreshListing(); saveDraft(); });
  minDelayInput.addEventListener("input", saveDraft);
  maxDelayInput.addEventListener("input", saveDraft);
  spamGuardInput.addEventListener("change", saveDraft);
  
  searchInput.addEventListener("input", (e) => {
    state.searchTerm = e.target.value.toLowerCase();
    renderPreview();
  });

  selectAllBtn.addEventListener("click", () => bulkToggle(true));
  selectNoneBtn.addEventListener("click", () => bulkToggle(false));
  failedOnlyBtn.addEventListener("click", toggleFailedFilter);

  previewList.addEventListener("click", handlePreviewClick);
  previewList.addEventListener("input", handlePreviewInput);
  
  startButton.addEventListener("click", startCampaign);
  stopButton.addEventListener("click", stopQueue);

  addPartyBtn.addEventListener("click", () => addModal.classList.add("active"));
  cancelAddBtn.addEventListener("click", () => addModal.classList.remove("active"));
  confirmAddBtn.addEventListener("click", handleManualAdd);

  document.querySelectorAll(".tag-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const tag = chip.textContent;
      const start = templateInput.selectionStart;
      const end = templateInput.selectionEnd;
      templateInput.value = templateInput.value.slice(0, start) + tag + templateInput.value.slice(end);
      handleTemplateChange();
    });
  });

  restoreDraft().then(() => renderPreview());
  
  refreshStatus();
  window.setInterval(refreshStatus, 1500);
}

async function restoreDraft() {
  if (typeof chrome === "undefined" || !chrome.storage) return;
  const saved = await chrome.storage.local.get([
    "draftTemplates", "draftActiveTemplateIdx", "draftCountryCode", 
    "draftMinDelay", "draftMaxDelay", "draftMinDays", "draftSpamGuard",
    "draftRows", "draftFileName", "draftStats"
  ]);

  if (saved.draftTemplates) state.templates = saved.draftTemplates;
  if (saved.draftActiveTemplateIdx !== undefined) state.activeTemplateIdx = saved.draftActiveTemplateIdx;
  
  templatePicker.value = state.activeTemplateIdx + 1;
  templateInput.value = state.templates[state.activeTemplateIdx] || "";
  
  if (saved.draftCountryCode) countryCodeInput.value = saved.draftCountryCode;
  if (saved.draftMinDelay) minDelayInput.value = saved.draftMinDelay;
  if (saved.draftMaxDelay) maxDelayInput.value = saved.draftMaxDelay;
  if (saved.draftMinDays) minDaysInput.value = saved.draftMinDays;
  if (saved.draftSpamGuard !== undefined) spamGuardInput.checked = saved.draftSpamGuard;
  
  if (Array.isArray(saved.draftRows)) state.rows = saved.draftRows;
  if (saved.draftFileName) state.fileName = saved.draftFileName;
  if (saved.draftStats) state.stats = saved.draftStats;
}

async function saveDraft() {
  if (typeof chrome === "undefined" || !chrome.storage) return;
  state.templates[state.activeTemplateIdx] = templateInput.value;
  await chrome.storage.local.set({
    draftTemplates: state.templates,
    draftActiveTemplateIdx: state.activeTemplateIdx,
    draftCountryCode: countryCodeInput.value,
    draftMinDelay: minDelayInput.value,
    draftMaxDelay: maxDelayInput.value,
    draftMinDays: minDaysInput.value,
    draftSpamGuard: spamGuardInput.checked,
    draftRows: state.rows,
    draftFileName: state.fileName,
    draftStats: state.stats
  });
}

function handleTemplateSwitch() {
  state.templates[state.activeTemplateIdx] = templateInput.value; // save old
  state.activeTemplateIdx = templatePicker.value - 1;
  templateInput.value = state.templates[state.activeTemplateIdx] || "";
  handleTemplateChange();
}

function bulkToggle(val) {
  state.rows.forEach(r => r.enabled = val);
  renderPreview();
  saveDraft();
}

function toggleFailedFilter() {
  state.filterFailed = !state.filterFailed;
  failedOnlyBtn.textContent = state.filterFailed ? "show all" : "show failed";
  renderPreview();
}

function handleManualAdd() {
  const name = newPartyName.value.trim();
  const phoneRaw = newPartyPhone.value.trim();
  const balance = newPartyBalance.value.trim();
  if (!name || !phoneRaw) return alert("name and phone required");

  const normPhone = normalizePhone(phoneRaw, countryCodeInput.value || "+91");
  const entry = {
    name, phone: normPhone, phone_raw: phoneRaw, all_phones: normPhone ? [normPhone] : [],
    balance, billno: "manual", bills: "manual", days: "0",
    _id: Date.now(), enabled: !!normPhone, customMessage: false, status: null
  };
  entry.message = applyTemplate(templateInput.value, entry);
  state.rows.unshift(entry);
  addModal.classList.remove("active");
  renderPreview();
  saveDraft();
}

async function handleFileUpload(event) {
  const [file] = event.target.files || [];
  if (!file) return;
  setPopupStatus("info", "loading...");
  try {
    const tableRows = await readTabularFile(file);
    state.fileName = file.name;
    state.rows = normalizeRows(tableRows, countryCodeInput.value || "+91", templateInput.value);
    state.stats = { sent: 0, skipped: 0 };
    await saveDraft();
    renderPreview();
    setPopupStatus("ok", `loaded ${state.rows.length} parties`);
  } catch (e) {
    setPopupStatus("error", e.message || "failed");
  }
}

function normalizeRows(tableRows, country, template) {
  const requiredHeaders = ["date", "billno", "agent", "days", "netamt", "balamt", "haste", "phone", "mobile"];
  let headers = [];
  let headerIdx = -1;
  for (let i = 0; i < Math.min(tableRows.length, 30); i++) {
    const r = tableRows[i].map(v => normalizeHeader(v));
    if (requiredHeaders.filter(h => r.includes(h)).length >= 5) { headers = r; headerIdx = i; break; }
  }
  if (headerIdx === -1) { headers = (tableRows[0] || []).map(v => normalizeHeader(v)); headerIdx = 0; }

  const parties = new Map();
  tableRows.slice(headerIdx + 1).forEach(vals => {
    const first = String(vals[0] || "").trim();
    if (first.toLowerCase().startsWith("party :")) {
      const m = first.match(/Party\s*:\s*([^:.(]+)/i);
      if (m) this._curParty = m[1].trim();
      return;
    }
    const raw = {}; headers.forEach((h, idx) => raw[h] = String(vals[idx] || "").trim());
    const billNo = pickFirst(raw, ["billno", "bill_no"]) || "";
    if (!billNo || billNo.toLowerCase() === "total") return;
    
    if (!parties.has(this._curParty)) parties.set(this._curParty, { name: this._curParty, bills: [], numbers: new Set(), raw: new Set(), maxDays: 0, total: 0 });
    const p = parties.get(this._curParty);
    const balance = Number(pickFirst(raw, ["balamt", "balance"]).replace(/[^\d.-]/g, "")) || 0;
    const days = Number(pickFirst(raw, ["days", "aging"])) || 0;
    p.bills.push({ billno: billNo, balance, days });
    p.maxDays = Math.max(p.maxDays, days);
    p.total += balance;
    [raw.mobile, raw.phone].forEach(r => { const n = normalizePhone(r, country); if (n) { p.numbers.add(n); p.raw.add(String(r).trim()); }});
  });

  const minDays = Number(minDaysInput.value || 0);
  return Array.from(parties.values()).filter(p => p.maxDays >= minDays).map((p, idx) => {
    const nums = Array.from(p.numbers);
    const entry = {
      name: p.name, billno: p.bills.map(b => b.billno).join(", "),
      bills: p.bills.map(b => `${b.billno} (rs.${b.balance})`).join(", "),
      days: p.maxDays, balance: p.total, phone: nums[0] || "",
      phone_raw: Array.from(p.raw).join("/") || "none",
      all_phones: nums, _id: Date.now() + idx, enabled: nums.length > 0,
      customMessage: false, status: null
    };
    entry.message = applyTemplate(template, entry);
    return entry;
  });
}

function normalizeHeader(v) { return String(v || "").trim().toLowerCase().replace(/[\s\-\/]+/g, "_").replace(/[^\w_]/g, ""); }
function pickFirst(raw, names) { for (const n of names) { const nm = normalizeHeader(n); if (raw[nm]) return raw[nm]; } return ""; }

function normalizePhone(p, code) {
  const t = String(p || "").trim();
  if (!t || t.toLowerCase() === "none" || t.length < 5) return "";
  let d = t.replace(/\D/g, "");
  if (d.length > 10) d = d.slice(-10);
  if (d.length !== 10) return "";
  const prefix = String(code || "+91").startsWith("+") ? code : `+${code}`;
  return `${prefix}${d}`;
}

function applyTemplate(tpl, row) {
  return String(tpl || "").replace(/\{([^}]+)\}/g, (_, token) => {
    const k = normalizeHeader(token);
    return String(row[k] ?? row[token] ?? "");
  });
}

function renderPreview() {
  let filtered = state.rows.filter(r => !state.searchTerm || r.name.toLowerCase().includes(state.searchTerm));
  if (state.filterFailed) filtered = filtered.filter(r => r.status === "skip" || r.status === "failed");

  statTotalEl.textContent = state.rows.length;
  statReadyEl.textContent = state.rows.filter(r => r.enabled && r.phone).length;
  statProcessedEl.textContent = `${state.stats.sent} / ${state.stats.skipped}`;

  previewList.innerHTML = filtered.map(row => `
    <div class="preview-card ${row.enabled ? "" : "is-disabled"} ${row.status || ""}" data-id="${row._id}">
      <div class="card-header">
        <input type="text" data-field="name" value="${escapeHtml(row.name)}">
        <div style="display:flex; align-items:center;">
          ${row.status ? `<span class="status-label status-${row.status}">${row.status}</span>` : ""}
          <input type="checkbox" ${row.enabled ? "checked" : ""} data-action="toggle" style="margin-left:10px">
        </div>
      </div>
      <div class="card-grid">
        <div class="card-item"><label>Phone / Mobile</label><input type="text" data-field="phone_raw" value="${escapeHtml(row.phone_raw)}"></div>
        <div class="card-item"><label>Total Balance</label><input type="text" data-field="balance" value="${escapeHtml(row.balance)}"></div>
        <div class="card-item"><label>Due Days</label><input type="text" data-field="days" value="${escapeHtml(row.days)}"></div>
        <div class="card-item"><label>Bill Numbers</label><input type="text" data-field="billno" value="${escapeHtml(row.billno)}"></div>
      </div>
      <div style="margin-top:8px">
        <textarea data-field="message" style="height:60px">${escapeHtml(row.message)}</textarea>
      </div>
      <div class="card-actions">
        <button class="btn-remove" data-action="remove">Delete Party</button>
      </div>
    </div>
  `).join("");
}

function handlePreviewInput(e) {
  const target = e.target;
  const card = target.closest(".preview-card");
  if (!card) return;
  const row = state.rows.find(r => r._id === Number(card.dataset.id));
  if (!row) return;
  const f = target.dataset.field;
  if (f === "message") { row.message = target.value; row.customMessage = true; }
  else if (f === "phone_raw") {
    row.phone_raw = target.value;
    row.all_phones = target.value.split(/[/,;]/).map(p => normalizePhone(p, countryCodeInput.value)).filter(Boolean);
    row.phone = row.all_phones[0] || "";
    if (!row.customMessage) row.message = applyTemplate(templateInput.value, row);
  } else {
    row[f] = target.value;
    if (!row.customMessage) row.message = applyTemplate(templateInput.value, row);
  }
  saveDraft();
  renderPreview();
}

function handlePreviewClick(e) {
  const t = e.target;
  const card = t.closest(".preview-card");
  if (!card) return;
  const idx = state.rows.findIndex(r => r._id === Number(card.dataset.id));
  if (t.dataset.action === "toggle") { state.rows[idx].enabled = t.checked; saveDraft(); renderPreview(); }
  else if (t.dataset.action === "remove") { state.rows.splice(idx, 1); saveDraft(); renderPreview(); }
}

function handleTemplateChange() {
  saveDraft();
  state.rows.forEach(r => { if (!r.customMessage) r.message = applyTemplate(templateInput.value, r); });
  renderPreview();
}

function handleCountryCodeChange() {
  saveDraft();
  state.rows.forEach(r => {
    if (r.phone_raw) {
      r.all_phones = r.phone_raw.split(/[/,;]/).map(p => normalizePhone(p, countryCodeInput.value)).filter(Boolean);
      r.phone = r.all_phones[0] || "";
    }
  });
  renderPreview();
}

function setPopupStatus(k, m) { statusBadge.textContent = k; statusText.textContent = m; }

async function startCampaign() {
  const queue = [];
  const randomize = spamGuardInput.checked;

  state.rows.forEach(r => {
    if (!r.enabled) return;
    const phones = r.all_phones?.length ? r.all_phones : (r.phone ? [r.phone] : []);
    phones.forEach(p => {
      let msg = r.message;
      if (randomize) {
        const dots = ["", ".", "..", "..."][Math.floor(Math.random() * 4)];
        msg += dots;
      }
      queue.push({ phone: p, message: msg, _id: r._id });
    });
  });

  if (!queue.length) return setPopupStatus("error", "no recipients");
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url?.includes("web.whatsapp.com")) return setPopupStatus("error", "open whatsapp first");

  await chrome.tabs.sendMessage(tab.id, { type: "WA_QUEUE_START", payload: { queue, settings: { minDelayMs: Number(minDelayInput.value)*1000, maxDelayMs: Number(maxDelayInput.value)*1000 } } });
  setPopupStatus("ok", "campaign started");
}

async function stopQueue() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) chrome.tabs.sendMessage(tab.id, { type: "WA_QUEUE_STOP" });
}

async function refreshStatus() {
  if (typeof chrome === "undefined" || !chrome.storage) return;
  const { waQueueState } = await chrome.storage.local.get("waQueueState");
  if (!waQueueState) return;
  statusBadge.textContent = waQueueState.phase;
  statusText.textContent = waQueueState.message;
  
  if (waQueueState.phase === "sent" || waQueueState.phase === "skip") {
    const id = waQueueState.item?._id;
    const row = state.rows.find(r => r._id === id);
    if (row && row.status !== waQueueState.phase) {
      row.status = waQueueState.phase;
      if (waQueueState.phase === "sent") state.stats.sent++;
      else state.stats.skipped++;
      renderPreview();
      saveDraft();
    }
  }
}

function escapeHtml(s) { return String(s || "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }

async function readTabularFile(f) {
  const ext = f.name.toLowerCase().split('.').pop();
  if (ext === "csv") return parseDelimitedText(await f.text());
  if (ext === "xlsx") return parseXlsxBuffer(await f.arrayBuffer());
  if (ext === "xls") {
    const t = await f.text();
    if (t.trim().startsWith("<")) return parseSpreadsheetXml(t);
    throw new Error("binary .xls not supported");
  }
  throw new Error("unsupported file");
}
function parseDelimitedText(t) { return t.replace(/\ufeff/g, "").split(/\r?\n/).filter(l => l.trim()).map(l => splitLine(l)); }
function splitLine(l) {
  const r = []; let c = ""; let q = false;
  for (let i = 0; i < l.length; i++) {
    if (l[i] === '"') { if (q && l[i+1] === '"') { c += '"'; i++; } else q = !q; }
    else if (l[i] === ',' && !q) { r.push(c); c = ""; }
    else c += l[i];
  }
  r.push(c); return r;
}
async function parseXlsxBuffer(b) {
  const files = await unzipEntries(b);
  const ss = parseSharedStrings(files.get("xl/sharedStrings.xml") || "");
  const wDoc = parseXml(files.get("xl/workbook.xml"));
  const s = wDoc.getElementsByTagNameNS("*", "sheet")[0];
  const rid = s?.getAttribute("r:id") || s?.getAttribute("id");
  const rDoc = parseXml(files.get("xl/_rels/workbook.xml.rels"));
  const rel = Array.from(rDoc.getElementsByTagNameNS("*", "Relationship")).find(i => i.getAttribute("Id") === rid);
  const target = rel?.getAttribute("Target") || "xl/worksheets/sheet1.xml";
  const path = target.startsWith("xl/") ? target : `xl/${target.replace(/^\.\//, "")}`;
  const sheetXml = files.get(path);
  const sDoc = parseXml(sheetXml);
  return Array.from(sDoc.getElementsByTagNameNS("*", "row")).map(r => {
    const res = [];
    Array.from(r.getElementsByTagNameNS("*", "c")).forEach(c => {
      const t = c.getAttribute("t");
      let v = collectText(c, "v");
      if (t === "s") v = ss[Number(v)] || "";
      else if (t === "inlineStr") v = collectText(c, "t");
      res[columnRefToIndex(c.getAttribute("r"))] = v;
    });
    return res.map(v => String(v || "").trim());
  });
}
async function unzipEntries(b) {
  const view = new DataView(b); const bytes = new Uint8Array(b); const entries = new Map(); let offset = 0;
  while (offset + 30 < view.byteLength) {
    if (view.getUint32(offset, true) !== 0x04034b50) break;
    const comp = view.getUint16(offset + 8, true);
    const cSize = view.getUint32(offset + 18, true);
    const nLen = view.getUint16(offset + 26, true);
    const eLen = view.getUint16(offset + 28, true);
    const name = new TextDecoder().decode(bytes.slice(offset + 30, offset + 30 + nLen));
    const compData = bytes.slice(offset + 30 + nLen + eLen, offset + 30 + nLen + eLen + cSize);
    let data;
    if (comp === 0) data = compData;
    else if (comp === 8) data = await inflateRaw(compData);
    entries.set(name, new TextDecoder().decode(data));
    offset += 30 + nLen + eLen + cSize;
  }
  return entries;
}
async function inflateRaw(b) { return new Uint8Array(await new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).arrayBuffer()); }
function parseSharedStrings(t) { return Array.from(parseXml(t).getElementsByTagNameNS("*", "si")).map(n => collectText(n, "t")); }
function parseSpreadsheetXml(t) { return Array.from(parseXml(t).getElementsByTagNameNS("*", "Row")).map(r => Array.from(r.getElementsByTagNameNS("*", "Cell")).map(c => (c.getElementsByTagNameNS("*", "Data")[0]?.textContent || "").trim())); }
function parseXml(t) { return new DOMParser().parseFromString(t, "application/xml"); }
function collectText(n, t) { return Array.from(n.getElementsByTagNameNS("*", t)).map(i => i.textContent || "").join("").trim(); }
function columnRefToIndex(r) { let i = 0; const l = r.replace(/\d/g, ""); for (let j = 0; j < l.length; j++) i = i * 26 + (l.charCodeAt(j) - 64); return Math.max(i - 1, 0); }
