import os
import json
import logging
from typing import Optional
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from src.config import ChannelConfig
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def setup_logging(correlation_id: str):
    """Set up structured logging with a correlation ID."""
    logger = logging.getLogger()
    for handler in logger.handlers:
        formatter = logging.Formatter(f'%(asctime)s - {correlation_id} - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

async def run_oauth_flow(output_file: str, client_secrets_file: Optional[str] = None) -> None:
    """Run the OAuth consent flow and save credentials to a file.

    Args:
        output_file (str): Path to the file where credentials will be saved.
        client_secrets_file (Optional[str]): Path to the client secrets JSON file. Defaults to environment variable YOUTUBE_CLIENT_SECRETS_FILE.
    """
    if not client_secrets_file:
        client_secrets_file = os.getenv('YOUTUBE_CLIENT_SECRETS_FILE')
        if not client_secrets_file:
            raise ValueError("Client secrets file path must be provided or set in the environment variable YOUTUBE_CLIENT_SECRETS_FILE.")

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
    creds = await asyncio.to_thread(flow.run_local_server, port=0)

    with open(output_file, 'w') as f:
        json.dump(creds.to_json(), f)

    logger.info(f"Credentials saved to {output_file}")

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description='Run YouTube OAuth consent flow and save credentials.')
    parser.add_argument('--output', required=True, help='Path to the output JSON file for saving credentials')
    parser.add_argument('--client-secrets-file', help='Path to the client secrets JSON file (optional if set in environment)')

    args = parser.parse_args()

    correlation_id = os.getenv('CORRELATION_ID', 'no_correlation_id_set')
    setup_logging(correlation_id)

    try:
        asyncio.run(run_oauth_flow(args.output, args.client_secrets_file))
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == '__main__':
    main()