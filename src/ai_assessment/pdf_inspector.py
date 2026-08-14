from pathlib import Path

import pymupdf


def inspect_pdf(pdf_path: Path) -> None:
    doc = pymupdf.open(pdf_path)

    print(f"\n{'=' * 60}")
    print(f"FILE: {pdf_path}")
    print(f"Pages: {len(doc)}")
    print(f"{'=' * 60}")

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text("text")

        print(f"\n--- Page {page_number} ---")
        print(f"Characters extracted: {len(text)}")

        # Show only the first 500 characters for now
        preview = text[:500].replace("\n", " | ")
        print(preview)

    doc.close()