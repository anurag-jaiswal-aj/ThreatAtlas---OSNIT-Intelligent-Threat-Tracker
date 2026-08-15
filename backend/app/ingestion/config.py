from typing import List
from pydantic import BaseModel, HttpUrl, Field


class RSSFeedConfig(BaseModel):
    """Configuration for a single public RSS feed source."""

    name: str = Field(..., description="Human-readable name of the feed source")
    url: str = Field(..., description="HTTP/HTTPS URL of the RSS XML feed")
    enabled: bool = Field(default=True, description="Whether to include feed in ingestion runs")


# Default legitimate public RSS sources for defensive threat monitoring
DEFAULT_RSS_FEEDS: List[RSSFeedConfig] = [
    RSSFeedConfig(
        name="BBC World News",
        url="http://feeds.bbci.co.uk/news/world/rss.xml",
    ),
    RSSFeedConfig(
        name="Al Jazeera English",
        url="https://www.aljazeera.com/xml/rss/all.xml",
    ),
    RSSFeedConfig(
        name="UN News",
        url="https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    ),
]
