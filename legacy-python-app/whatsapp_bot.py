"""WhatsApp sending helpers using pywhatkit only."""

from __future__ import annotations

import importlib
import logging
import re
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
        self._connection_validated = False

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

    def _get_pywhatkit(self) -> Any:
        """Import pywhatkit lazily so app startup stays light."""
        if self._pywhatkit is None:
            self._pywhatkit = importlib.import_module("pywhatkit")
        return self._pywhatkit

    @staticmethod
    def _normalize_phone_number(phone_number: str) -> str:
        """Return a WhatsApp-friendly international phone number."""
        cleaned = re.sub(r"[^\d+]", "", str(phone_number).strip())
        if not cleaned:
            raise ValueError("Phone number is empty")
        if not cleaned.startswith("+"):
            cleaned = f"+{cleaned.lstrip('+')}"
        digits_only = cleaned[1:]
        if not digits_only.isdigit():
            raise ValueError(f"Invalid phone number: {phone_number}")
        if len(digits_only) < 10:
            raise ValueError(f"Phone number is too short: {phone_number}")
        return cleaned

    def validate_connection(self) -> bool:
        """Validate WhatsApp Web connection is ready for sending."""
        try:
            self.log_callback("Validating WhatsApp Web connection...")
            self.log_callback("Note: For accurate validation, install: pip install pyautogui pytesseract")

            # Don't call _ensure_whatsapp_web_open here since we explicitly open WhatsApp Web in connect_whatsapp()
            # Just give time for WhatsApp Web to load if it was just opened
            time.sleep(3)

            # Check if we have advanced validation tools
            has_pyautogui = False
            has_ocr = False

            try:
                importlib.import_module("pyautogui")
                has_pyautogui = True
            except ImportError:
                pass

            try:
                importlib.import_module("pytesseract")
                has_ocr = True
            except ImportError:
                pass

            if not has_pyautogui:
                # Limited validation - just check if browser is running
                if self._is_browser_running():
                    self._connection_validated = True
                    self.log_callback("Limited validation: Browser detected - please ensure WhatsApp Web is logged in")
                    self.log_callback("For better validation, install: pip install pyautogui pytesseract")
                    return True
                else:
                    self.log_callback("No browser detected - open WhatsApp Web first")
                    return False

            # Advanced validation with pyautogui
            try:
                pyautogui = importlib.import_module("pyautogui")

                # Take a screenshot of the browser area
                screenshot = pyautogui.screenshot()

                # Try to detect QR code (indicates not logged in)
                if has_ocr:
                    try:
                        pytesseract = importlib.import_module("pytesseract")
                        # Convert to grayscale for better OCR
                        gray_screenshot = screenshot.convert('L')
                        text = pytesseract.image_to_string(gray_screenshot).lower()

                        # Check for QR code related text
                        qr_indicators = ['scan', 'qr', 'code', 'whatsapp web', 'link with phone']
                        if any(indicator in text for indicator in qr_indicators):
                            self.log_callback("QR code detected - WhatsApp Web not logged in")
                            return False

                        # Check for logged in indicators
                        logged_in_indicators = ['search', 'chats', 'new chat', 'menu']
                        if any(indicator in text for indicator in logged_in_indicators):
                            self._connection_validated = True
                            self.log_callback("WhatsApp Web appears to be logged in and ready")
                            return True

                    except Exception as exc:
                        self.log_callback(f"OCR validation failed: {exc}")

                # Fallback method without OCR
                # Check for typical WhatsApp Web color patterns
                pixels = list(screenshot.getdata())
                width, height = screenshot.size

                # Check center area for QR code (bright white area)
                center_x, center_y = width // 2, height // 2
                center_region = screenshot.crop((center_x - 100, center_y - 100, center_x + 100, center_y + 100))
                center_pixels = list(center_region.getdata())

                # Calculate average brightness in center
                avg_brightness = sum(sum(pixel) / 3 for pixel in center_pixels) / len(center_pixels)

                if avg_brightness > 200:  # Very bright center suggests QR code
                    self.log_callback("Bright center area detected - likely QR code (not logged in)")
                    return False

                # Check for WhatsApp green color (#25D366)
                green_count = sum(1 for r, g, b in pixels if g > 100 and g > r and g > b)
                green_ratio = green_count / len(pixels)

                if green_ratio > 0.005:  # At least 0.5% green pixels suggest logged in
                    self._connection_validated = True
                    self.log_callback("WhatsApp green theme detected - likely logged in")
                    return True

                # If we can't determine status, assume it's ready (better than blocking)
                self._connection_validated = True
                self.log_callback("Connection validation inconclusive - assuming WhatsApp Web is ready")
                self.log_callback("Please manually verify WhatsApp Web is logged in before sending")
                return True

            except Exception as exc:
                self.log_callback(f"Advanced validation error: {exc}")
                # Fallback to basic validation
                if self._is_browser_running():
                    self._connection_validated = True
                    self.log_callback("Basic validation: Browser detected - please ensure WhatsApp Web is logged in")
                    return True
                else:
                    self.log_callback("No browser detected")
                    return False

        except Exception as exc:
            self.log_callback(f"Connection validation error: {exc}")
            return False

    def send_message(self, phone_number: str, message: str) -> None:
        """Send a WhatsApp message using pywhatkit."""
        normalized_phone = self._normalize_phone_number(phone_number)
        text = str(message).strip()
        if not text:
            raise ValueError("Message is empty")

        self._ensure_whatsapp_web_open()
        pywhatkit = self._get_pywhatkit()

        self.log_callback(f"Preparing WhatsApp Web for {normalized_phone}")
        try:
            pywhatkit.sendwhatmsg_instantly(
                normalized_phone,
                text,
                wait_time=20,
                tab_close=False,
                close_time=3,
            )
            self._connection_validated = True
            self.log_callback(f"Message queued for {normalized_phone}")
            time.sleep(8)
        except Exception as exc:
            self.invalidate_connection()
            raise RuntimeError(f"pywhatkit send failed for {normalized_phone}: {exc}") from exc

    def is_connection_valid(self) -> bool:
        """Check if connection has been validated."""
        return getattr(self, '_connection_validated', False)

    def invalidate_connection(self) -> None:
        """Mark the connection as invalid."""
        self._connection_validated = False

    def close(self) -> None:
        """Clean up resources and invalidate connection."""
        self.invalidate_connection()
        return

    def __del__(self) -> None:
        self.close()
