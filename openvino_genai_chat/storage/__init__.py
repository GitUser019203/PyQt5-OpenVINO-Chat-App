"""Abstract storage layer for conversation persistence."""
from .json_backend import JSONStorage

__all__ = ["JSONStorage"]
