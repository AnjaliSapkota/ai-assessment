import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from workflow.state import AssessmentState


load_dotenv()


# ============================================================
# 1. GEMINI
# ============================================================

def get_gemini():
    """Create the Gemini model used by the workflow."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Add it to the .env file."
        )

    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=api_key,
        temperature=0,
    )


# ============================================================
# 2. LOAD NORMALIZED DATA
# ============================================================

def load_normalized_data(
    state: AssessmentState,
) -> AssessmentState:
    """
    Load normalized structured data produced by
    normalize_parser.py.

    Gemini receives normalized data rather than raw PDF,
    layout, or parsed word-level data.
    """

    source_1_path = Path(
        "data/normalized/source_1.json"
    )

    source_2_path = Path(
        "data/normalized/source_2.json"
    )

    if not source_1_path.exists():
        raise FileNotFoundError(
            f"Normalized Source 1 not found: {source_1_path}"
        )

    if not source_2_path.exists():
        raise FileNotFoundError(
            f"Normalized Source 2 not found: {source_2_path}"
        )

    with source_1_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        source_1_data = json.load(f)

    with source_2_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        source_2_data = json.load(f)

    state["source_1_data"] = source_1_data
    state["source_2_data"] = source_2_data

    return state


# ============================================================
# 3. HELPER: EXTRACT GEMINI TEXT
# ============================================================

def extract_response_text(response) -> str:
    """
    Safely extract text from a LangChain Gemini response.
    """

    content = response.content

    if isinstance(content, list):
        parts = []

        for part in content:
            if isinstance(part, dict):
                parts.append(
                    part.get("text", "")
                )
            else:
                parts.append(str(part))

        content = "".join(parts)

    return str(content).strip()


# ============================================================
# 4. HELPER: CLEAN JSON RESPONSE
# ============================================================

def clean_json_response(content: str) -> str:
    """
    Remove Markdown code fences if Gemini returns JSON
    inside ```json ... ``` blocks.
    """

    content = content.strip()

    if content.startswith("```"):

        lines = content.splitlines()

        # Remove opening fence
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    if content.lower().startswith("json"):
        content = content[4:].strip()

    return content


# ============================================================
# 5. RECONCILE DOCUMENTS
# ============================================================

def reconcile_documents(
    state: AssessmentState,
) -> AssessmentState:
    """
    Reconcile Source 1 and Source 2 using Gemini.

    Gemini is strictly instructed not to invent,
    infer, calculate, or copy values between models.
    """

    model = get_gemini()

    source_1 = json.dumps(
        state["source_1_data"],
        ensure_ascii=False,
        indent=2,
    )

    source_2 = json.dumps(
        state["source_2_data"],
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are an AI assistant performing document reconciliation
for an AI Engineer assessment.

Company:
SunBridge Trading, Kathmandu

Product being evaluated:
SUN-5K-G06P3

You have two normalized manufacturer datasheets.

Your task is to compare ONLY the information supplied
in Source 1 and Source 2.

============================================================
STRICT EVIDENCE RULES
============================================================

1. Use ONLY the supplied Source 1 and Source 2 data.

2. Do NOT use outside knowledge.

3. Do NOT search the internet.

4. Do NOT invent missing values.

5. Do NOT estimate missing values.

6. Do NOT calculate values.

7. Do NOT infer a SUN-5K-G06P3 value from another model.

8. If SUN-5K-G06P3 has null/missing data, preserve it as
   missing or uncertain.

9. A value belonging to SUN-7K-G06P3, SUN-15K-G06P3, etc.
   MUST NOT be copied to SUN-5K-G06P3.

10. Preserve the original source wording wherever possible.

11. Every important value must include its source label
    in the note.

12. If both sources contain the same value, classify it
    as "agreement".

13. If both sources contain different values or meanings,
    classify it as "conflict".

14. If only Source 1 contains a value for SUN-5K-G06P3,
    classify it as "source_1_only".

15. If only Source 2 contains a value for SUN-5K-G06P3,
    classify it as "source_2_only".

16. If the value cannot be established because of extraction
    problems or missing data, classify it as "uncertain".

17. Do NOT turn terminology differences into factual
    equivalence.

18. For example, do not automatically classify
    "Transformerless" and "Non-Isolated" as agreement.
    Preserve the exact terminology and flag the difference.

19. Do NOT treat kW and kVA as the same unit.

20. If one source says kW and another says kVA, preserve
    both units and classify the field appropriately.

21. Structural headings such as:
    - Input Side
    - Output Side
    - Protection
    - General Data
    - Features
    are NOT technical specifications.

22. Garbled or corrupted labels must be preserved as
    extraction issues. Do not guess what they mean.

23. A standard name appearing in a datasheet is NOT proof
    of certification. Do not claim certification unless
    certification evidence is explicitly supplied.

============================================================
PRODUCT SCOPE
============================================================

Only report actual values for:

SUN-5K-G06P3

The documents may contain many other models.

Other models may be mentioned only when necessary to explain
an extraction problem, for example:

"The field contains values for other models but the
SUN-5K-G06P3 value is missing."

Do NOT use another model's value as the product's value.

============================================================
RECONCILIATION CATEGORIES
============================================================

Allowed status values:

"agreement"
"conflict"
"source_1_only"
"source_2_only"
"uncertain"

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

Do not include:

- Markdown
- ```json fences
- explanations before the JSON
- explanations after the JSON

Use exactly this general structure:

{{
  "product": "SUN-5K-G06P3",

  "source_documents": {{
    "source_1": {{
      "models": [],
      "variant": "Source 1 Datasheet",
      "observations": []
    }},

    "source_2": {{
      "models": [],
      "variant": "Source 2 Datasheet",
      "observations": []
    }}
  }},

  "fields": [
    {{
      "field": "",

      "source_1": {{
        "value": null,
        "confidence": "",
        "note": ""
      }},

      "source_2": {{
        "value": null,
        "confidence": "",
        "note": ""
      }},

      "status": ""
    }}
  ],

  "uncertainties": [],

  "important_observations": []
}}

============================================================
CONFIDENCE
============================================================

Use:

"high"
when the SUN-5K-G06P3 value is directly and clearly
available in the normalized data.

"low"
when the value is missing, partial, corrupted, or affected
by extraction uncertainty.

============================================================
SOURCE DATA
============================================================

SOURCE 1 NORMALIZED DATA:

{source_1}


SOURCE 2 NORMALIZED DATA:

{source_2}

============================================================
FINAL CHECK BEFORE RETURNING
============================================================

Before returning the JSON:

- Verify every value belongs to SUN-5K-G06P3.
- Verify no value was copied from another model.
- Verify null remains null when the value is unavailable.
- Verify kW and kVA are not silently treated as equivalent.
- Verify terminology differences are preserved.
- Verify garbled labels are reported as uncertain.
- Verify certification claims are not invented.
- Verify the output is valid JSON.
"""

    response = model.invoke(prompt)

    content = extract_response_text(response)

    content = clean_json_response(content)

    try:
        reconciliation = json.loads(content)

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Gemini returned invalid JSON.\n\n"
            f"Response:\n{content}"
        ) from exc

    state["reconciliation"] = reconciliation

    return state


