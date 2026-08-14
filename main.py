from pathlib import Path

from ai_assessment.config import SOURCE_DOCUMENTS
from ai_assessment.downloader import download_pdf
from ai_assessment.pdf_inspector import inspect_pdf


RAW_DATA_DIR = Path("data/raw")


def main():
    for pdf_path in RAW_DATA_DIR.glob("*.pdf"):
        inspect_pdf(pdf_path)
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