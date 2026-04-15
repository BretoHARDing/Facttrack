from app.models import ArtifactType
from app.parsers.base import BaseParser, ParseResult

TEXT_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/x-log",
    "text/x-python",
    "text/x-java-source",
    "text/x-c",
    "text/html",
    "text/xml",
    "application/json",
    "application/xml",
}


class TextParser(BaseParser):
    def can_handle(self, mime_type: str) -> bool:
        return mime_type in TEXT_MIME_TYPES or mime_type.startswith("text/")

    async def parse(self, file_path: str, mime_type: str) -> ParseResult:
        warnings: list[str] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as exc:
            warnings.append(f"Failed to read file as UTF-8: {exc}")
            content = None

        return ParseResult(
            text=content,
            metadata={"char_count": len(content) if content else 0},
            warnings=warnings,
            artifact_type=ArtifactType.EXTRACTED_TEXT.value,
        )
