(function bootstrap() {
  const STORAGE_KEY = "waQueueState";
  const SESSION_KEY = "waQueueSession";
  let isProcessing = false;

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "WA_QUEUE_START") {
      startQueue(message.payload).then(() => sendResponse({ ok: true }));
      return true;
    }

    if (message?.type === "WA_QUEUE_STOP") {
      stopQueue().then(() => sendResponse({ ok: true }));
      return true;
    }

    return false;
  });

  resumeQueue();

  async function startQueue(payload) {
    const queue = Array.isArray(payload?.queue) ? payload.queue : [];
    const settings = sanitizeSettings(payload?.settings || {});

    if (!queue.length) {
      await updateState({ phase: "error", message: "Queue is empty.", error: true });
      return;
    }

    await chrome.storage.local.set({
      [SESSION_KEY]: {
        running: true,
        index: 0,
        queue,
        settings,
      },
    });

    await updateState({
      phase: "queued",
      message: `Queue loaded with ${queue.length} recipients.`,
      error: false,
    });

    await processQueue();
  }

  async function stopQueue() {
    const { waQueueSession } = await chrome.storage.local.get(SESSION_KEY);
    if (!waQueueSession) return;

    waQueueSession.running = false;
    await chrome.storage.local.set({ [SESSION_KEY]: waQueueSession });
    await updateState({
      phase: "stopping",
      message: "Stop requested. Finishing current step safely.",
      error: false,
    });
  }

  async function resumeQueue() {
    const { waQueueSession } = await chrome.storage.local.get(SESSION_KEY);
    if (!waQueueSession?.running) {
      await updateState({
        phase: "idle",
        message: "WhatsApp tab is ready. Start a queue from the extension popup.",
        error: false,
      });
      return;
    }

    await processQueue();
  }

  async function processQueue() {
    if (isProcessing) return;
    isProcessing = true;

    try {
      const { waQueueSession } = await chrome.storage.local.get(SESSION_KEY);
      if (!waQueueSession?.running) return;

      const session = waQueueSession;
      const queue = session.queue || [];

      while (session.running && session.index < queue.length) {
        const item = queue[session.index];
        await updateState({
          phase: "sending",
          message: `Opening chat ${session.index + 1}/${queue.length} for ${item.phone}`,
          error: false,
        });

        await openChatInSameTab(item);
        await sendCurrentMessage(item.phone);

        session.index += 1;
        await chrome.storage.local.set({ [SESSION_KEY]: session });

        if (session.index < queue.length) {
          const delayMs = randomBetween(session.settings.minDelayMs, session.settings.maxDelayMs);
          await updateState({
            phase: "waiting",
            message: `Sent to ${item.phone}. Waiting ${Math.round(delayMs / 1000)} seconds before the next chat.`,
            error: false,
          });
          await sleep(delayMs);
        }

        const latest = await chrome.storage.local.get(SESSION_KEY);
        if (!latest.waQueueSession?.running) {
          await updateState({
            phase: "stopped",
            message: "Queue stopped by user.",
            error: false,
          });
          return;
        }
      }

      session.running = false;
      await chrome.storage.local.set({ [SESSION_KEY]: session });
      await updateState({
        phase: "done",
        message: `Queue complete. Processed ${queue.length} recipients in the current WhatsApp session.`,
        error: false,
      });
    } catch (error) {
      await updateState({
        phase: "error",
        message: error.message || String(error),
        error: true,
      });
      const { waQueueSession } = await chrome.storage.local.get(SESSION_KEY);
      if (waQueueSession) {
        waQueueSession.running = false;
        await chrome.storage.local.set({ [SESSION_KEY]: waQueueSession });
      }
    } finally {
      isProcessing = false;
    }
  }

  async function openChatInSameTab(item) {
    if (detectLoginBlocker()) {
      throw new Error("WhatsApp Web is not logged in. Clear the QR/login screen before starting the queue.");
    }

    const phone = item.phone.replace(/[^\d]/g, "");
    
    // 1. Find Search Input
    const searchInput = await waitForElement([
      'div[contenteditable="true"][data-tab="3"]',
      'div[title="Search input textbox"]',
      '#side div[role="textbox"]'
    ], 10000);

    // 2. Clear and Type Number
    searchInput.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, phone);
    
    await sleep(1500); // Wait for results

    // 3. Find and Click the chat result
    // We look for:
    // a) An existing contact match
    // b) The "Chat with +91..." button for new numbers
    const chatResult = await waitForElement([
      `span[title="${phone}"]`,
      `span[title="+${phone}"]`,
      'div[role="button"] span[dir="auto"]', // Possible "Chat with..." text
      'div[role="listitem"]', 
      '#pane-side div[role="row"]'
    ], 8000).catch(() => null);

    let clicked = false;
    if (chatResult) {
      // If it's the "Chat with..." or a contact, click it
      const parentBtn = chatResult.closest('div[role="button"], div[role="listitem"], div[role="row"]');
      if (parentBtn) {
        parentBtn.click();
        clicked = true;
      } else {
        chatResult.click();
        clicked = true;
      }
      await sleep(1500);
    }

    if (!clicked) {
       // Fallback ONLY if search fails completely
       const url = `https://web.whatsapp.com/send?phone=${phone}&text=${encodeURIComponent(item.message)}`;
       // Only assign if we aren't already on a similar URL
       if (!window.location.href.includes(phone)) {
         window.location.assign(url);
         await waitForPageSettled();
         return;
       }
    }

    // 4. Find Message Input and Insert Text
    const msgInput = await waitForElement([
      'div[contenteditable="true"][data-tab="10"]',
      'div[title="Type a message"]',
      'footer div[role="textbox"]'
    ], 10000);

    msgInput.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, item.message);
    await sleep(500);
  }

  async function sendCurrentMessage(phone) {
    if (detectLoginBlocker()) {
      throw new Error("WhatsApp Web returned to a login/QR state before sending.");
    }

    try {
      const sendButton = await waitForElement([
        'button[aria-label="Send"]',
        'button span[data-icon="send"]',
        'button[data-testid="compose-btn-send"]',
        'div[role="button"] span[data-icon="send"]'
      ], 10000);

      const clickable = sendButton.closest("button,[role='button']") || sendButton;
      clickable.click();

      await updateState({
        phase: "sent",
        message: `Sent to ${phone}.`,
        error: false,
      });

      await sleep(2000);
    } catch (err) {
      const handled = await checkInvalidNumber();
      if (handled) {
        await updateState({
          phase: "skip",
          message: `Skipped ${phone}: Not on WhatsApp.`,
          error: false,
        });
        return;
      }
      throw err;
    }
  }

  async function checkInvalidNumber() {
    const dialog = document.querySelector('div[role="dialog"]');
    if (!dialog) return false;

    const text = dialog.innerText.toLowerCase();
    if (text.includes("invalid") || text.includes("not on whatsapp") || text.includes("not found")) {
      const okBtn = dialog.querySelector('button, div[role="button"]');
      if (okBtn) {
        okBtn.click();
        await sleep(1000);
        return true;
      }
    }
    return false;
  }

  function detectLoginBlocker() {
    return Boolean(
      document.querySelector('[data-testid="qrcode"]') ||
      document.body.innerText.includes("Link with phone") ||
      document.body.innerText.includes("Keep your phone connected")
    );
  }

  async function waitForPageSettled() {
    await waitForCondition(() => document.readyState === "complete", 15000);
    await waitForCondition(() => !document.querySelector("[data-testid='intro-md-beta-logo-dark']"), 8000).catch(() => {});
    await sleep(1800);
  }

  async function waitForElement(selectors, timeoutMs) {
    const selectorList = Array.isArray(selectors) ? selectors : [selectors];
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      for (const selector of selectorList) {
        const node = document.querySelector(selector);
        if (node) return node;
      }
      await sleep(500);
    }

    throw new Error(`Timed out waiting for element: ${selectorList.join(", ")}`);
  }

  async function waitForCondition(condition, timeoutMs) {
    const startedAt = Date.now();
    while (Date.now() - startedAt < timeoutMs) {
      if (condition()) return true;
      await sleep(250);
    }
    throw new Error("Timed out waiting for WhatsApp Web to settle.");
  }

  async function updateState(next) {
    await chrome.storage.local.set({
      [STORAGE_KEY]: {
        updatedAt: Date.now(),
        ...next,
      },
    });
  }

  function sanitizeSettings(settings) {
    const minDelayMs = Math.max(5000, Number(settings.minDelayMs) || 18000);
    const maxDelayMs = Math.max(minDelayMs, Number(settings.maxDelayMs) || 35000);
    return { minDelayMs, maxDelayMs };
  }

  function randomBetween(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function sleep(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }
})();
