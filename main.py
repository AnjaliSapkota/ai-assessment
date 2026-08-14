from pathlib import Path

from ai_assessment.config import SOURCE_DOCUMENTS
from ai_assessment.downloader import download_pdf
from ai_assessment.pdf_inspector import inspect_pdf
from ai_assessment.pdf_extractor import extract_pdf


RAW_DATA_DIR = Path("data/raw")
EXTRACTED_DATA_DIR = Path("data/extracted")


def main():

    # extract

    for pdf_path in RAW_DATA_DIR.glob("*.pdf"):
        output_path = extract_pdf(
            pdf_path,
            EXTRACTED_DATA_DIR,
        )

        print(f"Extracted: {pdf_path.name}")
        print(f"Saved to: {output_path}")

    # inspect

    for pdf_path in RAW_DATA_DIR.glob("*.pdf"):
        inspect_pdf(pdf_path)

    # download

    # RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # for source_id, source in SOURCE_DOCUMENTS.items():
    #     output_path = RAW_DATA_DIR / f"{source_id}.pdf"

    #     print(f"Downloading {source['name']}...")

    #     download_pdf(
    #         source["url"],
    #         output_path
    #     )

    #     print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()