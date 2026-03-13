import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from backend.agents.feedback_agent import FeedbackAgent
from backend.agents.taste_model_agent import TasteModelAgent
from backend.config import settings
from backend.database.db import async_session

logger = logging.getLogger(__name__)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    try:
        feedback_type, track_id = FeedbackAgent.parse_callback_data(query.data)
    except ValueError:
        logger.warning("Invalid callback data: %s", query.data)
        return

    # Single session for feedback + taste update
    async with async_session() as session:
        feedback_agent = FeedbackAgent()
        await feedback_agent.process_feedback(session, feedback_type, track_id)

        taste_agent = TasteModelAgent()
        await taste_agent.update_from_feedback(session, feedback_type, track_id)

        await session.commit()

    # Confirm to user
    emoji_map = {"like": "👍", "dislike": "👎", "skip": "⏭"}
    emoji = emoji_map.get(feedback_type, "✓")
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(
        f"{emoji} Feedback recorded! Thanks for helping me learn your taste."
    )


def create_telegram_app() -> Application:
    """Create and configure the Telegram bot application."""
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CallbackQueryHandler(handle_callback))
    return app
