# WhatsApp Messaging Workspace

This repo now has two tracks:

- `browser-extension/`
  The new Chrome/Edge extension that works inside the currently logged-in `web.whatsapp.com` session.
- `legacy-python-app/`
  The original desktop Python application, preserved as-is for reference and fallback.

## Recommended Path

Use the extension going forward if your goal is to stay inside one WhatsApp Web session and avoid the Python app's extra browser-tab behavior.

## Extension Quick Start

1. Open `chrome://extensions` or `edge://extensions`
2. Enable `Developer mode`
3. Load unpacked extension from `browser-extension/`
4. Open `https://web.whatsapp.com/` and log in
5. Load a CSV queue from the popup and start from the active WhatsApp tab

## Legacy App

The older Python project is now under `legacy-python-app/`, including its docs and helper scripts.
