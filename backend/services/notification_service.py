from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from backend.config import settings


class NotificationService:
    def __init__(self) -> None:
        self.bot = Bot(token=settings.telegram_bot_token)
        self.chat_id = settings.telegram_chat_id

    async def send_track_message(
        self,
        artist: str,
        track_name: str,
        album: str | None,
        explanation: str,
        spotify_url: str,
        track_id: int,
    ) -> int:
        """
        Send formatted track message with inline feedback buttons.
        Returns the Telegram message_id.
        """
        text = (
            f"🎵 *Today's Music Discovery*\n\n"
            f"*Artist:* {self._escape_md(artist)}\n"
            f"*Track:* {self._escape_md(track_name)}\n"
            f"*Album:* {self._escape_md(album or 'Unknown')}\n\n"
            f"_About this track:_\n"
            f"{self._escape_md(explanation)}\n\n"
            f"🔗 [Listen on Spotify]({self._escape_md_url(spotify_url)})"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👍 Like", callback_data=f"like:{track_id}"),
                InlineKeyboardButton("👎 Dislike", callback_data=f"dislike:{track_id}"),
                InlineKeyboardButton("⏭ Skip", callback_data=f"skip:{track_id}"),
            ]
        ])

        message = await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
        return message.message_id

    async def send_notification(self, text: str) -> int:
        """Send a plain text notification."""
        message = await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
        )
        return message.message_id

    @staticmethod
    def _escape_md(text: str) -> str:
        """Escape MarkdownV2 special characters for Telegram."""
        for char in [
            "_", "*", "[", "]", "(", ")", "~", "`",
            ">", "#", "+", "-", "=", "|", "{", "}", ".", "!",
        ]:
            text = text.replace(char, f"\\{char}")
        return text

    @staticmethod
    def _escape_md_url(url: str) -> str:
        """Escape only the chars that need escaping inside MarkdownV2 URL parentheses."""
        for char in [")", "\\"]:
            url = url.replace(char, f"\\{char}")
        return url
