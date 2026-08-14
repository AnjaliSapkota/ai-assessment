from pathlib import Path
import json

import pymupdf


def extract_pdf(pdf_path: Path, output_dir: Path) -> Path:
    """
    Extract text and word-level positional information from a PDF.

    Each word retains its page number and coordinates so that
    downstream processing can reason about table layout.
    """

    doc = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(doc, start=1):
        words = page.get_text("words")

        page_words = []

        for word in words:
            x0, y0, x1, y1, text, block, line, word_no = word

            page_words.append(
                {
                    "text": text,
                    "x0": round(x0, 2),
                    "y0": round(y0, 2),
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "block": block,
                    "line": line,
                    "word": word_no,
                }
            )

        pages.append(
            {
                "page": page_number,
                "width": page.rect.width,
                "height": page.rect.height,
                "words": page_words,
            }
        )

    doc.close()

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{pdf_path.stem}.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(pages, f, indent=2, ensure_ascii=False)

    return output_path