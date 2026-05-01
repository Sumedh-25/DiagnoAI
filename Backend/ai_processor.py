"""
ai_processor.py
───────────────
Sends extracted PDF data to Groq AI and receives
a fully structured DDR (Detailed Diagnosis Report) as JSON.

Using Groq with llama-3.3-70b-versatile model.
- Completely free
- No quota issues
- Very fast
- Excellent JSON output

IMPROVEMENTS v2:
- Better thermal area mapping
- Better positive side extraction
- More specific prompt instructions
- Thermal readings now properly mapped to areas
"""

import json
from groq import Groq
from pdf_extractor import PDFExtractResult


# ─────────────────────────────────────────────────────────────
#  DDR SCHEMA
# ─────────────────────────────────────────────────────────────

DDR_SCHEMA = {
    "property_issue_summary": "3 to 5 line overview of all issues found",
    "area_wise_observations": [
        {
            "area_name":      "e.g. Hall Skirting Level, Master Bedroom Wall, Common Bathroom",
            "negative_side":  "exact damage visible on impacted side — dampness location, extent, type",
            "positive_side":  "exact source or cause on exposed side — tile gaps, plumbing, cracks etc.",
            "thermal_reading":"exact hotspot and coldspot temperatures from thermal report e.g. Hotspot: 28.8C Coldspot: 23.4C — write Not Available only if truly absent",
            "images":         ["list of image labels relevant to this area e.g. Inspection-Page3-Img1"],
        }
    ],
    "probable_root_cause": "detailed logical explanation combining inspection + thermal findings",
    "severity_assessment": {
        "overall_level": "Low / Moderate / High / Critical",
        "reasoning":     "detailed explanation with specific evidence from documents",
        "area_wise_severity": [
            {
                "area":     "exact area name",
                "severity": "Low / Moderate / High / Critical",
                "reason":   "specific reason with evidence from documents"
            }
        ]
    },
    "recommended_actions": [
        {
            "action":   "specific action to be taken in simple language",
            "area":     "which exact area this applies to",
            "priority": "Immediate / Short Term / Long Term",
        }
    ],
    "additional_notes":                "any other important observations not covered above",
    "missing_or_unclear_information":  ["list each specific missing or unclear item"],
    "conflicts_found":                 ["list any conflicting data between inspection and thermal reports"]
}


# ─────────────────────────────────────────────────────────────
#  SYSTEM PROMPT — IMPROVED v2
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a senior building inspection analyst at UrbanRoof Private Limited with 15 years of experience.
Your job is to read an Inspection Report and a Thermal Imaging Report carefully and generate
a professional Detailed Diagnosis Report (DDR) for the property owner.

═══════════════════════════════════════════════
STRICT RULES — FOLLOW WITHOUT EXCEPTION
═══════════════════════════════════════════════

RULE 1 — NO INVENTION:
Do NOT invent any facts. Use ONLY information present in the provided documents.

RULE 2 — MISSING DATA:
If information is truly missing from both documents → write exactly "Not Available"
But FIRST search carefully in the text before concluding it is missing.

RULE 3 — CONFLICTS:
If inspection report and thermal report give conflicting information → mention the conflict clearly.

RULE 4 — LANGUAGE:
Use simple language that a homeowner can understand.
Avoid unnecessary technical jargon.
Example: say "water leaking through bathroom floor" not "hydrostatic pressure through substrate"

RULE 5 — NO DUPLICATION:
Do not repeat the same observation in multiple sections.

═══════════════════════════════════════════════
HOW TO EXTRACT POSITIVE SIDE (SOURCE AREA)
═══════════════════════════════════════════════

The inspection report describes each area with:
- NEGATIVE SIDE = the impacted/damaged area (where damage is visible)
- POSITIVE SIDE = the source/exposed area (where water is entering from)

For example:
- Negative side: Hall skirting dampness
- Positive side: Common bathroom tile gaps (water leaking from above bathroom)

Look for these clues in the inspection text:
- "Positive side Description" or "Positive Side Inputs"
- Tile gaps, plumbing issues, Nahani trap gaps
- External wall cracks, duct issues
- Bathroom tile hollowness

