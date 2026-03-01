import logging
import yt_dlp

logger = logging.getLogger(__name__)

async def search_youtube_video(query: str) -> str | None:
    """
    Search for a YouTube video based on the provided query.
    Returns the URL of the first result, or None if no results found.
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'max_downloads': 1,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Searching YouTube for: {query}")
            info = ydl.extract_info(query, download=False)
            
            # Extract the first result
            if 'entries' in info and len(info['entries']) > 0:
                video_url = info['entries'][0]['webpage_url']
                video_title = info['entries'][0].get('title', 'Unknown')
                logger.info(f"Found video: {video_title} ({video_url})")
                return video_url
            else:
                logger.warning(f"No videos found for query: {query}")
                return None
                
    except Exception as e:
        logger.error(f"Error searching YouTube: {str(e)}")
        return None
