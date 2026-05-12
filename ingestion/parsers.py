import csv, io, openpyxl
from dataclasses import dataclass, field
@dataclass
class ParseResult:
    text: str
    metadata: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
class PDFParser:
    def parse(self, data: bytes) -> ParseResult:
        try:
            import fitz
            doc = fitz.open(stream=data, filetype="pdf")
            text = "\n".join(page.get_text("text") for page in doc); doc.close()
            return ParseResult(text=text, metadata={"pages": len(doc)})
        except ImportError:
            return ParseResult(
                text="[PDF parsing requires PyMuPDF - install with: pip install PyMuPDF]",
                metadata={"note": "PyMuPDF not available"},
                errors=["PyMuPDF not installed"]
            )
        except Exception as e: return ParseResult(text="", errors=[f"PDF error: {e}"])
class EmailParser:
    def parse(self, data: bytes) -> ParseResult:
        import email; msg = email.message_from_bytes(data); body = ""
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8", errors="replace"); break
        return ParseResult(text=f"From: {msg['From']}\nSubject: {msg['Subject']}\n{body}",
                           metadata={"from": str(msg['From']), "subject": str(msg['Subject']), "date": str(msg['Date'])})
class SpreadsheetParser:
    def parse(self, data: bytes, mime: str) -> ParseResult:
        try:
            if mime == "text/csv":
                rows = list(csv.reader(io.StringIO(data.decode())))
                return ParseResult(text="\n".join(" | ".join(row) for row in rows[:100]), metadata={"rows": len(rows)})
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
            text = "\n".join(f"=== {ws.title} ===\n" + "\n".join(" | ".join(str(c) for c in row if c) for row in list(ws.iter_rows(values_only=True))[:50]) for ws in list(wb.worksheets)[:3])
            wb.close(); return ParseResult(text=text)
        except Exception as e: return ParseResult(text="", errors=[f"Spreadsheet error: {e}"])
