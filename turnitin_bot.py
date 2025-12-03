#!/usr/bin/env python3
"""
Turnitin Maintenance Status Telegram Bot
- Monitors https://production.turnitindetect.org/maintenance-status
- Sends notifications when Turnitin becomes active (is_maintenance: false)
- Users can subscribe to notifications and check current status
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Bot Configuration
BOT_TOKEN = "8223400461:AAGYK1zeKjnQMP9lG5J-FfTfWC7tBWtY1QU"
STATUS_URL = "https://production.turnitindetect.org/maintenance-status"
CHECK_INTERVAL = 1  # Check every 1 second
SUBSCRIBERS_FILE = "subscribers.json"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Store subscribers
subscribers = set()
last_status = None


def load_subscribers():
    """Load subscribers from file."""
    global subscribers
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                subscribers = set(json.load(f))
            print(f"Loaded {len(subscribers)} subscribers")
    except Exception as e:
        print(f"Error loading subscribers: {e}")
        subscribers = set()


def save_subscribers():
    """Save subscribers to file."""
    try:
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(list(subscribers), f)
    except Exception as e:
        print(f"Error saving subscribers: {e}")


async def fetch_status():
    """Fetch current maintenance status from Turnitin."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(STATUS_URL, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error fetching status: HTTP {response.status}")
                    return None
    except Exception as e:
        print(f"Error fetching status: {e}")
        return None


async def send_message(chat_id, text, reply_markup=None):
    """Send a message via Telegram API."""
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            async with session.post(f"{TELEGRAM_API}/sendMessage", json=data) as response:
                return await response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None


async def answer_callback_query(callback_query_id, text=None):
    """Answer a callback query."""
    try:
        async with aiohttp.ClientSession() as session:
            data = {"callback_query_id": callback_query_id}
            if text:
                data["text"] = text
            async with session.post(f"{TELEGRAM_API}/answerCallbackQuery", json=data) as response:
                return await response.json()
    except Exception as e:
        print(f"Error answering callback: {e}")
        return None


async def edit_message(chat_id, message_id, text, reply_markup=None):
    """Edit an existing message."""
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            async with session.post(f"{TELEGRAM_API}/editMessageText", json=data) as response:
                return await response.json()
    except Exception as e:
        print(f"Error editing message: {e}")
        return None


def format_status_message(data):
    """Format the status data into a readable message."""
    if data is None:
        return "❌ Unable to fetch status. Please try again later."
    
    is_maintenance = data.get('is_maintenance', True)
    updated_at = data.get('updated_at', 'Unknown')
    
    # Current fetch time
    fetch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Parse and format the timestamp
    try:
        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        formatted_time = updated_at
    
    if is_maintenance:
        status_emoji = "🔴"
        status_text = "INACTIVE (Maintenance Mode)"
        
        # Include last maintenance info
        last_maintenance = data.get('last_maintenance', {})
        if last_maintenance:
            duration = last_maintenance.get('duration_minutes', 0)
            started = last_maintenance.get('started_at', 'Unknown')
            
            try:
                started_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                started_formatted = started_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                started_formatted = started
            
            maintenance_info = f"\n\n📋 *Last Maintenance:*\n• Duration: {duration:.1f} minutes\n• Started: {started_formatted}"
        else:
            maintenance_info = ""
    else:
        status_emoji = "🟢"
        status_text = "ACTIVE (No Maintenance)"
        maintenance_info = ""
    
    message = f"""{status_emoji} *Turnitin Status*

*Status:* {status_text}
*Last Updated:* {formatted_time}{maintenance_info}

🕐 *Last Refreshed:* {fetch_time}"""
    return message


def get_main_keyboard():
    """Get the main menu keyboard."""
    return {
        "inline_keyboard": [
            [{"text": "📊 Check Status", "callback_data": "check_status"}],
            [{"text": "🔔 Get Notified", "callback_data": "subscribe"}],
            [{"text": "🔕 Stop Notifications", "callback_data": "unsubscribe"}]
        ]
    }


def get_refresh_keyboard():
    """Get the refresh keyboard."""
    return {
        "inline_keyboard": [
            [{"text": "🔄 Refresh", "callback_data": "check_status"}]
        ]
    }


async def handle_start(chat_id):
    """Handle /start command."""
    welcome_message = """👋 *Welcome to Turnitin Status Bot!*

I monitor Turnitin's maintenance status and can notify you when it becomes active.

*Commands:*
• /status - Check current status
• /subscribe - Get notified when Turnitin is active
• /unsubscribe - Stop receiving notifications

Choose an option below:"""
    
    await send_message(chat_id, welcome_message, get_main_keyboard())


async def handle_status(chat_id):
    """Handle /status command."""
    await send_message(chat_id, "🔄 Checking Turnitin status...")
    
    data = await fetch_status()
    message = format_status_message(data)
    
    await send_message(chat_id, message, get_refresh_keyboard())