ALWAYS extract the positive side from the inspection text.
Never write "Not Available" for positive side if the inspection document mentions it.

═══════════════════════════════════════════════
HOW TO READ THERMAL DATA CORRECTLY
═══════════════════════════════════════════════

Each thermal image has:
- Hotspot temperature (highest temp in image)
- Coldspot temperature (lowest temp in image)
- A reference photograph showing the exact area

Rules for thermal analysis:
1. Temperature difference of 3°C or more = active moisture/dampness confirmed
2. Cold zones (blue/cyan color) = moisture present
3. Match each thermal image to an area by reading the text near it
4. The thermal report pages follow the same order as inspection areas

When you see thermal data like:
"Hotspot: 28.8°C, Coldspot: 23.4°C"
→ Write in thermal_reading: "Hotspot: 28.8°C | Coldspot: 23.4°C | Difference: 5.4°C — Active moisture confirmed"

If thermal data exists for an area → ALWAYS include it. Never write Not Available if data is present.

═══════════════════════════════════════════════
HOW TO MAP THERMAL IMAGES TO AREAS
═══════════════════════════════════════════════

The thermal report pages correspond to inspection areas in this order:
- First few thermal pages → Hall area
- Next thermal pages → Bedroom areas
- Then → Kitchen, Master Bedroom
- Then → External Wall, Parking Area
- Then → Common Bathroom ceiling

Read the thermal text on each page and match it to the inspection area
based on the sequence and the reference photo description.

═══════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════

Return ONLY a valid JSON object.
No explanation before or after.
No markdown code blocks.
Start directly with { and end with }
Follow the exact schema provided.
"""


# ─────────────────────────────────────────────────────────────
#  AI PROCESSOR CLASS
# ─────────────────────────────────────────────────────────────

class AIProcessor:
    """
    Sends inspection + thermal data to Groq AI.
    Returns structured DDR as a Python dictionary.
    """

    MODEL_NAME = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    # ─────────────────────────────────────────────────────────
    #  MAIN METHOD
    # ─────────────────────────────────────────────────────────

    def generate_ddr(
        self,
        inspection_result: PDFExtractResult,
        thermal_result: PDFExtractResult,
        property_info: dict,
        max_images_to_send: int = 3,
    ) -> dict:
        """
        Main entry point.
        Sends all data to Groq and returns DDR as a dict.
        """

        # Build the text prompt
        prompt = self._build_prompt(
            inspection_result,
            thermal_result,
            property_info,
        )

        # Call Groq
        raw_response = self._call_groq(prompt)

        # Parse JSON from response
        ddr_data = self._parse_response(raw_response)

        return ddr_data

    # ─────────────────────────────────────────────────────────
    #  BUILD PROMPT — IMPROVED v2
    # ─────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        inspection_result: PDFExtractResult,
        thermal_result: PDFExtractResult,
        property_info: dict,
    ) -> str:

        # List all image labels
        insp_image_labels  = [img.label for img in inspection_result.images]
        therm_image_labels = [img.label for img in thermal_result.images]

        # Use more text for better extraction — Groq handles 128K tokens
        inspection_text = inspection_result.full_text[:20000]
        thermal_text    = thermal_result.full_text[:12000]

        # Build thermal summary to help AI map temperatures to areas
        thermal_summary = self._build_thermal_summary(thermal_result.full_text)

        prompt = f"""
{SYSTEM_PROMPT}

═══════════════════════════════════════════════════════════
PROPERTY INFORMATION
═══════════════════════════════════════════════════════════
Customer Name    : {property_info.get('customer_name',    'Not Available')}
Property Address : {property_info.get('property_address', 'Not Available')}
Property Type    : {property_info.get('property_type',    'Not Available')}
Number of Floors : {property_info.get('floors',           'Not Available')}
Property Age     : {property_info.get('property_age',     'Not Available')} years
Inspection Date  : {property_info.get('inspection_date',  'Not Available')}
Inspected By     : {property_info.get('inspected_by',     'Not Available')}
Previous Audit   : {property_info.get('prev_audit',       'Not Available')}
Previous Repairs : {property_info.get('prev_repair',      'Not Available')}
Selected Areas   : {property_info.get('selected_areas',   'Not Available')}

