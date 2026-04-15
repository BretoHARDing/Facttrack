from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParseResult:
    text: Optional[str]
    metadata: dict
    warnings: list[str]
    artifact_type: str  # from ArtifactType enum value


class BaseParser:
    def can_handle(self, mime_type: str) -> bool:
        raise NotImplementedError

    async def parse(self, file_path: str, mime_type: str) -> ParseResult:
        raise NotImplementedError
