import aiohttp
import datetime
import asyncio
import json
import os
import logging
import constants
from discord.ext import tasks

# ----- CONFIG -----
FORTNITE_SHOP_URL = "https://fortnite-api.com/v2/shop"
SHOP_STATE_FILE = "last_shop.json"

logger = logging.getLogger("FortniteShop")

SHOP_REFRESH_HOUR_UTC = 0  # midnight UTC
SHOP_REFRESH_MINUTE_UTC = 0

# ----- HELPER FUNCTIONS -----
async def fetch_shop():
    async with aiohttp.ClientSession() as session:
        async with session.get(FORTNITE_SHOP_URL) as resp:
            if resp.status != 200:
                logger.warning(f"Failed to fetch Fortnite shop: HTTP {resp.status}")
                return None
            data = await resp.json()
            logger.info("Fetched Fortnite shop successfully")
            return data

def extract_skin_names(shop_data):
    skins = {}
    entries = shop_data.get("data", {}).get("entries", {})

    for entry in entries:
        if "brItems" in entry:
            for br_item in entry["brItems"]:
                item_type = br_item.get("type", {}).get("value", "").lower()
                item_set = br_item.get("set", {}).get("text", "").lower()
                # Only include skins/characters
                if item_type in ("outfit"):
                    name = br_item.get("name")
                    if name:
                        skins[name] = item_set

    logger.info(f"Extracted {len(skins)} skins from shop data")
    return skins

def load_previous_items():
    if not os.path.exists(SHOP_STATE_FILE):
        return {}
    with open(SHOP_STATE_FILE, "r") as f:
        return json.load(f)

def save_current_items(items):
    with open(SHOP_STATE_FILE, "w") as f:
        json.dump(items, f, indent=2)

def seconds_until_next_refresh(hour=SHOP_REFRESH_HOUR_UTC, minute=SHOP_REFRESH_MINUTE_UTC):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()

# ----- BACKGROUND TASK -----
def start_daily_shop_task(bot):
    async def shop_loop():
        await bot.wait_until_ready()
        logger.info("Fortnite shop task started")

        # ---------- First-run edge case ----------
        previous_skins = load_previous_items()
        channel = bot.get_channel(constants.GAMER_CHANNEL)
        if not previous_skins:
            shop_data = await fetch_shop()
            if shop_data:
                current_skins = extract_skin_names(shop_data)
            if current_skins:
                await channel.send(
                "**🛒 Fortnite skins currently in the shop:**\n" +
                "\n".join(f"- {skin} : ({item_set})" for skin, item_set in sorted(current_skins.items()))
                )
                logger.info(f"Posted {len(current_skins)} skins to Discord (first run)")
            save_current_items(current_skins)
            previous_skins = current_skins

        # ---------- Daily loop ----------
        while not bot.is_closed():
            delay = seconds_until_next_refresh()
            logger.info(f"[FortniteShop] Next shop check in {int(delay)} seconds")
            await asyncio.sleep(delay)

            shop_data = await fetch_shop()
            if not shop_data:
                continue

            current_skins = extract_skin_names(shop_data)
            if not current_skins:
                logger.info("No skins found in shop today")
                continue

            # Detect new skins (keys in current that aren't in previous)
            new_skins = set(current_skins.keys()) - set(previous_skins.keys())
            if new_skins:
                channel = bot.get_channel(constants.GAMER_CHANNEL)
                if channel:
                    await channel.send(
                    "**🛒 Fortnite skins currently in the shop:**\n" +
                    "\n".join(f"- {skin} : ({item_set})" for skin, item_set in sorted(current_skins.items()))
                    )
                    logger.info(f"Posted {len(new_skins)} new skins to Discord")
                else:
                    logger.warning(f"Channel {constants.GAMER_CHANNEL} not found for daily check")
            else:
                logger.info("No new skins in the Fortnite shop today")
                
            # Save current shop for next comparison
            save_current_items(current_skins)
            previous_skins = current_skins

    # Run the loop in the background
    asyncio.create_task(shop_loop())
