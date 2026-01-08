import re
import random
import asyncio
import os
import discord
from discord.ext import commands

import random
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # INFO level will show messages in console
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("dice_roller")

async def roll(ctx, dice_input: str):
    logger.info(f"Original input: '{dice_input}'")

    # Remove spaces
    dice_input_clean = dice_input.replace(" ", "")
    logger.info(f"Input without spaces: '{dice_input_clean}'")

    # Split input by '+'
    expressions = dice_input_clean.split("+")
    logger.info(f"Split expressions: {expressions}")

    if not expressions:
        await ctx.send("No dice to roll.")
        logger.warning("No expressions found after splitting.")
        return

    all_rolls = []
    total = 0

    dice_pattern = re.compile(r"^(\d+)d(\d+)$", re.IGNORECASE)

    for expr in expressions:
        logger.info(f"Processing expression: '{expr}'")
        match = dice_pattern.fullmatch(expr)
        if not match:
            await ctx.send(f"Invalid dice expression: `{expr}`. Use NdM format, e.g., 2d6.")
            logger.error(f"Expression failed regex match: '{expr}'")
            return

        count, sides = map(int, match.groups())
        logger.info(f"Parsed count={count}, sides={sides}")

        # Safety limits
        if count < 1 or sides < 2:
            await ctx.send(f"Dice count must be ≥1 and sides ≥2 in `{expr}`.")
            logger.warning(f"Expression out of bounds: '{expr}'")
            return
        if count > 100 or sides > 1000:
            await ctx.send(f"Limits: max 100 dice, max 1000 sides in `{expr}`.")
            logger.warning(f"Expression exceeds limits: '{expr}'")
            return

        rolls = [random.randint(1, sides) for _ in range(count)]
        logger.info(f"Rolled dice for '{expr}': {rolls}")

        all_rolls.append((expr, rolls))
        total += sum(rolls)

    # Build response
    response_lines = [
        f"🎲 {expr}: {', '.join(map(str, rolls))} → {sum(rolls)}"
        for expr, rolls in all_rolls
    ]
    response_lines.append(f"**Total: {total}**")

    logger.info(f"Final total: {total}")
    logger.info(f"Response lines: {response_lines}")

    await ctx.send("\n".join(response_lines))
