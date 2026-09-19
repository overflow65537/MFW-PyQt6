"""Image preparation helpers shared by external notification channels."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
from io import BytesIO


DEFAULT_MAX_IMAGE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ImagePayload:
    data: bytes
    mime_type: str
    base64_data: str
    md5: str
    data_uri: str

    @property
    def filename(self) -> str:
        extension = "jpg" if self.mime_type == "image/jpeg" else "png"
        return f"screenshot.{extension}"


def _detect_mime_type(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return "image/png"


def compress_for_notice(
    image_bytes: bytes,
    *,
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
) -> bytes:
    """Shrink oversized screenshots to JPEG while retaining useful resolution."""

    if not image_bytes or len(image_bytes) <= max_bytes:
        return image_bytes

    try:
        from PIL import Image

        with Image.open(BytesIO(image_bytes)) as source:
            image = source.convert("RGB")
            best = image_bytes
            quality = 85

            for _ in range(12):
                buffer = BytesIO()
                image.save(
                    buffer,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                )
                candidate = buffer.getvalue()
                if len(candidate) < len(best):
                    best = candidate
                if len(candidate) <= max_bytes:
                    return candidate

                if quality > 55:
                    quality -= 10
                else:
                    width = max(320, int(image.width * 0.8))
                    height = max(180, int(image.height * 0.8))
                    if (width, height) == image.size:
                        break
                    image = image.resize((width, height), Image.Resampling.LANCZOS)

            return best
    except Exception:
        return image_bytes


def encode_image_payload(
    image_bytes: bytes,
    *,
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
) -> ImagePayload:
    """Compress and encode screenshot bytes for JSON, HTML, and QYWX payloads."""

    prepared = compress_for_notice(image_bytes, max_bytes=max_bytes)
    mime_type = _detect_mime_type(prepared)
    encoded = base64.b64encode(prepared).decode("ascii")
    return ImagePayload(
        data=prepared,
        mime_type=mime_type,
        base64_data=encoded,
        md5=hashlib.md5(prepared).hexdigest(),
        data_uri=f"data:{mime_type};base64,{encoded}",
    )


__all__ = [
    "DEFAULT_MAX_IMAGE_BYTES",
    "ImagePayload",
    "compress_for_notice",
    "encode_image_payload",
]
