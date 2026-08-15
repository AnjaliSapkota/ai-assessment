from pathlib import Path

from ai_assessment.config import SOURCE_DOCUMENTS
from ai_assessment.downloader import download_pdf
from ai_assessment.pdf_extractor import extract_pdf
from ai_assessment.layout_parser import parse_pdf
from workflow.graph import build_graph
import json


RAW_DATA_DIR = Path("data/raw")
EXTRACTED_DATA_DIR = Path("data/extracted")
PARSED_DATA_DIR = Path("data/parsed")


# def download_sources():
#     """Download all source PDFs defined in config.py."""

#     RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

#     for source_id, source in SOURCE_DOCUMENTS.items():

#         output_path = RAW_DATA_DIR / f"{source_id}.pdf"

#         # Avoid downloading again if the file already exists.
#         if output_path.exists():
#             print(f"Already exists: {output_path}")
#             continue

#         print(f"Downloading {source['name']}...")

#         download_pdf(
#             source["url"],
#             output_path,
#         )

#         print(f"Saved to: {output_path}")


# def extract_sources():
#     """Extract word-level PDF data using pdfplumber."""

#     EXTRACTED_DATA_DIR.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     for pdf_path in sorted(
#         RAW_DATA_DIR.glob("*.pdf")
#     ):

#         print(f"\nExtracting: {pdf_path.name}")

#         output_path = extract_pdf(
#             pdf_path,
#             EXTRACTED_DATA_DIR,
#         )

#         print(
#             f"Saved extracted data to: {output_path}"
#         )


# def parse_layout():
#     """
#     Convert extracted word-level data into
#     visually structured table data.
#     """

#     PARSED_DATA_DIR.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     for extracted_path in sorted(
#         EXTRACTED_DATA_DIR.glob("*.json")
#     ):

#         output_path = (
#             PARSED_DATA_DIR
#             / extracted_path.name
#         )

#         print(
#             f"\nParsing layout: {extracted_path.name}"
#         )

#         parse_pdf(
#             extracted_path,
#             output_path,
#         )

#         print(
#             f"Saved parsed data to: {output_path}"
#         )


# def main():

#     print("=" * 80)
#     print("SUNBRIDGE DOCUMENT EXTRACTION PIPELINE")
#     print("=" * 80)

#     # --------------------------------------------------------
#     # Step 1: Download
#     # --------------------------------------------------------

#     print(
#         "\n[1/3] DOWNLOADING SOURCE DOCUMENTS"
#     )

#     download_sources()

#     # --------------------------------------------------------
#     # Step 2: Extract
#     # --------------------------------------------------------

#     print(
#         "\n[2/3] EXTRACTING PDF WORDS"
#     )

#     extract_sources()

#     # --------------------------------------------------------
#     # Step 3: Parse layout
#     # --------------------------------------------------------

#     print(
#         "\n[3/3] PARSING TABLE LAYOUT"
#     )

#     parse_layout()

#     print("\n" + "=" * 80)
#     print("LAYOUT EXTRACTION COMPLETE")
#     print("=" * 80)



import json
from pathlib import Path

from workflow.graph import build_graph


# ============================================================
# PATHS
# ============================================================

OUTPUT_DIR = Path("data/output")

RECONCILIATION_PATH = (
    OUTPUT_DIR / "reconciliation.json"
)

REPORT_PATH = (
    OUTPUT_DIR / "compliance_draft.md"
)


# ============================================================
# MAIN WORKFLOW
# ============================================================

def main():

    print("=" * 80)
    print("CANTORDUST — TASK 1")
    print("SunBridge Trading — China → Nepal")
    print("=" * 80)

    # --------------------------------------------------------
    # Build LangGraph workflow
    # --------------------------------------------------------

    graph = build_graph()

    # --------------------------------------------------------
    # Initial state
    #
    # The actual data is loaded by the first LangGraph node
    # from:
    #
    # data/normalized/source_1.json
    # data/normalized/source_2.json
    #
    # The PDF paths are retained as metadata/reference only.
    # --------------------------------------------------------

    initial_state = {
        "source_1_pdf": "data/raw/source_1.pdf",
        "source_2_pdf": "data/raw/source_2.pdf",
        "errors": [],
    }

    # --------------------------------------------------------
    # Run workflow
    # --------------------------------------------------------

    print(
        "\n[1/3] Loading normalized structured data..."
    )

    result = graph.invoke(initial_state)

    print(
        "[2/3] Reconciling documents with Gemini..."
    )

    print(
        "[3/3] Generating compliance draft..."
    )

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Save reconciliation JSON
    # --------------------------------------------------------

    with RECONCILIATION_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result["reconciliation"],
            f,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # Save compliance report
    # --------------------------------------------------------

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            result["report"]
        )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("TASK 1 COMPLETE")
    print("=" * 80)

    print(
        f"Reconciliation: {RECONCILIATION_PATH}"
    )

    print(
        f"Report:         {REPORT_PATH}"
    )

    print("=" * 80)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()