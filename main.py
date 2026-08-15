import json
from pathlib import Path

from ai_assessment.config import (SOURCE_DOCUMENTS, RAW_DATA_DIR, EXTRACTED_DATA_DIR, PARSED_DATA_DIR, NORMALIZED_DATA_DIR,)
from ai_assessment.downloader import download_pdf
from ai_assessment.pdf_extractor import extract_pdf
from ai_assessment.layout_parser import parse_pdf

from table_parser import parse_source as parse_table
from normalize_parser import normalize_source
from validator import validate_source

from workflow.graph import build_graph


# Paths
OUTPUT_DIR = Path("data/output")

RECONCILIATION_PATH = OUTPUT_DIR / "reconciliation.json"
REPORT_PATH = OUTPUT_DIR / "compliance_draft.md"

SOURCE_IDS = list(SOURCE_DOCUMENTS.keys())  # ["source_1", "source_2"]


# Download
def download_sources():
    """Download all source PDFs defined in config.py."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for source_id, source in SOURCE_DOCUMENTS.items():

        output_path = RAW_DATA_DIR / f"{source_id}.pdf"

        # Avoid downloading again if the file already exists.
        if output_path.exists():
            print(f"Already exists: {output_path}")
            continue

        print(f"Downloading {source['name']}...")

        download_pdf(
            source["url"],
            output_path,
        )

        print(f"Saved to: {output_path}")

# Extract word level pdf data
def extract_sources():
    """Extract word-level PDF data using pdfplumber, for each source."""

    EXTRACTED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for source_id in SOURCE_IDS:

        pdf_path = RAW_DATA_DIR / f"{source_id}.pdf"
        output_path = EXTRACTED_DATA_DIR / f"{source_id}.json"

        if output_path.exists():
            print(f"  [skip] Already extracted: {output_path}")
            continue

        print(f"  Extracting: {pdf_path.name}")
        extract_pdf(pdf_path, EXTRACTED_DATA_DIR)
        print(f"  Saved extracted data to: {output_path}")


# Parse visual table layout
def parse_layout():
    """Convert extracted word-level data into structured table data."""

    PARSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for source_id in SOURCE_IDS:

        extracted_path = EXTRACTED_DATA_DIR / f"{source_id}.json"
        output_path = PARSED_DATA_DIR / f"{source_id}.json"

        if output_path.exists():
            print(f"  [skip] Already layout-parsed: {output_path}")
            continue

        print(f"  Parsing layout: {extracted_path.name}")
        parse_pdf(extracted_path, output_path)
        print(f"  Saved parsed data to: {output_path}")

# parse into a structure table
def build_tables():
    """Turn each source's parsed layout into a structured table."""

    for source_id in SOURCE_IDS:

        table_path = Path("data/tables") / f"{source_id}_table.json"

        if table_path.exists():
            print(f"  [skip] Already table-parsed: {table_path}")
            continue

        print(f"  Building table: {source_id}")
        parse_table(source_id)


# Normalize
def normalize_sources():
    """Normalize every source's table into the per-model schema."""

    for source_id in SOURCE_IDS:

        normalized_path = NORMALIZED_DATA_DIR / f"{source_id}.json"

        if normalized_path.exists():
            print(f"  [skip] Already normalized: {normalized_path}")
            continue

        print(f"  Normalizing: {source_id}")
        normalize_source(source_id, verbose=False)


# validate
def validate_sources():
    """
    Validate each normalized source and surface any problems.

    Errors are printed but non-fatal: a dirty field is still useful
    context for the reconciliation step (and gets surfaced in the
    output), so we don't want a single bad row to kill the whole run.
    """

    all_errors = []

    for source_id in SOURCE_IDS:

        errors, warnings = validate_source(source_id, verbose=False)

        if errors:
            print(f"  [{source_id}] {len(errors)} error(s):")
            for error in errors:
                print(f"    - {error}")

        if warnings:
            print(f"  [{source_id}] {len(warnings)} warning(s):")
            for warning in warnings:
                print(f"    - {warning}")

        if not errors and not warnings:
            print(f"  [{source_id}] OK, no issues found.")

        all_errors.extend(
            f"{source_id}: {error}" for error in errors
        )

    return all_errors

# Main workflow
def main():

    print("=" * 80)
    print("CANTORDUST -- TASK 1")
    print("SunBridge Trading -- China -> Nepal")
    print("=" * 80)

    print("\n[1/7] Downloading source PDFs...")
    download_sources()

    print("\n[2/7] Extracting word-level PDF data...")
    extract_sources()

    print("\n[3/7] Parsing visual table layout...")
    parse_layout()

    print("\n[4/7] Building structured tables...")
    build_tables()

    print("\n[5/7] Normalizing tables...")
    normalize_sources()

    print("\n[6/7] Validating normalized data...")
    validation_errors = validate_sources()

    # Build + run LangGraph workflow

    print("\n[7/7] Reconciling documents with Gemini and generating report...")

    graph = build_graph()

    initial_state = {
        "source_1_pdf": str(RAW_DATA_DIR / "source_1.pdf"),
        "source_2_pdf": str(RAW_DATA_DIR / "source_2.pdf"),
        "errors": validation_errors,
    }

    result = graph.invoke(initial_state)

    # Save outputs

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with RECONCILIATION_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            result["reconciliation"],
            f,
            indent=2,
            ensure_ascii=False,
        )

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write(result["report"])

    # Final status

    print("\n" + "=" * 80)
    print("TASK 1 COMPLETE")
    print("=" * 80)
    print(f"Reconciliation: {RECONCILIATION_PATH}")
    print(f"Report:         {REPORT_PATH}")

    if validation_errors:
        print(f"\nNote: {len(validation_errors)} validation error(s) "
              f"were logged above and passed through to the graph "
              f"state -- review before treating the draft as final.")

    print("=" * 80)


# ENTRY POINT

if __name__ == "__main__":
    main()
