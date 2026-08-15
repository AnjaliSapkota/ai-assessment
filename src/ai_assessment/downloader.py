from pathlib import Path

import requests


def download_pdf(url: str, output_path: Path) -> Path:
    """Download a PDF from a public URL."""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    content = response.content

    # Basic protection against saving an HTML error page as a PDF.
    if not content.startswith(b"%PDF"):
        raise ValueError(
            f"Downloaded content does not appear to be a PDF: {url}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)

    return output_path