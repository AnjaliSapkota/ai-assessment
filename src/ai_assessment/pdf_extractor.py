from pathlib import Path
import json

import pdfplumber


def extract_pdf(pdf_path: Path, output_dir: Path) -> Path:
    """
    Extract word-level text and coordinates from a PDF using pdfplumber.

    The extracted words retain their page number and position so that
    downstream parsing can reconstruct the visually positioned table.
    """

    pages = []

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            words = page.extract_words(
                use_text_flow=False,
                keep_blank_chars=False,
            )

            page_words = []

            for word in words:
                page_words.append(
                    {
                        "text": word["text"],
                        "x0": round(word["x0"], 2),
                        "x1": round(word["x1"], 2),
                        "top": round(word["top"], 2),
                        "bottom": round(word["bottom"], 2),
                    }
                )

            pages.append(
                {
                    "page": page_number,
                    "width": page.width,
                    "height": page.height,
                    "words": page_words,
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{pdf_path.stem}.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            pages,
            f,
            indent=2,
            ensure_ascii=False,
        )

    return output_path