async def handle_subscribe(chat_id, user_id):
    """Handle /subscribe command."""
    if user_id in subscribers:
        await send_message(chat_id, "✅ You're already subscribed to notifications!")
    else:
        subscribers.add(user_id)
        save_subscribers()
        await send_message(
            chat_id,
            "🔔 *Subscribed!*\n\nYou'll receive a notification as soon as Turnitin becomes active (maintenance ends).\n\nUse /unsubscribe to stop notifications."
        )


async def handle_unsubscribe(chat_id, user_id):
    """Handle /unsubscribe command."""
    if user_id in subscribers:
        subscribers.discard(user_id)
        save_subscribers()
        await send_message(chat_id, "🔕 You've been unsubscribed from notifications.")
    else:
        await send_message(chat_id, "ℹ️ You weren't subscribed to notifications.")


async def handle_callback(callback_query):
    """Handle callback queries from inline buttons."""
    callback_id = callback_query['id']
    data = callback_query.get('data', '')
    message = callback_query.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    message_id = message.get('message_id')
    user_id = callback_query.get('from', {}).get('id')
    
    await answer_callback_query(callback_id)
    
    if data == "check_status":
        status_data = await fetch_status()
        status_message = format_status_message(status_data)
        await edit_message(chat_id, message_id, status_message, get_refresh_keyboard())
    
    elif data == "subscribe":
        if user_id in subscribers:
            await edit_message(chat_id, message_id, "✅ You're already subscribed to notifications!\n\nUse /status to check current status.")
        else:
            subscribers.add(user_id)
            save_subscribers()
            await edit_message(
                chat_id, message_id,
                "🔔 *Subscribed!*\n\nYou'll receive a notification as soon as Turnitin becomes active (maintenance ends).\n\nUse /unsubscribe to stop notifications.\nUse /status to check current status."
            )
    
    elif data == "unsubscribe":
        if user_id in subscribers:
            subscribers.discard(user_id)
            save_subscribers()
            await edit_message(chat_id, message_id, "🔕 You've been unsubscribed from notifications.\n\nUse /subscribe to subscribe again.")
        else:
            await edit_message(chat_id, message_id, "ℹ️ You weren't subscribed to notifications.\n\nUse /subscribe to subscribe.")


async def process_update(update):
    """Process a single update from Telegram."""
    if 'message' in update:
        message = update['message']
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')
        text = message.get('text', '')
        
        if text.startswith('/start'):
            await handle_start(chat_id)
        elif text.startswith('/status'):
            await handle_status(chat_id)
        elif text.startswith('/subscribe'):
            await handle_subscribe(chat_id, user_id)
        elif text.startswith('/unsubscribe'):
            await handle_unsubscribe(chat_id, user_id)
    
    elif 'callback_query' in update:
        await handle_callback(update['callback_query'])


async def get_updates(offset=None):
    """Get updates from Telegram."""
    try:
        async with aiohttp.ClientSession() as session:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            
            async with session.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=aiohttp.ClientTimeout(total=35)) as response:
                result = await response.json()
                if result.get('ok'):
                    return result.get('result', [])
                return []
    except Exception as e:
        print(f"Error getting updates: {e}")
        return []


async def monitor_status():
    """Background task to monitor status and send notifications."""
    global last_status
    
    print("🔄 Starting status monitor...")
    
    while True:
        try:
            data = await fetch_status()
            
            if data is not None:
                current_status = data.get('is_maintenance', True)
                
                # Check if status changed from maintenance (True) to active (False)
                if last_status is True and current_status is False:
                    print("🟢 Turnitin is now ACTIVE! Sending notifications...")
                    
                    notification_message = """🟢 *TURNITIN IS NOW ACTIVE!*

Maintenance has ended. Turnitin is now available for use.

Use /status to check the current status."""
                    
                    # Send notification to all subscribers
                    for user_id in list(subscribers):
                        try:
                            await send_message(user_id, notification_message)
                            print(f"✅ Notification sent to user {user_id}")
                        except Exception as e:
                            print(f"❌ Failed to send notification to {user_id}: {e}")
                
                # Log status changes
                if last_status != current_status:
                    status_text = "ACTIVE" if not current_status else "MAINTENANCE"
                    print(f"📊 Status changed: {status_text} at {datetime.now()}")
                
                last_status = current_status
            
        except Exception as e:
            print(f"Error in monitor loop: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)


async def poll_updates():
    """Poll for updates from Telegram."""
    offset = None
    print("📡 Starting to poll for updates...")
    
    while True:
        try:
            updates = await get_updates(offset)
            
            for update in updates:
                offset = update['update_id'] + 1
                await process_update(update)
        
        except Exception as e:
            print(f"Error polling updates: {e}")
            await asyncio.sleep(5)


async def main():
    """Main function to run the bot."""
    print("🤖 Starting Turnitin Status Bot...")
    
    load_subscribers()
    
    print("✅ Bot initialized!")
    print(f"📊 Checking status every {CHECK_INTERVAL} seconds")
    print(f"👥 Current subscribers: {len(subscribers)}")
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    
    # Run both tasks concurrently
    await asyncio.gather(
        monitor_status(),
        poll_updates()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")
