import json
import os
from pathlib import Path

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
    Load the normalized structured data produced by
    normalize_parser.py.

    Gemini should reason over normalized table data rather
    than raw PDF/layout extraction.
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
# 3. RECONCILE DOCUMENTS
# ============================================================

def reconcile_documents(
    state: AssessmentState,
) -> AssessmentState:
    """
    Ask Gemini to reconcile the two manufacturer datasheets.

    Gemini must not invent, infer, or silently repair
    missing/conflicting information.
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
You are assisting with an AI Engineer assessment for
SunBridge Trading, Kathmandu.

The task is to compare two manufacturer datasheets for
the same solar inverter product family.

The buyer is ordering:

SUN-5K-G06P3

Your job is to reconcile the normalized structured
information from both manufacturer documents.

IMPORTANT RULES:

1. Use ONLY the supplied source data.
2. Do NOT use outside knowledge.
3. Do NOT invent missing values.
4. Do NOT calculate or infer a value simply because it
   appears mathematically obvious.
5. If a value is null, treat it as missing.
6. Do NOT assume that a null value means the specification
   does not exist in the real product.
7. If two sources disagree, report both values.
8. Distinguish:
   - agreement
   - conflict
   - source_1_only
   - source_2_only
   - uncertain
9. Pay special attention to SUN-5K-G06P3.
10. Include source attribution for every important value.
11. Preserve values exactly as supplied whenever possible.
12. Similar terminology may be mapped to the same conceptual
    field, but the original source labels must be preserved
    in the notes.
13. Do not treat different units such as kW and kVA as
    identical without explicitly noting the difference.
14. Do not treat terminology such as "Transformerless" and
    "Non-Isolated" as an agreement merely because they may
    describe related concepts. Report the exact source
    wording.
15. If a field is present for other models but null for
    SUN-5K-G06P3, mark the SUN-5K-G06P3 value as uncertain
    or missing. Do not copy another model's value.
16. Section/header rows such as "Input Side", "Output Side",
    "Protection", "General Data", and "Features" are
    structural headings, not technical values. Do not
    report them as meaningful product specifications.
17. Clearly distinguish extraction uncertainty from an
    actual disagreement between the documents.

Return ONLY valid JSON.

Use this structure:

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

Allowed status values:

"agreement"
"conflict"
"source_1_only"
"source_2_only"
"uncertain"

SOURCE 1 NORMALIZED DATA:

{source_1}

SOURCE 2 NORMALIZED DATA:

{source_2}
"""

    response = model.invoke(prompt)

    content = response.content

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            if isinstance(part, dict)
            else str(part)
            for part in content
        )

    content = str(content).strip()

    # --------------------------------------------------------
    # Remove Markdown JSON fences if Gemini returns them.
    # --------------------------------------------------------

    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

        if content.lower().startswith("json"):
            content = content[4:].strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        reconciliation = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Gemini returned invalid JSON.\n"
            f"Response:\n{content}"
        ) from exc

    state["reconciliation"] = reconciliation

    return state


# ============================================================
# 4. GENERATE REPORT
# ============================================================

def generate_report(
    state: AssessmentState,
) -> AssessmentState:
    """
    Generate the human-readable compliance draft from the
    reconciliation result.
    """

    model = get_gemini()

    reconciliation = json.dumps(
        state["reconciliation"],
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
Create a concise professional Markdown draft for
SunBridge Trading's import agent.

The buyer is ordering:

SUN-5K-G06P3

This is a DRAFT based only on two manufacturer
datasheets.

Use ONLY the supplied reconciliation data.

Do NOT use outside knowledge.

Do NOT invent missing information.

Do NOT silently choose one conflicting value.

Where information is missing or uncertain, explicitly say:

"Not established from the supplied documents."

The report should contain:

# SunBridge Trading — Import Compliance Draft

## 1. Executive summary

## 2. Product identification

## 3. Manufacturer / document observations

## 4. Technical specifications for SUN-5K-G06P3

## 5. Cross-document comparison

## 6. Testing and standards evidence

## 7. Labeling / nameplate information

## 8. Uncertainties and extraction issues

## 9. Items requiring confirmation from manufacturer

## 10. Short methodology note

REPORTING RULES:

1. Make the source clear for important values.
2. Preserve original extracted values.
3. If Source 1 and Source 2 agree, identify this as agreement.
4. If they conflict, show both values.
5. If only one source contains a value, identify the
   corresponding source.
6. If a value is null or affected by incomplete extraction,
   explicitly identify the uncertainty.
7. Do not copy values from another inverter model.
8. Do not convert units unless the reconciliation already
   established the conversion.
9. Do not turn a possible interpretation into a fact.
10. Do not claim manufacturer identity unless established
    by the supplied data.
11. Do not claim certification merely because a standard
    name appears in a datasheet. Report the standard as
    documented and identify certification evidence as
    unestablished if no evidence is supplied.

Reconciliation data:

{reconciliation}
"""

    response = model.invoke(prompt)

    content = response.content

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            if isinstance(part, dict)
            else str(part)
            for part in content
        )

    state["report"] = str(content).strip()

    return state