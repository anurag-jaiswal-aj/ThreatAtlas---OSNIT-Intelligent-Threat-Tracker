import logging
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from app.db.repositories.raw_post import RawPostRepository
from app.ingestion.config import DEFAULT_RSS_FEEDS, RSSFeedConfig
from app.ingestion.rss_collector import RSSCollector

logger = logging.getLogger("threat_atlas.ingestion.service")


class IngestionStatistics(BaseModel):
    """Statistics summary returned after executing an ingestion run."""

    feeds_attempted: int = Field(default=0, description="Total feeds attempted")
    feeds_succeeded: int = Field(default=0, description="Feeds successfully fetched and parsed")
    feeds_failed: int = Field(default=0, description="Feeds that failed due to network or parse errors")
    entries_processed: int = Field(default=0, description="Total individual entries processed across all feeds")
    entries_inserted: int = Field(default=0, description="New RawPost documents inserted into MongoDB")
    duplicates_skipped: int = Field(default=0, description="Duplicate items skipped due to unique constraint")
    entries_failed: int = Field(default=0, description="Entries that failed validation or parsing")


class IngestionService:
    """Orchestration service for running OSINT ingestion tasks."""

    def __init__(self, db: AsyncIOMotorDatabase, collector: Optional[RSSCollector] = None):
        self.db = db
        self.repository = RawPostRepository(db)
        self.collector = collector or RSSCollector()

    async def ingest_feed(self, feed_config: RSSFeedConfig) -> tuple[bool, int, int, int, int]:
        """Ingest a single RSS feed source. Returns (success_flag, processed, inserted, duplicates, failed)."""
        logger.info("Starting ingestion for RSS feed '%s' (%s)...", feed_config.name, feed_config.url)
        feed_meta, entries = await self.collector.fetch_feed_entries(feed_config.url)

        if not entries and not feed_meta:
            logger.error("Feed '%s' returned no data or failed to fetch.", feed_config.name)
            return False, 0, 0, 0, 0

        processed = len(entries)
        inserted = 0
        duplicates = 0
        failed = 0

        for entry in entries:
            post_create = self.collector.normalize_entry(entry, feed_config.name, feed_meta)
            if not post_create:
                failed += 1
                continue

            created_post = await self.repository.create(post_create)
            if created_post:
                inserted += 1
            else:
                duplicates += 1

        logger.info(
            "Completed feed '%s': %d processed, %d inserted, %d duplicates, %d failed.",
            feed_config.name,
            processed,
            inserted,
            duplicates,
            failed,
        )
        return True, processed, inserted, duplicates, failed

    async def ingest_all_feeds(self, feeds: Optional[List[RSSFeedConfig]] = None) -> IngestionStatistics:
        """Ingest all configured RSS feeds resiliently."""
        target_feeds = feeds if feeds is not None else DEFAULT_RSS_FEEDS
        stats = IngestionStatistics()

        for feed in target_feeds:
            if not feed.enabled:
                logger.info("Skipping disabled feed '%s'.", feed.name)
                continue

            stats.feeds_attempted += 1
            success, processed, inserted, duplicates, failed = await self.ingest_feed(feed)

            if success:
                stats.feeds_succeeded += 1
            else:
                stats.feeds_failed += 1

            stats.entries_processed += processed
            stats.entries_inserted += inserted
            stats.duplicates_skipped += duplicates
            stats.entries_failed += failed

        logger.info("Ingestion run finished. Summary: %s", stats.model_dump_json())
        return stats