# ============================================================
# 6. GENERATE REPORT
# ============================================================

def generate_report(
    state: AssessmentState,
) -> AssessmentState:
    """
    Generate the final human-readable compliance draft
    from the structured reconciliation result.
    """

    model = get_gemini()

    reconciliation = json.dumps(
        state["reconciliation"],
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are preparing a professional draft import-compliance
assessment for:

SunBridge Trading, Kathmandu

Product:

SUN-5K-G06P3

The report must be based ONLY on the reconciliation data
provided below.

============================================================
STRICT REPORTING RULES
============================================================

1. Use ONLY the reconciliation data.

2. Do NOT use outside knowledge.

3. Do NOT invent missing information.

4. Do NOT silently select one value when sources conflict.

5. Preserve Source 1 and Source 2 values separately when
   they differ.

6. Do not copy values from another model.

7. If a value is missing or uncertain, write:

"Not established from the supplied documents."

8. Make the source clear for important values.

9. Preserve original units.

10. Do not treat kW and kVA as interchangeable.

11. Do not turn terminology differences into confirmed
    technical equivalence.

12. Do not claim manufacturer identity unless established.

13. Do not claim certification merely because standards
    are listed.

14. If standards are listed but certification evidence is
    not supplied, explicitly say that certification evidence
    is not established from the supplied documents.

15. Clearly separate:
    - agreement
    - conflict
    - source-only information
    - extraction uncertainty

16. Garbled labels should be reported as extraction issues.
    Do not guess their meaning.

18. Do not classify a difference as a technical conflict merely because
    of capitalization, spacing, punctuation, or equivalent formatting.

19. If two values are substantively identical but one source includes a
    unit and the other omits it, classify this as agreement or
    presentation_difference, while preserving the original values.

20. If one source contains a more complete version of the same information
    and the other contains a subset of it, do not automatically classify
    this as conflict.

21. Distinguish true technical conflicts from:
    - formatting differences
    - capitalization differences
    - spacing differences
    - unit-display differences
    - equivalent terminology
    - extraction artifacts

22. Never create a field from a corrupted OCR/PDF extraction label unless
    its meaning can be established from the supplied structured data.
    If the label is corrupted and its meaning cannot be established,
    classify it as an extraction uncertainty rather than a technical
    specification.
============================================================
REPORT STRUCTURE
============================================================

Create a concise professional Markdown report using exactly
these sections:

# SunBridge Trading — Import Compliance Draft

## 1. Executive summary

Summarize:

- product
- overall document consistency
- major agreements
- major conflicts
- major missing/uncertain information
- whether manufacturer clarification is required

Do not make a legal or regulatory clearance decision that
is not supported by the supplied documents.

## 2. Product identification

Include:

- Model
- Product type, only if established
- Manufacturer, only if established

If something is unknown:

"Not established from the supplied documents."

## 3. Manufacturer / document observations

Describe important observations from Source 1 and Source 2.

Do not invent manufacturer identity.

## 4. Technical specifications for SUN-5K-G06P3

Create a Markdown table.

Use columns:

| Parameter | Source 1 | Source 2 | Status |

Include important reconciled technical fields.

For missing values use:

"Not established from the supplied documents."

Preserve units exactly.

## 5. Cross-document comparison

List the important conflicts and explain them briefly.

Examples of categories:

- electrical values
- grid voltage
- grid frequency
- topology
- cooling
- efficiency
- terminology
- unit differences

Do not resolve conflicts unless the reconciliation explicitly
established an agreement.

## 6. Testing and standards evidence

Report only standards/evidence actually present in the
reconciliation.

Do NOT state that the product is certified unless the
reconciliation contains actual certification evidence.

## 7. Labeling / nameplate information

Report actual labeling/nameplate information.

Garbled labels should be described as extraction issues.

## 8. Uncertainties and extraction issues

List:

- missing values
- partial extraction
- null values
- corrupted labels
- model-specific missing data
- other uncertainties

## 9. Items requiring confirmation from manufacturer

Create a numbered list of concrete clarification requests.

Only include issues actually supported by the reconciliation.

## 10. Short methodology note

Explain briefly that:

- normalized PDF extraction was used
- two source documents were compared
- Gemini performed reconciliation
- no outside knowledge was used
- missing/conflicting information was preserved
- values from other models were not substituted

============================================================
RECONCILIATION DATA
============================================================

{reconciliation}

============================================================
FINAL REPORT RULE
============================================================

The report is a DRAFT.

Do not present it as a final legal, customs, engineering,
or regulatory determination.
"""

    response = model.invoke(prompt)

    content = extract_response_text(response)

    state["report"] = content.strip()

    return state