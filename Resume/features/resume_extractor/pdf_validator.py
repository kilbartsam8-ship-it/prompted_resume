from pdf2image import convert_from_path
import pytesseract
import PyPDF2


class PDFValidator:
    """
    Determines whether a PDF is image-based (scanned) or text-based.
    """

    def is_image_based_pdf(
        self,
        pdf_path: str,
        extracted_text: str,
        text_threshold: int = 300,
        sample_pages: int = 3
    ) -> bool:

        try:
            reader = PyPDF2.PdfReader(pdf_path)
            total_pages = len(reader.pages)

            if total_pages == 0:
                return True

            # choose sample pages
            if total_pages <= sample_pages:
                pages_to_check = list(range(total_pages))
            else:
                mid = total_pages // 2
                pages_to_check = [0, mid, total_pages - 1]

            images = convert_from_path(
                pdf_path,
                first_page=min(pages_to_check) + 1,
                last_page=max(pages_to_check) + 1
            )

            for idx, page_index in enumerate(pages_to_check):
                ocr_text = pytesseract.image_to_string(images[idx]).strip()
                page_text = reader.pages[page_index].extract_text() or ""

                # OCR detects text but PDF extraction doesn't
                if len(page_text.strip()) < 20 and len(ocr_text) > 20:
                    return True

            # global text threshold
            if len(extracted_text.strip()) < text_threshold:
                return True

            return False

        except Exception:
            # fail-safe: assume scanned
            return True
