from pathlib import Path

from ai_assessment.config import SOURCE_DOCUMENTS
from ai_assessment.downloader import download_pdf
from ai_assessment.pdf_extractor import extract_pdf
from ai_assessment.layout_parser import parse_pdf


RAW_DATA_DIR = Path("data/raw")
EXTRACTED_DATA_DIR = Path("data/extracted")
PARSED_DATA_DIR = Path("data/parsed")


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


def extract_sources():
    """Extract word-level PDF data using pdfplumber."""

    EXTRACTED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for pdf_path in sorted(
        RAW_DATA_DIR.glob("*.pdf")
    ):

        print(f"\nExtracting: {pdf_path.name}")

        output_path = extract_pdf(
            pdf_path,
            EXTRACTED_DATA_DIR,
        )

        print(
            f"Saved extracted data to: {output_path}"
        )


def parse_layout():
    """
    Convert extracted word-level data into
    visually structured table data.
    """

    PARSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for extracted_path in sorted(
        EXTRACTED_DATA_DIR.glob("*.json")
    ):

        output_path = (
            PARSED_DATA_DIR
            / extracted_path.name
        )

        print(
            f"\nParsing layout: {extracted_path.name}"
        )

        parse_pdf(
            extracted_path,
            output_path,
        )

        print(
            f"Saved parsed data to: {output_path}"
        )


def main():

    print("=" * 80)
    print("SUNBRIDGE DOCUMENT EXTRACTION PIPELINE")
    print("=" * 80)

    # --------------------------------------------------------
    # Step 1: Download
    # --------------------------------------------------------

    print(
        "\n[1/3] DOWNLOADING SOURCE DOCUMENTS"
    )

    download_sources()

    # --------------------------------------------------------
    # Step 2: Extract
    # --------------------------------------------------------

    print(
        "\n[2/3] EXTRACTING PDF WORDS"
    )

    extract_sources()

    # --------------------------------------------------------
    # Step 3: Parse layout
    # --------------------------------------------------------

    print(
        "\n[3/3] PARSING TABLE LAYOUT"
    )

    parse_layout()

    print("\n" + "=" * 80)
    print("LAYOUT EXTRACTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()