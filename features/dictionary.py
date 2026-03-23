import logging
import aiohttp

logger = logging.getLogger(__name__)

async def get_definition(word: str) -> str:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        logger.info(f"Fetching definition for '{word}'...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        entry = data[0]
                        word = entry.get("word", "Unknown")
                        meanings = entry.get("meanings", [])
                        if meanings:
                            result = f"**{word}**\n"
                            for meaning in meanings:
                                part_of_speech = meaning.get("partOfSpeech", "Unknown")
                                definitions = meaning.get("definitions", [])
                                result += f"\n*{part_of_speech}*:\n"
                                if definitions:
                                    for i, definition_obj in enumerate(definitions, 1):
                                        definition_text = definition_obj.get("definition", "No definition found.")
                                        result += f"{i}. {definition_text}\n"
                                else:
                                    result += "  No definitions found.\n"
                            logger.info(f"Definition for '{word}' fetched successfully.")
                            return result.strip()
                    return "No definition found."
                else:
                    raise Exception
    except Exception as e:
        logger.error(f"Error fetching definition for '{word}': {e}")
        return "Are you sure about that?"