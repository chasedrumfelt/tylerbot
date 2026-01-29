import discord
from discord import app_commands
from pathlib import Path
import random
import os
import logging

logger = logging.getLogger("ImagePuller")

image_folder = Path(__file__).parent.parent / "images"


async def image_autocomplete(
    interaction: discord.Interaction,
    current: str,
    ) -> list[app_commands.Choice[str]]:
    """
    Autocomplete callback that returns available image files.
    """
    
    if not image_folder.exists():
        return []
    
    image_files = [f for f in os.listdir(image_folder) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    
    # Add "random" option and filter by current input
    options = ["random"] + sorted([os.path.splitext(f)[0] for f in image_files])
    
    # Filter based on what user has typed so far
    filtered = [opt for opt in options if opt.lower().startswith(current.lower())]
    
    # Return as Choice objects, limited to 25 (Discord's limit)
    return [app_commands.Choice(name=opt, value=opt) for opt in filtered[:25]]


async def pull_image(interaction: discord.Interaction, image_name: str = None):
    """
    Select or randomly pull an image from the images folder.
    
    Args:
        interaction: Discord interaction from the slash command
        image_name: Image filename (without extension) or 'random' for a random image
    """

    if not image_folder.exists():
        await interaction.response.send_message("Images folder not found.", ephemeral=True)
        logger.error(f"Images folder not found at {image_folder}")
        return

    image_files = [f for f in os.listdir(image_folder) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]

    if not image_files:
        await interaction.response.send_message("No images found in the folder.", ephemeral=True)
        logger.warning("No image files found in folder")
        return

    if image_name and image_name.lower() == "random":
        selected_image = random.choice(image_files)
    elif image_name:
        # Find the image file that matches the name (without extension)
        matching_images = [f for f in image_files if os.path.splitext(f)[0].lower() == image_name.lower()]
        if matching_images:
            selected_image = matching_images[0]
        else:
            await interaction.response.send_message(
                f"Image not found. Available images: {', '.join([os.path.splitext(f)[0] for f in image_files])}", 
                ephemeral=True
            )
            logger.warning(f"Image '{image_name}' not found")
            return
    else:
        await interaction.response.send_message(
            "Please select an image or use 'random'.", 
            ephemeral=True
        )
        return

    image_path = image_folder / selected_image
    logger.info(f"Sending image: {selected_image}")
    await interaction.response.send_message(file=discord.File(image_path))