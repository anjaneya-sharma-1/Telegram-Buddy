# Buddy - Your Friendly Telegram Bot

A Python Telegram bot with three intelligent messaging modes designed to be your friendly chat companion.

## Features

🤖 **Three Smart Modes:**
- **Single Mode** (`/single`): Batches your messages for 5 seconds, then responds with one thoughtful reply
- **Parallel Mode** (`/parallel`): Starts thinking immediately but restarts if you send more messages  
- **Stitch Mode** (`/stitch`): Simply echoes back your combined messages (great for testing!)

✨ **Smart Features:**
- Per-user mode management (each user has their own settings)
- Typing indicators while Buddy is thinking
- Configurable batching window (default 5 seconds)
- Async message handling with proper cancellation
- Friendly, conversational AI personality

## Setup

### Prerequisites
- Python 3.8+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- Groq API Key (included in `.env`)

### Installation

1. **Clone or download this project**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Edit `.env` file
   - Add your Telegram Bot Token:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token_here
     ```
   - Groq API key is already configured

4. **Run the bot:**
   ```bash
   python buddy_bot.py
   ```

## Usage

### Getting Started
1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Choose a mode with `/single`, `/parallel`, or `/stitch`
4. Start chatting!

### Commands
- `/start` - Welcome message and instructions
- `/single` - Switch to single mode (batch then respond)
- `/parallel` - Switch to parallel mode (immediate response, restarts if new messages)
- `/stitch` - Switch to stitch mode (echo only)

### How Each Mode Works

#### Single Mode (`/single`)
```
You: "Hello"
You: "How are you?"
You: "What's the weather like?"
[5 second wait]
Buddy: [One combined response to all three messages]
```

#### Parallel Mode (`/parallel`)  
```
You: "Hello"
[Buddy starts thinking immediately]
You: "How are you?" 
[Buddy cancels previous response and restarts with both messages]
[5 second wait or response completion]
Buddy: [Response to combined messages]
```

#### Stitch Mode (`/stitch`)
```
You: "Hello"
You: "How are you?"
[5 second wait]
Buddy: "You said: Hello How are you?"
```

## Configuration

Edit the bot configuration in `buddy_bot.py`:
- `BATCH_WINDOW = 5.0` - Message batching window in seconds
- Groq model and parameters in `_generate_ai_response()`
- Bot personality in the system prompt

## Architecture

- **Async/await**: Full asyncio support for concurrent user handling
- **Per-user state**: Each user maintains independent mode and message state
- **Proper cancellation**: AI tasks and timers are properly cancelled when needed
- **Error handling**: Graceful error handling with user-friendly messages
- **Typing indicators**: Shows when Buddy is thinking

## Files Structure

```
telegram buddy/
├── buddy_bot.py      # Main bot application
├── requirements.txt  # Python dependencies  
├── .env             # Environment configuration
└── README.md        # This file
```

## Dependencies

- `python-telegram-bot==20.7` - Telegram Bot API wrapper
- `groq==0.4.1` - Groq AI API client
- `python-dotenv==1.0.0` - Environment variable loading
- `asyncio` - Async programming support

## Error Handling

The bot includes comprehensive error handling:
- Network errors with Groq API
- Telegram API errors  
- Malformed messages
- User-friendly error messages
- Logging for debugging

## Development

To modify Buddy's personality, edit the `system_prompt` in the `_generate_ai_response()` method:

```python
system_prompt = (
    "You are Buddy, a friendly and casual chat companion. "
    "You're helpful, empathetic, and speak like a good friend would - "
    "warm, supportive, and conversational. Keep responses natural and engaging. "
    "You can use emojis when appropriate to add friendliness. "
    "Be concise but thoughtful in your responses."
)
```

## License

This project is open source. Feel free to modify and distribute!

---

Happy chatting with Buddy! 🤖✨