═══════════════════════════════════════════════════════════
INSPECTION REPORT — COMPLETE TEXT
(Total Pages: {inspection_result.page_count})
READ CAREFULLY — Extract both negative and positive side for each area
═══════════════════════════════════════════════════════════
{inspection_text}

═══════════════════════════════════════════════════════════
THERMAL IMAGING REPORT — COMPLETE TEXT
(Total Pages: {thermal_result.page_count})
READ CAREFULLY — Extract hotspot and coldspot for each image
═══════════════════════════════════════════════════════════
{thermal_text}

═══════════════════════════════════════════════════════════
THERMAL DATA SUMMARY — USE THIS TO MAP TEMPERATURES TO AREAS
═══════════════════════════════════════════════════════════
{thermal_summary}

═══════════════════════════════════════════════════════════
AVAILABLE IMAGE LABELS
═══════════════════════════════════════════════════════════
Inspection Report Images ({len(insp_image_labels)} total images):
{chr(10).join(insp_image_labels[:30]) if insp_image_labels else 'No images extracted'}

Thermal Report Images ({len(therm_image_labels)} total images):
{chr(10).join(therm_image_labels[:30]) if therm_image_labels else 'No images extracted'}

INSTRUCTION FOR IMAGES:
- Assign inspection images to areas based on page number sequence
- Pages 3-6 images → Hall, Bedroom, Master Bedroom, Kitchen areas
- Pages 5-7 images → External wall, parking
- Assign thermal images sequentially to match inspection areas
- Only assign images that are clearly relevant to each area

═══════════════════════════════════════════════════════════
INSPECTOR CHECKLIST INPUTS — USE THESE FOR POSITIVE SIDE
═══════════════════════════════════════════════════════════
WC Leakage at adjacent walls     : {property_info.get('wc_leak_adj',      'Not Available')}
WC Leakage below floor           : {property_info.get('wc_leak_below',    'Not Available')}
WC Leakage timing                : {property_info.get('wc_leak_during',   'Not Available')}
WC Concealed plumbing issue      : {property_info.get('wc_conc_plumb',    'Not Available')}
WC Nahani trap damage            : {property_info.get('wc_nahani_dmg',    'Not Available')}
WC Tile gaps observed            : {property_info.get('wc_tile_gaps',     'Not Available')}
WC Nahani gaps                   : {property_info.get('wc_nahani_gaps',   'Not Available')}
WC Tiles broken or loose         : {property_info.get('wc_tiles_brkn',    'Not Available')}
WC Loose plumbing joints         : {property_info.get('wc_plumb_loose',   'Not Available')}
External wall leakage interior   : {property_info.get('ext_leak_int',     'Not Available')}
External wall leakage timing     : {property_info.get('ext_leak_dur',     'Not Available')}
External wall cracks condition   : {property_info.get('ext_cracks',       'Not Available')}
External wall algae or moss      : {property_info.get('ext_algae',        'Not Available')}
RCC cracks on column and beam    : {property_info.get('rcc_cracks',       'Not Available')}
RCC rust marks                   : {property_info.get('rcc_rust',         'Not Available')}
RCC spalling or corrosion        : {property_info.get('rcc_spalling',     'Not Available')}
Plaster patchwork required       : {property_info.get('plaster_patch',    'Not Available')}
Thermal camera device used       : {property_info.get('thermal_device',   'Not Available')}
Thermal emissivity value         : {property_info.get('thermal_emiss',    'Not Available')}
Thermal reflected temperature    : {property_info.get('thermal_ref_temp', 'Not Available')}
Inspector severity estimate      : {property_info.get('severity_level',   'Auto Detect by AI')}
Additional notes from inspector  : {property_info.get('additional_notes', 'Not Available')}

═══════════════════════════════════════════════════════════
CRITICAL REMINDERS BEFORE YOU GENERATE
═══════════════════════════════════════════════════════════

1. FOR EACH AREA — find BOTH negative AND positive side from the inspection text
   Look for sections labeled "Positive side Description" in the inspection report
   The inspection report clearly lists positive side for each impacted area

