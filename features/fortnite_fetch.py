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

logger = logging.getLogger(__name__)

SHOP_REFRESH_HOUR_UTC = 0  # midnight UTC
SHOP_REFRESH_MINUTE_UTC = 5

# ----- HELPER FUNCTIONS -----
async def fetch_shop():
    logger.debug(f"Fetching shop from {FORTNITE_SHOP_URL}")
    async with aiohttp.ClientSession() as session:
        async with session.get(FORTNITE_SHOP_URL) as resp:
            logger.debug(f"Shop API response status: {resp.status}")
            if resp.status != 200:
                logger.warning(f"Failed to fetch Fortnite shop: HTTP {resp.status}")
                return None
            data = await resp.json()
            logger.info("Fetched Fortnite shop successfully")
            logger.debug(f"Shop data keys: {data.keys() if isinstance(data, dict) else 'not a dict'}")
            return data

def extractSkinsSetData(shop_data):
    skins = {}
    entries = shop_data.get("data", {}).get("entries", {})
    logger.debug(f"Found {len(entries)} entries in shop data")

    for idx, entry in enumerate(entries):
        logger.debug(f"Processing entry {idx}: keys={entry.keys()}")
        if "brItems" in entry:
            logger.debug(f"Entry {idx} has {len(entry['brItems'])} brItems")
            for br_item in entry["brItems"]:
                item_type = br_item.get("type", {}).get("value", "").lower()
                item_set = br_item.get("set", {}).get("value", "")
                item_name = br_item.get("name")
                logger.debug(f"BR Item: name={item_name}, type={item_type}, set={item_set}")
                # Only include skins/characters
                if item_type in ("outfit"):
                    if item_name:
                        skins[item_name] = item_set if item_set else "idk"
                        logger.debug(f"Added skin: {item_name}")
        else:
            logger.debug(f"Entry {idx} has no brItems")

    logger.info(f"Extracted {len(skins)} skins from shop data")
    logger.debug(f"Extracted skins: {list(skins.keys())}")
    return skins

def load_previous_items():
    if not os.path.exists(SHOP_STATE_FILE):
        logger.debug(f"Shop state file {SHOP_STATE_FILE} does not exist")
        return {}
    logger.debug(f"Loading shop state from {SHOP_STATE_FILE}")
    with open(SHOP_STATE_FILE, "r") as f:
        items = json.load(f)
        logger.debug(f"Loaded {len(items)} previous items")
        return items

def save_current_items(items):
    logger.debug(f"Saving {len(items)} items to {SHOP_STATE_FILE}")
    with open(SHOP_STATE_FILE, "w") as f:
        json.dump(items, f, indent=2)
    logger.debug("Shop state saved successfully")

def seconds_until_next_refresh(hour=SHOP_REFRESH_HOUR_UTC, minute=SHOP_REFRESH_MINUTE_UTC):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()

# ----- BACKGROUND TASK -----
def start_daily_shop_task(bot):
    async def shop_loop():
        try:
            await bot.wait_until_ready()
            logger.info("Fortnite shop task started")
            channel = bot.get_channel(constants.GAMER_CHANNEL)
            # ---------- First-run edge case ----------
            previous_skins = load_previous_items()
            logger.debug(f"First-run check: channel={channel}, previous_skins count={len(previous_skins)}")
            if not previous_skins:
                shop_data = await fetch_shop()
                current_skins = {}
                if shop_data:
                    current_skins = extractSkinsSetData(shop_data)
                if current_skins and channel:
                    message = "**🛒 Fortnite skins currently in the shop:**\n" + "\n".join(f"- {skin} : ({item_set})" for skin, item_set in sorted(current_skins.items()))
                    if len(message) <= 2000:
                        await channel.send(message)
                        logger.info(f"Posted {len(current_skins)} skins to Discord (first run)")
                    else:
                        logger.warning(f"Shop message too large ({len(message)} chars), not sending")
                if current_skins:
                    save_current_items(current_skins)
                    previous_skins = current_skins

            # ---------- Daily loop ----------
            while not bot.is_closed():
                delay = seconds_until_next_refresh()
                logger.info(f"Next shop check in {int(delay)} seconds")
                await asyncio.sleep(delay)

                shop_data = await fetch_shop()
                if not shop_data:
                    logger.warning("Failed to fetch shop data, skipping this cycle")
                    continue

                current_skins = extractSkinsSetData(shop_data)
                if not current_skins:
                    logger.info("No skins found in shop today")
                    continue

                # Detect new skins (keys in current that aren't in previous)
                new_skins = {skin: current_skins[skin] for skin in current_skins.keys() - previous_skins.keys()}
                logger.debug(f"Previous skins: {len(previous_skins)}, Current skins: {len(current_skins)}, New skins: {len(new_skins)}")
                if new_skins:
                    logger.debug(f"New skins detected: {new_skins}")
                    if channel:
                        message = "**🛒 Fortnite skins currently in the shop:**\n" + "\n".join(f"- {skin} ({item_set})" for skin, item_set in sorted(new_skins.items()))
                        logger.debug(f"Sending message ({len(message)} chars) to channel {constants.GAMER_CHANNEL}")
                        await channel.send(message)
                        logger.info(f"Posted {len(new_skins)} new skins to Discord")
                    else:
                        logger.warning(f"Channel {constants.GAMER_CHANNEL} not found for daily check")
                else:
                    logger.info("No new skins in the Fortnite shop today")
                    
                # Save current shop for next comparison
                save_current_items(current_skins)
                previous_skins = current_skins
        except Exception as e:
            logger.error(f"Error in shop loop: {e}")

    # Run the loop in the background
    asyncio.create_task(shop_loop())
