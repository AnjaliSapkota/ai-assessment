from pathlib import Path

import pymupdf


def extract_words(pdf_path: Path) -> None:
    doc = pymupdf.open(pdf_path)

    for page_number, page in enumerate(doc, start=1):
        print(f"\n{'=' * 80}")
        print(f"FILE: {pdf_path.name} | PAGE: {page_number}")
        print(f"{'=' * 80}")

        words = page.get_text("words")

        for word in words[:100]:
            x0, y0, x1, y1, text, block, line, word_no = word

            print(
                f"text={text!r:30} "
                f"x={x0:7.1f} "
                f"y={y0:7.1f} "
                f"block={block} "
                f"line={line}"
            )

    doc.close()