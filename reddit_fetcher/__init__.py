"""reddit-fetcher: personal Reddit data fetcher for research and organization."""

from .fetcher import Fetcher
from .storage import Storage

__all__ = ["Fetcher", "Storage"]
__version__ = "1.0.0"
