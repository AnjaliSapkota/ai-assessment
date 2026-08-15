import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from workflow.prompt import (
    RECONCILIATION_PROMPT,
    REPORT_GENERATION_PROMPT,
)
from workflow.state import AssessmentState


load_dotenv()


# Gemini model

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


# Load normalized data
def load_normalized_data(
    state: AssessmentState,
) -> AssessmentState:
    """
    Load the normalized JSON produced by the deterministic
    extraction pipeline.
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


# Response text helper
def extract_response_text(response) -> str:
    """
    Extract plain text from a LangChain Gemini response.
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


# JSON cleaning helper

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

    # Handle accidental "json" prefix
    if content.lower().startswith("json"):
        content = content[4:].strip()

    return content


# Reconcile source documents

def reconcile_documents(
    state: AssessmentState,
) -> AssessmentState:
    """
    Compare the normalized Source 1 and Source 2 data
    using Gemini.

    The actual prompt is maintained separately in prompt.py.
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

    prompt = RECONCILIATION_PROMPT.format(
        source_1=source_1,
        source_2=source_2,
    )

    response = model.invoke(prompt)

    content = extract_response_text(response)

    content = clean_json_response(content)

    try:

        reconciliation = json.loads(content)

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Gemini returned invalid JSON during reconciliation.\n\n"
            f"Response:\n{content}"
        ) from exc

    state["reconciliation"] = reconciliation

    return state


# generate final report

def generate_report(
    state: AssessmentState,
) -> AssessmentState:
    """
    Generate the final human-readable Markdown report
    from the structured reconciliation result.

    The report prompt is maintained separately in prompt.py.
    """

    model = get_gemini()

    reconciliation = json.dumps(
        state["reconciliation"],
        ensure_ascii=False,
        indent=2,
    )

    prompt = REPORT_GENERATION_PROMPT.format(
        reconciliation=reconciliation,
    )

    response = model.invoke(prompt)

    content = extract_response_text(response)

    state["report"] = content.strip()

    return state