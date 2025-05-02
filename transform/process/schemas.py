from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pytz import timezone

class News(BaseModel):
    link: Optional[str] = None
    content: Optional[str] = None
    published: Optional[datetime] = Field(default_factory=lambda: datetime.now(tz=timezone('Asia/Ho_Chi_Minh')))
    sentiment: Optional[str] = None
    sentiment_score: Optional[int] = 0
    summary: Optional[str] = None
    title: Optional[str] = None
    topic: Optional[str] = None
