"""Dashboard segments performance schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import List


class SegmentPerformance(BaseModel):
    """Performance metrics for a segment"""
    segment_id: int
    segment_name: str
    
    leads_sent: int
    opened: int
    replied: int
    bounced: int
    
    open_rate: float
    reply_rate: float
    bounce_rate: float
    
    class Config:
        from_attributes = True


class TopSegmentsResponse(BaseModel):
    """Response for top performing segments"""
    time_range_from: datetime
    time_range_to: datetime
    metric: str  # "reply_rate" | "open_rate"
    segments: List[SegmentPerformance]

