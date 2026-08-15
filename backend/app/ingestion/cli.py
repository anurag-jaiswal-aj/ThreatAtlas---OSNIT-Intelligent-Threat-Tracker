import asyncio
import logging
import sys
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import close_mongo_connection, connect_to_mongo, init_db, get_database
from app.ingestion.service import IngestionService

logger = logging.getLogger("threat_atlas.ingestion.cli")


async def run_manual_ingestion():
    """Manual CLI entry point for triggering RSS ingestion."""
    setup_logging()
    logger.info("Initializing database connection for manual RSS ingestion...")
    await connect_to_mongo()
    await init_db()

    try:
        db = get_database()
        service = IngestionService(db)
        logger.info("Starting manual RSS ingestion run...")
        stats = await service.ingest_all_feeds()
        logger.info("=" * 60)
        logger.info("MANUAL INGESTION SUMMARY:")
        logger.info("Feeds Attempted:  %d", stats.feeds_attempted)
        logger.info("Feeds Succeeded:  %d", stats.feeds_succeeded)
        logger.info("Feeds Failed:     %d", stats.feeds_failed)
        logger.info("Entries Processed:%d", stats.entries_processed)
        logger.info("Entries Inserted: %d", stats.entries_inserted)
        logger.info("Duplicates Skipped:%d", stats.duplicates_skipped)
        logger.info("Entries Failed:   %d", stats.entries_failed)
        logger.info("=" * 60)
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(run_manual_ingestion())
