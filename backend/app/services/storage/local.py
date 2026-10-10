import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from app.services.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, data: BinaryIO, *, suffix: str) -> str:
        # Keys are generated server-side, never derived from user-supplied filenames.
        key = f"resumes/{datetime.now(UTC):%Y/%m}/{uuid.uuid4().hex}{suffix}"
        target = self.path_for(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as out:
            shutil.copyfileobj(data, out)
        return key

    def path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Invalid storage key")
        return path

    def delete(self, key: str) -> None:
        self.path_for(key).unlink(missing_ok=True)