2. FOR THERMAL READINGS — use the thermal summary above
   Every thermal image has a hotspot and coldspot temperature
   Map these temperatures to areas based on sequence
   DO NOT write "Not Available" for thermal readings if temperatures are listed above

3. FOR IMAGES — assign sequentially by page
   Early pages = Hall/Bedroom areas
   Later pages = Bathrooms/External wall

4. GENERATE ALL 7 REQUIRED SECTIONS without skipping any

Now generate the complete DDR JSON following this exact schema:
{json.dumps(DDR_SCHEMA, indent=2)}

Return ONLY the JSON. Start with {{ end with }}
"""
        return prompt

    # ─────────────────────────────────────────────────────────
    #  BUILD THERMAL SUMMARY — NEW HELPER
    # ─────────────────────────────────────────────────────────

    def _build_thermal_summary(self, thermal_text: str) -> str:
        """
        Extracts thermal readings from text and creates a clean summary.
        This helps AI map temperatures to areas more accurately.
        """
        lines   = thermal_text.split('\n')
        summary = []
        page    = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect page breaks
            if 'PAGE BREAK' in line:
                page += 1
                continue

            # Extract hotspot lines
            if 'Hotspot' in line and '°C' in line:
                summary.append(f"Thermal Image {page+1} → {line.strip()}")

            # Extract coldspot lines
            if 'Coldspot' in line and '°C' in line:
                summary.append(f"Thermal Image {page+1} → {line.strip()}")

        if not summary:
            return "Thermal data could not be parsed. Please check thermal report format."

        # Group by image number
        result = "THERMAL READINGS BY IMAGE:\n"
        result += "\n".join(summary[:60])  # Limit to 60 lines
        result += "\n\nNote: Map these thermal readings to inspection areas by sequence order."
        return result

    # ─────────────────────────────────────────────────────────
    #  CALL GROQ API
    # ─────────────────────────────────────────────────────────

    def _call_groq(self, prompt: str) -> str:
        """
        Sends prompt to Groq.
        Returns raw text response.
        """
        try:
            response = self.client.chat.completions.create(
                model    = self.MODEL_NAME,
                messages = [
                    {
                        "role":    "system",
                        "content": (
                            "You are a senior building inspection analyst at UrbanRoof. "
                            "Always respond with valid JSON only. "
                            "Extract both negative and positive side for every area. "
                            "Always include thermal readings from the provided thermal data summary. "
                            "Never write Not Available if the data exists in the documents."
                        )
                    },
                    {
                        "role":    "user",
                        "content": prompt
                    }
                ],
                temperature     = 0.1,   # Low = factual and consistent
                max_tokens      = 8000,
                response_format = {"type": "json_object"},
            )
            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")

    # ─────────────────────────────────────────────────────────
    #  PARSE JSON RESPONSE
    # ─────────────────────────────────────────────────────────

    def _parse_response(self, raw_text: str) -> dict:
        """
        Parses JSON from Groq response.
        Handles edge cases where Groq adds extra text.
        """
        text = raw_text.strip()

        # Strip markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            text  = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Try to extract JSON from within response
            start = text.find("{")
            end   = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except Exception:
                    pass

            return self._fallback_ddr(f"JSON parse error: {e}")

    # ─────────────────────────────────────────────────────────
    #  FALLBACK DDR
    # ─────────────────────────────────────────────────────────

    def _fallback_ddr(self, error_msg: str) -> dict:
        """
        Returns safe empty DDR if AI fails completely.
        Ensures report builder never crashes.
        """
        return {
            "property_issue_summary":         "Not Available — AI processing error occurred. Please retry.",
            "area_wise_observations":         [],
            "probable_root_cause":            "Not Available",
            "severity_assessment": {
                "overall_level":              "Not Available",
                "reasoning":                  "Not Available",
                "area_wise_severity":         [],
            },
            "recommended_actions":            [],
            "additional_notes":               f"System Note: {error_msg}",
            "missing_or_unclear_information": ["AI processing failed — please retry."],
            "conflicts_found":                [],
        }