#!/usr/bin/env python3
"""
Buddy - Your Friendly Telegram Bot

A Telegram bot with three modes:
- /single: Batch messages and respond once after the window
- /parallel: Start AI generation immediately, cancel if new messages arrive
- /stitch: Only batch and echo back the stitched message

Author: Anjaneya Sharma
Version: 1.0
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    ContextTypes,
    filters
)
from telegram.constants import ChatAction
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BATCH_WINDOW = 5.0  # seconds
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required")


class BotMode(Enum):
    """Available bot modes"""
    SINGLE = "single"
    PARALLEL = "parallel" 
    STITCH = "stitch"


@dataclass
class UserState:
    """State for each user"""
    mode: BotMode = BotMode.SINGLE
    pending_messages: List[str] = field(default_factory=list)
    timer_task: Optional[asyncio.Task] = None
    ai_task: Optional[asyncio.Task] = None
    last_activity: datetime = field(default_factory=datetime.now)
    prepared_response: Optional[str] = None


class BuddyBot:
    """
    Buddy - Your friendly Telegram bot
    
    Handles three different message processing modes with per-user state management.
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.user_states: Dict[int, UserState] = {}
        self.typing_users: Set[int] = set()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user_id = update.effective_user.id
        self.user_states[user_id] = UserState()
        
        welcome_message = (
            "👋 Hey there! I'm Buddy, your friendly chat companion!\n\n"
            "I have three different modes to chat with you:\n\n"
            "🔸 `/single` - I'll wait for all your messages in a 5-second window, "
            "then give you one thoughtful response\n\n"
            "🔸 `/parallel` - I start thinking as soon as you message me, but if you "
            "send more messages, I'll restart with everything combined\n\n"
            "🔸 `/stitch` - I just repeat back what you said (great for testing!)\n\n"
            "Currently in **single** mode. What's on your mind? 😊"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
    async def mode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, mode: BotMode) -> None:
        """Handle mode switching commands"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_states:
            self.user_states[user_id] = UserState()
            
        # Cancel any pending operations
        await self._cancel_user_operations(user_id)
        
        self.user_states[user_id].mode = mode
        
        mode_descriptions = {
            BotMode.SINGLE: "I'll batch your messages and respond once after the window closes! 📦",
            BotMode.PARALLEL: "I'll start working immediately but restart if you send more messages! ⚡",
            BotMode.STITCH: "I'll just echo back your combined messages! 🔁"
        }
        
        await update.message.reply_text(
            f"Switched to **{mode.value}** mode! {mode_descriptions[mode]}",
            parse_mode='Markdown'
        )
        
    async def single_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /single command"""
        await self.mode_command(update, context, BotMode.SINGLE)
        
    async def parallel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /parallel command"""
        await self.mode_command(update, context, BotMode.PARALLEL)
        
    async def stitch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stitch command"""
        await self.mode_command(update, context, BotMode.STITCH)
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming text messages"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Initialize user state if needed
        if user_id not in self.user_states:
            self.user_states[user_id] = UserState()
            
        user_state = self.user_states[user_id]
        user_state.last_activity = datetime.now()
        user_state.pending_messages.append(message_text)
        
        logger.info(f"User {user_id} ({user_state.mode.value} mode): {message_text}")
        
        if user_state.mode == BotMode.SINGLE:
            await self._handle_single_mode(update, context, user_id)
        elif user_state.mode == BotMode.PARALLEL:
            await self._handle_parallel_mode(update, context, user_id)
        elif user_state.mode == BotMode.STITCH:
            await self._handle_stitch_mode(update, context, user_id)
            
    async def _handle_single_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle message in single mode"""
        user_state = self.user_states[user_id]
        
        # Start typing indicator immediately when first message arrives
        if len(user_state.pending_messages) == 1:
            await self._start_typing(context.bot, update.effective_chat.id)
        
        # Cancel existing timer if any
        if user_state.timer_task and not user_state.timer_task.done():
            user_state.timer_task.cancel()
            
        # Start new timer
        user_state.timer_task = asyncio.create_task(
            self._batch_timer(update, context, user_id)
        )
        
    async def _handle_parallel_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle message in parallel mode"""
        user_state = self.user_states[user_id]
        
        # Start typing indicator immediately when first message arrives
        if len(user_state.pending_messages) == 1:
            await self._start_typing(context.bot, update.effective_chat.id)
        
        # Cancel existing AI task if running
        if user_state.ai_task and not user_state.ai_task.done():
            user_state.ai_task.cancel()
            
        # Cancel existing timer if any
        if user_state.timer_task and not user_state.timer_task.done():
            user_state.timer_task.cancel()
            
        # Start AI generation immediately
        user_state.ai_task = asyncio.create_task(
            self._generate_ai_response(update, context, user_id, wait_for_batch=True)
        )
        
        # Start timer for potential new messages
        user_state.timer_task = asyncio.create_task(
            self._batch_timer(update, context, user_id)
        )
        
    async def _handle_stitch_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle message in stitch mode"""
        user_state = self.user_states[user_id]
        
        # Start typing indicator immediately when first message arrives
        if len(user_state.pending_messages) == 1:
            await self._start_typing(context.bot, update.effective_chat.id)
        
        # Cancel existing timer if any
        if user_state.timer_task and not user_state.timer_task.done():
            user_state.timer_task.cancel()
            
        # Start new timer
        user_state.timer_task = asyncio.create_task(
            self._batch_timer(update, context, user_id)
        )
        
    async def _batch_timer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Timer for batching window"""
        try:
            await asyncio.sleep(BATCH_WINDOW)
            
            user_state = self.user_states[user_id]
            
            if user_state.mode == BotMode.SINGLE:
                await self._generate_ai_response(update, context, user_id)
            elif user_state.mode == BotMode.PARALLEL:
                # In parallel mode, AI task should already be running or completed
                if user_state.ai_task and not user_state.ai_task.done():
                    # Wait for AI task to complete
                    await user_state.ai_task
                
                # Send the prepared response after batch window
                await self._send_prepared_response(update, context, user_id)
            elif user_state.mode == BotMode.STITCH:
                await self._send_stitched_response(update, context, user_id)
                
        except asyncio.CancelledError:
            logger.debug(f"Batch timer cancelled for user {user_id}")
            
    async def _generate_ai_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, wait_for_batch: bool = False) -> None:
        """Generate AI response using Groq"""
        user_state = self.user_states[user_id]
        
        if not user_state.pending_messages:
            return
            
        try:
            # Typing indicator already started when first message arrived
            # Just ensure it's still active
            await self._start_typing(context.bot, update.effective_chat.id)
            
            # Stitch messages together
            stitched_message = " ".join(user_state.pending_messages)
            
            # Create friend-like prompt for Buddy
            system_prompt = (
                "You are Buddy, a friendly and casual chat companion. "
                "You're helpful, empathetic, and speak like a good friend would - "
                "warm, supportive, and conversational. Keep responses natural and engaging. "
                "You can use emojis when appropriate to add friendliness. "
                "Be concise but thoughtful in your responses."
            )
            
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": stitched_message}
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            
            ai_response = response.choices[0].message.content
            
            # In parallel mode, store the response but don't send yet if we need to wait
            if wait_for_batch:
                user_state.prepared_response = ai_response
                return
            
            # Stop typing indicator
            await self._stop_typing(user_id)
            
            # Send response
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=ai_response
            )
            
            # Clear pending messages
            user_state.pending_messages.clear()
            
        except asyncio.CancelledError:
            await self._stop_typing(user_id)
            logger.debug(f"AI generation cancelled for user {user_id}")
        except Exception as e:
            await self._stop_typing(user_id)
            logger.error(f"Error generating AI response for user {user_id}: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Oops! I had a hiccup there. Could you try again? 😅"
            )
            user_state.pending_messages.clear()
            
    async def _send_stitched_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Send stitched message response"""
        user_state = self.user_states[user_id]
        
        if not user_state.pending_messages:
            return
            
        try:
            # Typing indicator already started when first message arrived
            # Just ensure it's still active
            await self._start_typing(context.bot, update.effective_chat.id)
            
            # Brief delay to simulate processing
            await asyncio.sleep(1)
            
            # Stitch messages together
            stitched_message = " ".join(user_state.pending_messages)
            
            # Stop typing indicator
            await self._stop_typing(user_id)
            
            # Send stitched response
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"You said: {stitched_message}"
            )
            
            # Clear pending messages
            user_state.pending_messages.clear()
            
        except Exception as e:
            await self._stop_typing(user_id)
            logger.error(f"Error sending stitched response for user {user_id}: {e}")
            
    async def _send_prepared_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Send prepared AI response in parallel mode"""
        user_state = self.user_states[user_id]
        
        if not user_state.prepared_response:
            return
            
        try:
            # Stop typing indicator
            await self._stop_typing(user_id)
            
            # Send the prepared response
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=user_state.prepared_response
            )
            
            # Clear pending messages and prepared response
            user_state.pending_messages.clear()
            user_state.prepared_response = None
            
        except Exception as e:
            await self._stop_typing(user_id)
            logger.error(f"Error sending prepared response for user {user_id}: {e}")
            
    async def _start_typing(self, bot: Bot, chat_id: int) -> None:
        """Start typing indicator"""
        user_id = chat_id  # Assuming chat_id is user_id for private chats
        if user_id not in self.typing_users:
            self.typing_users.add(user_id)
            try:
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            except Exception as e:
                logger.error(f"Error starting typing indicator: {e}")
                
    async def _stop_typing(self, user_id: int) -> None:
        """Stop typing indicator"""
        self.typing_users.discard(user_id)
        
    async def _cancel_user_operations(self, user_id: int) -> None:
        """Cancel all pending operations for a user"""
        if user_id not in self.user_states:
            return
            
        user_state = self.user_states[user_id]
        
        # Cancel timer task
        if user_state.timer_task and not user_state.timer_task.done():
            user_state.timer_task.cancel()
            
        # Cancel AI task
        if user_state.ai_task and not user_state.ai_task.done():
            user_state.ai_task.cancel()
            
        # Stop typing
        await self._stop_typing(user_id)
        
        # Clear pending messages and prepared response
        user_state.pending_messages.clear()
        user_state.prepared_response = None
        
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")


def main():
    """Main function to run the bot"""
    # Create bot instance
    buddy = BuddyBot()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", buddy.start_command))
    application.add_handler(CommandHandler("single", buddy.single_command))
    application.add_handler(CommandHandler("parallel", buddy.parallel_command))
    application.add_handler(CommandHandler("stitch", buddy.stitch_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buddy.handle_message))
    
    # Add error handler
    application.add_error_handler(buddy.error_handler)
    
    # Start the bot
    logger.info("Starting Buddy bot...")
    application.run_polling()


if __name__ == '__main__':
    main()