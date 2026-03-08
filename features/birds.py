import discord
import requests
import constants
from discord.ext import commands

# constants
BIRD_API_BASE = "https://api.ebird.org/v2/data/obs"

# region codes
REGION_CODES = {
    "Savannah": "US-GA-051",
    "Jacksonville": "US-FL-019"
}

headers = {
    'X-eBirdApiToken': constants.EBIRD_API_KEY
}

async def get_notable_birds(interaction: discord.Interaction, region: str):
    """
    Fetch recent notable bird observations from eBird API for a given region.
    
    Args:
        interaction: Discord interaction object
        region: Region code (e.g., "US", "CA-ON" for Ontario). Defaults to "US"
    """
    await interaction.response.defer()
    
    try:
        regionCode = REGION_CODES.get(region, region)
        # eBird API endpoint for recent notable observations
        endpoint = f"{BIRD_API_BASE}/{regionCode}/recent/notable"
        
        params = {
            "maxResults": 5,
            "detail": "full"
        }
        
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            await interaction.followup.send("No notable bird observations found for that region.")
            return
        
        # Build embed with bird observations
        embed = discord.Embed(
            title=f"Notable Bird Observations - {region}",
            color=discord.Color.green(),
            description="Recent notable sightings from eBird"
        )
        
        for idx, bird in enumerate(data[:10], 1):
            species = bird.get('comName', 'Unknown Species')
            sci_name = bird.get('sciName', '')
            location = bird.get('locName', 'Unknown Location')
            date = bird.get('obsDt', 'Unknown Date')
            count = bird.get('howMany', 1)
            
            # Build value string with available information
            value_parts = [f"*{sci_name}*" if sci_name else ""]
            value_parts.append(f"📍 {location}")
            
            value = "\n".join(filter(None, value_parts))
            
            embed.add_field(
                name=f"{idx}. {species}",
                value=value,
                inline=False
            )
        
        embed.set_footer(text="Data from eBird")
        
        await interaction.followup.send(embed=embed)
        
    except requests.exceptions.Timeout:
        await interaction.followup.send("Request to eBird API timed out. Please try again later.")
    except requests.exceptions.HTTPError as e:
        await interaction.followup.send(f"Error fetching bird data: {e.response.status_code}")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")
