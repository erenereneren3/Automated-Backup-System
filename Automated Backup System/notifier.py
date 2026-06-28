"""
notifier.py — Telegram notification handler.
Sends success/failure messages via the Telegram Bot API.
If no token is configured, all calls silently do nothing.
"""

import logging
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    API_BASE = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token.strip()
        self.chat_id = str(chat_id).strip()
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.info("Telegram notifications disabled (no token/chat_id configured).")

    def send(self, message: str) -> bool:
        """Send a plain-text message. Returns True on success, False on failure."""
        if not self.enabled:
            return False

        url = self.API_BASE.format(token=self.bot_token)
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.debug("Telegram message sent successfully.")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to send Telegram notification: {e}")
            return False

    def notify_success(self, backup_name: str, size_mb: float, duration_sec: float, file_count: int):
        """Send a structured success notification."""
        message = (
            "✅ <b>Backup Successful</b>\n\n"
            f"📦 <b>File:</b> {backup_name}\n"
            f"📁 <b>Files backed up:</b> {file_count}\n"
            f"💾 <b>Size:</b> {size_mb:.2f} MB\n"
            f"⏱ <b>Duration:</b> {duration_sec:.1f}s"
        )
        self.send(message)

    def notify_failure(self, error_message: str):
        """Send a structured failure notification."""
        message = (
            "❌ <b>Backup Failed</b>\n\n"
            f"🔴 <b>Error:</b> {error_message}"
        )
        self.send(message)
