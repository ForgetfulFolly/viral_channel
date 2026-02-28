"""
Downloads media files from URLs.
"""
import os
import aiohttp
from typing import Optional
from dotenv import load_dotenv
from utils.logging import get_logger

load_dotenv()

logger = get_logger(__name__)

class Downloader:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize the downloader by creating an aiohttp session."""
        self.session = aiohttp.ClientSession()
        logger.info("Downloader initialized.")

    async def shutdown(self) -> None:
        """Shutdown the downloader by closing the aiohttp session."""
        if self.session:
            await self.session.close()
            logger.info("Downloader shut down.")

    async def download_media(self, url: str, destination_path: str) -> bool:
        """
        Download media from a given URL to a specified path.

        Args:
            url (str): The URL of the media file to download.
            destination_path (str): The local path where the file should be saved.

        Returns:
            bool: True if the download was successful, False otherwise.
        """
        try:
            if not self.session:
                logger.error("Downloader session is not initialized.")
                return False

            async with self.session.get(url) as response:
                if response.status == 200:
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    with open(destination_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    logger.info(f"Media downloaded successfully to {destination_path}.")
                    return True
                else:
                    logger.error(f"Failed to download media. Status code: {response.status}")
                    return False

        except Exception as e:
            logger.exception(f"An error occurred while downloading media from {url}: {e}")
            return False