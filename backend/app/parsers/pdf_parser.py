import io
from typing import Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.models import ArtifactType
from app.parsers.base import BaseParser, ParseResult

PDF_MIME_TYPES = {"application/pdf"}
OCR_CHARS_PER_PAGE_THRESHOLD = 50


class PDFParser(BaseParser):
    def can_handle(self, mime_type: str) -> bool:
        return mime_type in PDF_MIME_TYPES

    async def parse(self, file_path: str, mime_type: str) -> ParseResult:
        warnings: list[str] = []
        doc = fitz.open(file_path)
        page_count = len(doc)

        pages_text: list[str] = []
        for page in doc:
            pages_text.append(page.get_text())

        total_chars = sum(len(t) for t in pages_text)
        ocr_used = False

        if page_count > 0 and (total_chars / page_count) < OCR_CHARS_PER_PAGE_THRESHOLD:
            ocr_used = True
            warnings.append("Low text density detected; falling back to OCR")
            pages_text = []
            for page_num in range(page_count):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img)
                pages_text.append(ocr_text)

        doc.close()
        full_text = "\n\n".join(pages_text).strip() if pages_text else None

        return ParseResult(
            text=full_text or None,
            metadata={"page_count": page_count, "ocr_used": ocr_used},
            warnings=warnings,
            artifact_type=(
                ArtifactType.OCR_TEXT.value if ocr_used else ArtifactType.EXTRACTED_TEXT.value
            ),
        )
