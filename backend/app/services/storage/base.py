from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageBackend(ABC):
    """Stores uploaded files (resumes). Swap the implementation for S3/GCS in production."""

    @abstractmethod
    def save(self, data: BinaryIO, *, suffix: str) -> str:
        """Persist `data` and return an opaque storage key."""

    @abstractmethod
    def path_for(self, key: str) -> Path:
        """Return a local path to read the file identified by `key`."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a stored file. Missing files are ignored."""
