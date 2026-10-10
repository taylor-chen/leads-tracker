from dataclasses import dataclass
from pathlib import PurePath
from typing import BinaryIO

from app.core.errors import PayloadTooLargeError, ValidationError


@dataclass(frozen=True)
class ResumeFormat:
    content_type: str
    magic: tuple[bytes, ...]


# Extension -> canonical content type and file signatures. We trust neither the
# client-supplied content type nor the extension alone; the bytes must match too.
ALLOWED_RESUME_FORMATS: dict[str, ResumeFormat] = {
    ".pdf": ResumeFormat("application/pdf", (b"%PDF-",)),
    ".doc": ResumeFormat("application/msword", (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)),
    ".docx": ResumeFormat(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        (b"PK\x03\x04",),
    ),
}


@dataclass(frozen=True)
class ValidatedResume:
    filename: str
    suffix: str
    content_type: str
    size_bytes: int


def validate_resume(file: BinaryIO, filename: str | None, *, max_bytes: int) -> ValidatedResume:
    """Check the resume's extension, signature and size. Leaves `file` rewound to the start."""
    safe_name = PurePath(filename or "").name.strip()
    suffix = PurePath(safe_name).suffix.lower()
    fmt = ALLOWED_RESUME_FORMATS.get(suffix)
    if not safe_name or fmt is None:
        allowed = ", ".join(sorted(ALLOWED_RESUME_FORMATS))
        raise ValidationError(f"Resume must be one of: {allowed}")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size == 0:
        raise ValidationError("Resume file is empty")
    if size > max_bytes:
        raise PayloadTooLargeError(f"Resume must be at most {max_bytes // (1024 * 1024)} MB")

    header = file.read(8)
    file.seek(0)
    if not any(header.startswith(sig) for sig in fmt.magic):
        raise ValidationError("Resume content does not match its file type")

    return ValidatedResume(
        filename=safe_name[:255],
        suffix=suffix,
        content_type=fmt.content_type,
        size_bytes=size,
    )
