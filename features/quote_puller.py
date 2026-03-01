import discord
import random
import logging

logger = logging.getLogger(__name__)


async def get_random_quote(interaction, channel_id: int):
    """
    Pulls a random message from a random thread in a specific channel.
    
    Args:
        interaction: Discord interaction from the slash command
        channel_id: The ID of the channel to search for threads
    """
    try:
        # Fetch the channel
        channel = interaction.client.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message(f"Could not find channel with ID {channel_id}")
            logger.error(f"Channel with ID {channel_id} not found")
            return
        
        # Get all archived and active threads
        threads = []
        
        # Fetch archived threads
        async for thread in channel.archived_threads(limit=None):
            threads.append(thread)
        
        # Also check for active threads
        if hasattr(channel, 'threads'):
            threads.extend(channel.threads)
        
        if not threads:
            await interaction.response.send_message("No threads found in that channel.")
            logger.warning(f"No threads found in channel {channel_id}")
            return
        
        # Select a random thread
        random_thread = random.choice(threads)
        logger.info(f"Selected thread: {random_thread.name}")
        
        # Get all messages from the thread
        messages = []
        async for message in random_thread.history(limit=None):
            # Exclude bot messages and empty content
            if not message.author.bot and message.content.strip():
                messages.append(message)
        
        if not messages:
            await interaction.response.send_message(f"No user messages found in thread '{random_thread.name}'.")
            logger.warning(f"No messages found in thread {random_thread.name}")
            return
        
        # Select a random message
        random_message = random.choice(messages)
        
        # Format the response
        author_name = random_message.author.display_name
        quote_text = random_message.content
        thread_name = random_thread.name
        
        embed = discord.Embed(
            title=f"Quote from {thread_name}",
            description=quote_text,
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"Sent quote from {author_name} in thread {thread_name}")
        logger.info(f"Message ID: {random_message.id}")
        
    except Exception as e:
        logger.error(f"Error in get_random_quote: {str(e)}")
        await interaction.response.send_message("An error occurred while fetching a quote.")
