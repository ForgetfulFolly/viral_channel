from pydantic import BaseModel
from datetime import datetime

class RawContent(BaseModel):
    """Raw discovered content from sources."""
    source: str
    url: str
    title: str
    timestamp: datetime

class ProcessedContent(BaseModel):
    """Content after analysis and processing."""
    id: str
    clips: list[str]
    script: str
    status: str