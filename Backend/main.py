"""
main.py
───────
Main orchestrator for the DDR generation pipeline.

Flow:
  1. Receive inspection PDF + thermal PDF + property info
  2. Extract text and images from both PDFs
  3. Send text to Groq AI
  4. Receive structured DDR JSON
  5. Build Word document with images
  6. Return document bytes to frontend
"""

from pdf_extractor  import extract_both_pdfs
from ai_processor   import AIProcessor
from report_builder import ReportBuilder


# ─────────────────────────────────────────────────────────────
#  MAIN PIPELINE FUNCTION
# ─────────────────────────────────────────────────────────────

def generate_ddr_report(
    inspection_pdf_bytes: bytes,
    thermal_pdf_bytes: bytes,
    property_info: dict,
    gemini_api_key: str = None,   # kept for compatibility
    groq_api_key: str   = None,   # new Groq key
) -> dict:
    """
    Full DDR generation pipeline.

    Returns:
        {
            "success"    : bool,
            "docx_bytes" : bytes,
            "ddr_data"   : dict,
            "stats"      : dict,
            "errors"     : list[str],
        }
    """

    result = {
        "success"    : False,
        "docx_bytes" : None,
        "ddr_data"   : None,
        "stats"      : {},
        "errors"     : [],
    }

    # Use whichever key is provided
    api_key = groq_api_key or gemini_api_key
    if not api_key:
        result["errors"].append("No API key provided.")
        return result

    # ── STEP 1: Extract PDFs ─────────────────────────────────
    try:
        inspection_result, thermal_result = extract_both_pdfs(
            inspection_bytes      = inspection_pdf_bytes,
            thermal_bytes         = thermal_pdf_bytes,
            max_inspection_images = 40,
            max_thermal_images    = 35,
        )

        result["errors"].extend(inspection_result.errors)
        result["errors"].extend(thermal_result.errors)

        result["stats"] = {
            "inspection_pages"  : inspection_result.page_count,
            "thermal_pages"     : thermal_result.page_count,
            "inspection_images" : len(inspection_result.images),
            "thermal_images"    : len(thermal_result.images),
            "inspection_chars"  : len(inspection_result.full_text),
            "thermal_chars"     : len(thermal_result.full_text),
        }

    except Exception as e:
        result["errors"].append(f"PDF extraction failed: {e}")
        return result

    # ── STEP 2: AI Processing ────────────────────────────────
    try:
        processor = AIProcessor(api_key=api_key)
        ddr_data  = processor.generate_ddr(
            inspection_result  = inspection_result,
            thermal_result     = thermal_result,
            property_info      = property_info,
            max_images_to_send = 3,
        )
        result["ddr_data"] = ddr_data

    except Exception as e:
        result["errors"].append(f"AI processing failed: {e}")
        return result

    # ── STEP 3: Build Word Document ──────────────────────────
    try:
        builder    = ReportBuilder()
        docx_bytes = builder.build(
            ddr_data          = ddr_data,
            inspection_result = inspection_result,
            thermal_result    = thermal_result,
            property_info     = property_info,
        )
        result["docx_bytes"] = docx_bytes
        result["success"]    = True

    except Exception as e:
        result["errors"].append(f"Report building failed: {e}")
        return result

    return result