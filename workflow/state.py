from typing import Any, TypedDict


class AssessmentState(TypedDict, total=False):
    """
    Shared state passed between LangGraph nodes.
    """

    # Input documents
    source_1_pdf: str
    source_2_pdf: str

    # Existing deterministic extraction
    source_1_data: dict[str, Any]
    source_2_data: dict[str, Any]

    # Gemini's reconciliation
    reconciliation: dict[str, Any]

    # Final human-readable report
    report: str

    # Validation / pipeline messages
    errors: list[str]