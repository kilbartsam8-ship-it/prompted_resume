import docx
import PyPDF2
from typing import List
from .models import ParsedResume


class ResumeParser:
    """
    Responsible only for reading resume files and extracting
    raw text and hyperlinks.
    """

    def parse(self, file_path: str, file_type: str = "pdf") -> ParsedResume:
        text = ""
        links: List[str] = []

        try:
            if file_type == "pdf":
                text, links = self._parse_pdf(file_path)

            elif file_type == "docx":
                text, links = self._parse_docx(file_path)

            elif file_type == "txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

            else:
                raise ValueError(f"Unsupported file type: {file_type}")

        except Exception as e:
            text = f"__READ_ERROR__: {str(e)}"
            links = []

        return ParsedResume(
            text=text.strip(),
            links=sorted(set(links))
        )

    # -------------------- internal helpers --------------------

    def _parse_pdf(self, file_path: str):
        text = ""
        links = []

        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

                annots = page.get("/Annots")
                if annots:
                    for a in annots:
                        obj = a.get_object()
                        if "/A" in obj and "/URI" in obj["/A"]:
                            links.append(obj["/A"]["/URI"])

        return text, links

    def _parse_docx(self, file_path: str):
        text = ""
        links = []

        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

        for rel in doc.part.rels.values():
            if "hyperlink" in rel.reltype:
                links.append(rel.target_ref)

        return text, links
