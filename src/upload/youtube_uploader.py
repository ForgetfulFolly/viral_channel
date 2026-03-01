import asyncio
import os
from typing import Dict
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

# Configure logging
logger = logging.getLogger(__name__)

class YouTubeUploader:
    """Handles OAuth-based YouTube uploads and video management."""

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    def __init__(self, config: Dict):
        """
        Initialize the YouTubeUploader with configuration.

        Args:
            config (Dict): Configuration dictionary containing necessary settings.
        """
        self.config = config

    async def upload_video(
        self,
        file_path: str,
        metadata: Dict,
        credentials_file: str
    ) -> str:
        """
        Upload a video file with specified metadata using resumable upload.

        Args:
            file_path (str): Path to the video file.
            metadata (Dict): Metadata for the video.
            credentials_file (str): Path to the OAuth credentials JSON file.

        Returns:
            str: YouTube video ID of the uploaded video.
        """
        try:
            youtube = await self._get_authenticated_service(credentials_file)
            request_body = {
                'snippet': {
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'tags': metadata.get('tags', []),
                    'categoryId': metadata.get('category_id', '')
                },
                'status': {
                    'privacyStatus': metadata.get('privacy_status', 'private')
                }
            }

            media_file = MediaFileUpload(
                file_path,
                chunksize=-1,  # Use default chunk size
                resumable=True
            )

            request = youtube.videos().insert(
                part='snippet,status',
                body=request_body,
                media_body=media_file
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if 'id' in response:
                    logger.info(f"Video uploaded successfully. Video ID: {response['id']}")
                    return response['id']
        except Exception as e:
            logger.error(f"Error uploading video: {e}", exc_info=True)
            raise

    async def set_thumbnail(
        self,
        video_id: str,
        thumbnail_path: str,
        credentials_file: str
    ) -> bool:
        """
        Set the thumbnail for an uploaded video.

        Args:
            video_id (str): YouTube video ID.
            thumbnail_path (str): Path to the thumbnail image file.
            credentials_file (str): Path to the OAuth credentials JSON file.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            youtube = await self._get_authenticated_service(credentials_file)
            media_file = MediaFileUpload(thumbnail_path)

            request = youtube.thumbnails().set(
                videoId=video_id,
                media_body=media_file
            )

            response = request.execute()
            logger.info(f"Thumbnail set successfully for video ID: {video_id}")
            return True if 'etag' in response else False
        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}", exc_info=True)
            return False

    async def update_video_status(
        self,
        video_id: str,
        privacy_status: str,
        credentials_file: str
    ) -> bool:
        """
        Update the privacy status of a video.

        Args:
            video_id (str): YouTube video ID.
            privacy_status (str): New privacy status ('public', 'private', 'unlisted').
            credentials_file (str): Path to the OAuth credentials JSON file.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            youtube = await self._get_authenticated_service(credentials_file)
            request_body = {
                'id': video_id,
                'status': {
                    'privacyStatus': privacy_status
                }
            }

            request = youtube.videos().update(
                part='status',
                body=request_body
            )

            response = request.execute()
            logger.info(f"Video status updated successfully for video ID: {video_id}")
            return True if 'etag' in response else False
        except Exception as e:
            logger.error(f"Error updating video status: {e}", exc_info=True)
            return False

    async def _get_authenticated_service(self, credentials_file: str):
        """
        Get an authenticated YouTube service object.

        Args:
            credentials_file (str): Path to the OAuth credentials JSON file.

        Returns:
            googleapiclient.discovery.Resource: Authenticated YouTube service.
        """
        creds = None
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                creds = json.load(f)

        if not creds or not creds.get('token'):
            logger.error("No valid credentials found.")
            raise ValueError("No valid credentials found.")

        credentials = self._load_credentials(creds)
        if credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
        else:
            logger.error("Invalid or expired credentials.")
            raise ValueError("Invalid or expired credentials.")

        return build('youtube', 'v3', credentials=credentials)

    def _load_credentials(self, creds: Dict):
        """
        Load OAuth2 credentials from a dictionary.

        Args:
            creds (Dict): Dictionary containing OAuth2 credentials.

        Returns:
            google.oauth2.credentials.Credentials: Loaded credentials object.
        """
        from google.oauth2.credentials import Credentials

        return Credentials(
            token=creds['token'],
            refresh_token=creds.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            scopes=self.SCOPES
        )