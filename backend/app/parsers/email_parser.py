import email
import email.policy
from email.header import decode_header, make_header

from app.models import ArtifactType
from app.parsers.base import BaseParser, ParseResult

EMAIL_MIME_TYPES = {
    "message/rfc822",
    "application/octet-stream",  # .eml files often detected as this
}
EMAIL_EXTENSIONS = {".eml", ".msg"}


class EmailParser(BaseParser):
    def can_handle(self, mime_type: str) -> bool:
        return mime_type in EMAIL_MIME_TYPES

    async def parse(self, file_path: str, mime_type: str) -> ParseResult:
        warnings: list[str] = []

        with open(file_path, "rb") as f:
            raw = f.read()

        msg = email.message_from_bytes(raw, policy=email.policy.default)

        def decode_field(value: str | None) -> str:
            if value is None:
                return ""
            try:
                return str(make_header(decode_header(value)))
            except Exception:
                return str(value)

        headers = {
            "From": decode_field(msg.get("From")),
            "To": decode_field(msg.get("To")),
            "Subject": decode_field(msg.get("Subject")),
            "Date": decode_field(msg.get("Date")),
            "Message-ID": decode_field(msg.get("Message-ID")),
            "Cc": decode_field(msg.get("Cc")),
        }

        body_parts: list[str] = []
        attachments: list[str] = []

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition") or "")
            content_type = part.get_content_type()

            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    attachments.append(decode_field(filename))
                continue

            if content_type in ("text/plain", "text/html"):
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body_parts.append(payload.decode(charset, errors="replace"))
                except Exception as exc:
                    warnings.append(f"Failed to decode body part: {exc}")

        header_text = "\n".join(f"{k}: {v}" for k, v in headers.items() if v)
        body_text = "\n\n".join(body_parts)
        if attachments:
            body_text += f"\n\n[Attachments: {', '.join(attachments)}]"

        full_text = f"{header_text}\n\n{body_text}".strip()

        return ParseResult(
            text=full_text or None,
            metadata={
                "headers": headers,
                "attachment_count": len(attachments),
                "attachments": attachments,
            },
            warnings=warnings,
            artifact_type=ArtifactType.EMAIL_BODY.value,
        )
