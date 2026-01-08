from discord.ext import tasks
from datetime import datetime
import random

birthdays {
    227510432364101632: {
        "date": (7, 5),
        "video": "https://www.youtube.com/watch?v=e1-a9sVOTis&pp=ygUUaGFwcHkgYmlydGhkYXkgY2hhc2U%3D"
    }
}


@tasks.loop(hours=24)
async def check_birthdays():
    today = datetime.now(tz=UTC)
    for user_id, info in birthdays.items():
        if info["date"] == today