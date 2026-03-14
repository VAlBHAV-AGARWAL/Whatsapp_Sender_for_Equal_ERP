"""WhatsApp sending helpers using pywhatkit only."""

from __future__ import annotations

import importlib
import logging
import subprocess
import time
import webbrowser
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class WhatsAppBot:
    """WhatsApp sender that relies only on pywhatkit."""

    def __init__(
        self,
        log_callback: Optional[Callable[[str], None]] = None,
        send_mode: str = "pywhatkit",
    ) -> None:
        self.log_callback = log_callback or logger.info
        self.send_mode = send_mode
        self._pywhatkit: Any = None
        self._wa_bootstrapped = False

        if self.send_mode not in {"pywhatkit", "auto"}:
            raise ValueError(
                "Only pywhatkit mode is supported. "
                "Set send_mode to 'pywhatkit' or 'auto'."
            )

        self.log_callback("Sender initialized: pywhatkit mode")

    def _is_browser_running(self) -> bool:
        """Check if a common desktop browser process is already running."""
        try:
            result = subprocess.run(
                ["tasklist"],
                capture_output=True,
                text=True,
                check=False,
            )
            tasks = result.stdout.lower()
            return any(name in tasks for name in ("chrome.exe", "msedge.exe", "firefox.exe"))
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _ensure_whatsapp_web_open(self) -> None:
        """Open WhatsApp Web if no browser is currently running."""
        if self._wa_bootstrapped and self._is_browser_running():
            return

        if not self._is_browser_running():
            self.log_callback("No browser detected, opening WhatsApp Web...")
            webbrowser.open("https://web.whatsapp.com/")
            time.sleep(8)

        self._wa_bootstrapped = True

    def _import_pywhatkit(self) -> Any:
        """Lazy import pywhatkit to keep startup resilient if dependency is missing."""
        if self._pywhatkit is not None:
            return self._pywhatkit

        try:
            self._pywhatkit = importlib.import_module("pywhatkit")
            return self._pywhatkit
        except ImportError as exc:
            raise RuntimeError(
                "pywhatkit is not installed. Run: pip install pywhatkit"
            ) from exc

    @staticmethod
    def _force_enter_send() -> None:
        """
        Force-send by pressing ENTER.
        Useful when WhatsApp pre-fills text but doesn't auto-submit.
        """
        try:
            pyautogui = importlib.import_module("pyautogui")
            time.sleep(1.2)
            pyautogui.press("enter")
            time.sleep(0.6)
        except Exception:
            # Keep non-fatal; pywhatkit may have already sent the message.
            pass

    def send_message(self, phone_number: str, message: str) -> bool:
        """Send a WhatsApp message to one number via pywhatkit."""
        phone_number = str(phone_number).strip()
        if not phone_number.startswith("+"):
            phone_number = "+91" + phone_number.lstrip("0")

        self.log_callback(f"Preparing to send to {phone_number}...")
        self._ensure_whatsapp_web_open()

        try:
            pywhatkit = self._import_pywhatkit()
            pywhatkit.sendwhatmsg_instantly(
                phone_no=phone_number,
                message=message,
                wait_time=15,
                tab_close=False,
                close_time=3,
            )
            self._force_enter_send()
            time.sleep(2)
            self.log_callback(f"Message sent to {phone_number} using pywhatkit")
            return True
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise RuntimeError(f"pywhatkit send failed: {exc}") from exc

    def close(self) -> None:
        """No-op for compatibility with existing app flow."""
        return

    def __del__(self) -> None:
        self.close()
