import json
import asyncio
import aiohttp
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Load configuration
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        Logger.error(f"{Fore.RED}Config file not found. Please ensure 'config.json' exists.")
        raise
    except json.JSONDecodeError:
        Logger.error(f"{Fore.RED}Invalid JSON in config file. Please check the format.")
        raise

# Fetch data from API
async def fetch(session, url, headers=None, json_data=None):
    try:
        async with session.patch(url, headers=headers, json=json_data) as response:
            response.raise_for_status()
            return await response.json(), response.status
    except aiohttp.ClientError as e:
        Logger.error(f"{Fore.RED}HTTP request failed: {e}")
        return None, 500

# Change status and activity
async def status_change(session, statuses, token, delay):
    headers = {"Authorization": token}

    while True:
        for status in statuses:
            # Custom Status
            message = status.get("status", "")
            emoji_id = status.get("emoji_id", "")
            emoji_name = status.get("emoji_name", "")
            nitro_emoji = status.get("nitro_emoji", False)

            payload = {
                "custom_status": {
                    "text": message,
                    "emoji_id": emoji_id if nitro_emoji else None,
                    "emoji_name": emoji_name
                }
            }

            # Discord Activity
            activity = status.get("activity", {})
            if activity:
                activity_type = activity.get("type", 0)  # 0 = Playing, 1 = Streaming, 2 = Listening, 3 = Watching
                activity_name = activity.get("name", "")
                activity_url = activity.get("url", "") if activity_type == 1 else None  # URL only for streaming

                payload["activities"] = [{
                    "type": activity_type,
                    "name": activity_name,
                    "url": activity_url
                }]

            response_data, status_code = await fetch(
                session,
                "https://discord.com/api/v8/users/@me/settings",
                headers=headers,
                json_data=payload
            )

            if status_code == 200:
                Logger.info(f"{Fore.GREEN}Successfully changed status to: {Fore.CYAN}{message}")
                if activity:
                    activity_type_str = {
                        0: "Playing",
                        1: "Streaming",
                        2: "Listening",
                        3: "Watching"
                    }.get(activity_type, "Unknown")
                    Logger.info(f"{Fore.GREEN}Activity set to: {Fore.CYAN}{activity_name} {Fore.YELLOW}({activity_type_str})")
            elif status_code == 429:
                retry_after = int(response_data.get("retry_after", 5))
                Logger.warning(f"{Fore.YELLOW}Rate limited. Retrying in {Fore.CYAN}{retry_after} seconds...")
                await asyncio.sleep(retry_after)
                continue
            else:
                Logger.error(f"{Fore.RED}Failed to change status. HTTP Status: {Fore.CYAN}{status_code}")
                continue

            await asyncio.sleep(delay)

# Main setup
async def setup():
    config = load_config()
    token = config.get("token")
    statuses = config.get("statuses", [])
    delay = config.get("delay", 1)

    if not token:
        Logger.error(f"{Fore.RED}No token provided in config.")
        return

    async with aiohttp.ClientSession() as session:
        await status_change(session, statuses, token, delay)

if __name__ == "__main__":
    print(f"{Fore.BLUE}Starting Discord Status Changer...{Style.RESET_ALL}")
    asyncio.run(setup())