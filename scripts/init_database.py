import argparse
import logging
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [correlation_id=%(correlation_id)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main(db_path: str) -> None:
    """
    Initialize the database schema.

    Args:
        db_path (str): Path to the SQLite database file.
    """
    try:
        logger.info("Initializing database schema...", extra={"correlation_id": "init_db"})
        engine = init_db(db_path)
        logger.info(
            "Database initialized successfully at %s", db_path, extra={"correlation_id": "init_db"}
        )
    except SQLAlchemyError as e:
        logger.error(
            "Failed to initialize database: %s", str(e), extra={"correlation_id": "init_db"}
        )
        raise
    except Exception as e:
        logger.error(
            "An unexpected error occurred: %s", str(e), extra={"correlation_id": "init_db"}
        )
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the database schema.")
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/viral_channel.db",
        help="Path to the SQLite database file (default: data/viral_channel.db)",
    )
    args = parser.parse_args()

    # Ensure the directory for the database exists
    db_dir = os.path.dirname(args.db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    main(args.db_path)