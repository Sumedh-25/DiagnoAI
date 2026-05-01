"""
pdf_extractor.py
────────────────
Extracts text and images from the Inspection Report and Thermal Report PDFs.

Responsibilities:
  - Read every page of each PDF
  - Pull all text content per page
  - Extract every embedded image with page number
  - Return structured data ready for AI processor
"""

import io
import fitz  # PyMuPDF
from PIL import Image
from typing import Optional


# ─────────────────────────────────────────────────────────────
#  DATA STRUCTURES
# ─────────────────────────────────────────────────────────────

class ExtractedImage:
    """Holds one image pulled from a PDF page."""

    def __init__(
        self,
        page_number: int,
        image_index: int,
        image_bytes: bytes,
        width: int,
        height: int,
        source: str,  # "inspection" or "thermal"
    ):
        self.page_number = page_number
        self.image_index = image_index
        self.image_bytes = image_bytes
        self.width       = width
        self.height      = height
        self.source      = source
        # Human-readable label used in DDR
        self.label       = f"{source.capitalize()}-Page{page_number}-Img{image_index}"

    def to_pil(self):
        return Image.open(io.BytesIO(self.image_bytes))


class PDFExtractResult:
    """Full extraction result for one PDF file."""

    def __init__(self, source: str):
        self.source     = source   # "inspection" or "thermal"
        self.pages_text = []       # list[str] one entry per page
        self.full_text  = ""       # all pages joined into one string
        self.images     = []       # list[ExtractedImage]
        self.page_count = 0
        self.errors     = []       # non-fatal issues recorded here


# ─────────────────────────────────────────────────────────────
#  MAIN EXTRACTOR CLASS
# ─────────────────────────────────────────────────────────────

class PDFExtractor:
    """
    Extracts text and images from a PDF.

    Usage:
        extractor = PDFExtractor()
        result    = extractor.extract(pdf_bytes, source="inspection")
    """

    # Skip images smaller than this (logos, icons, page decorations)
    MIN_WIDTH  = 100
    MIN_HEIGHT = 100

    def extract(
        self,
        pdf_bytes: bytes,
        source: str,                      # "inspection" or "thermal"
        max_images: Optional[int] = None, # optional cap on images
    ) -> PDFExtractResult:
        """
        Main entry point.
        Returns PDFExtractResult with all text and images from the PDF.
        """
        result = PDFExtractResult(source=source)

        # Open PDF from bytes
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            result.errors.append(f"Cannot open PDF: {e}")
            return result

        result.page_count = len(doc)
        image_counter     = 0

        for page_num in range(len(doc)):
            page = doc[page_num]

            # ── Extract text from this page ──────────────────
            try:
                page_text = page.get_text("text").strip()
                result.pages_text.append(page_text)
            except Exception as e:
                result.pages_text.append("")
                result.errors.append(f"Text error page {page_num+1}: {e}")

            # ── Extract images from this page ────────────────
            try:
                image_list = page.get_images(full=True)

                for img_idx, img_info in enumerate(image_list):

                    # Stop if we hit the max_images cap
                    if max_images and image_counter >= max_images:
                        break

                    xref = img_info[0]

                    try:
                        base_image  = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        width       = base_image["width"]
                        height      = base_image["height"]

                        # Skip tiny images (icons, decorations)
                        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                            continue

                        # Convert to PNG bytes for consistency
                        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                        png_buf = io.BytesIO()
                        pil_img.save(png_buf, format="PNG")
                        png_bytes = png_buf.getvalue()

                        extracted = ExtractedImage(
                            page_number  = page_num + 1,
                            image_index  = img_idx + 1,
                            image_bytes  = png_bytes,
                            width        = width,
                            height       = height,
                            source       = source,
                        )
                        result.images.append(extracted)
                        image_counter += 1

                    except Exception as e:
                        result.errors.append(
                            f"Image error page {page_num+1} img {img_idx+1}: {e}"
                        )

            except Exception as e:
                result.errors.append(f"Image list error page {page_num+1}: {e}")

        doc.close()

        # Join all page texts into one big string
        result.full_text = "\n\n--- PAGE BREAK ---\n\n".join(result.pages_text)

        return result


# ─────────────────────────────────────────────────────────────
#  HELPER: Extract both PDFs at once
# ─────────────────────────────────────────────────────────────

def extract_both_pdfs(
    inspection_bytes: bytes,
    thermal_bytes: bytes,
    max_inspection_images: int = 40,
    max_thermal_images: int    = 35,
):
    """
    Convenience function extracts both PDFs and returns both results.
    Returns: (inspection_result, thermal_result)
    """
    extractor = PDFExtractor()

    inspection_result = extractor.extract(
        pdf_bytes  = inspection_bytes,
        source     = "inspection",
        max_images = max_inspection_images,
    )

    thermal_result = extractor.extract(
        pdf_bytes  = thermal_bytes,
        source     = "thermal",
        max_images = max_thermal_images,
    )

    return inspection_result, thermal_result