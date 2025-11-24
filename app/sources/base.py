"""Base class for lead sources"""
from abc import ABC, abstractmethod
from typing import Iterable
from app.core.models import Lead


class SourceBase(ABC):
    """Abstract base class for lead sources"""
    
    @abstractmethod
    def search(self, niche: str, location: str | None = None) -> Iterable[Lead]:
        """
        Return basic leads with at least name + website (if available).
        Contact info can be empty; website will be crawled later.
        """
        ...

