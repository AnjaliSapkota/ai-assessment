from pathlib import Path
import json
import re

# load extracted pdf
def load_extracted_pdf(json_path: Path) -> list:
    """Load word-level PDF extraction data."""
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# takes individual words and reconstructs the visual rows of the PDF.
def group_words_into_rows(words, y_tolerance=3):
    """
    Group words that appear on approximately the same horizontal line.

    PDF extraction gives every word its own y-coordinate.
    Words belonging to the same visual row may have slightly
    different y values, so we use a tolerance.
    """

    rows = []

    # Sort from top to bottom, then left to right
    sorted_words = sorted(
        words,
        key=lambda word: (word["y0"], word["x0"])
    )

    for word in sorted_words:

        placed = False

        for row in rows:

            # Compare this word's y position with the row's average y
            if abs(word["y0"] - row["y"]) <= y_tolerance:

                row["words"].append(word)

                # Update average y
                row["y"] = sum(
                    w["y0"] for w in row["words"]
                ) / len(row["words"])

                placed = True
                break

        if not placed:
            rows.append(
                {
                    "y": word["y0"],
                    "words": [word],
                }
            )

    # Sort words within each row from left to right
    for row in rows:
        row["words"].sort(key=lambda word: word["x0"])

    # Sort rows from top to bottom
    rows.sort(key=lambda row: row["y"])

    return rows


def print_rows(rows):
    """Print reconstructed visual rows."""

    for row_number, row in enumerate(rows, start=1):

        text = " ".join(
            word["text"]
            for word in row["words"]
        )

        print(
            f"{row_number:03d} | "
            f"y={row['y']:7.2f} | "
            f"{text}"
        )


def inspect_pdf(json_path: Path):
    """Inspect all pages of an extracted PDF."""

    pages = load_extracted_pdf(json_path)

    for page in pages:

        print()
        print("=" * 100)
        print(
            f"PAGE {page['page']} "
            f"({page['width']:.1f} x {page['height']:.1f})"
        )
        print("=" * 100)

        rows = group_words_into_rows(page["words"])

        print_rows(rows)

        # if page["page"] == 2:
        #     print_model_columns(page)

        if page["page"] == 2:

            for y in [
                88.03,
                99.76,
                111.46,
                123.62,
                135.18,
                146.65,
                158.92,
            ]:
                print_row_coordinates(page, y)


MODEL_PATTERN = re.compile(
    r"SUN-\d+K-G06P3"
)


def detect_model_columns(page):
    """
    Detect model names and their horizontal positions.

    The datasheet contains model names in the header row.
    We use their x coordinates as anchors for the table columns.
    """

    model_columns = []

    for word in page["words"]:
        text = word["text"]

        if MODEL_PATTERN.fullmatch(text):
            model_columns.append(
                {
                    "model": text,
                    "x": word["x0"],
                }
            )

    return sorted(
        model_columns,
        key=lambda item: item["x"]
    )

def print_model_columns(page):
    """Print detected model columns."""

    models = detect_model_columns(page)

    print()
    print("Detected model columns:")
    print("-" * 60)

    for model in models:
        print(
            f"{model['model']:20} "
            f"x={model['x']:.2f}"
        )

def get_row_words(page, target_y, tolerance=3):
    """
    Return words belonging to a particular visual row.
    """

    words = [
        word
        for word in page["words"]
        if abs(word["y0"] - target_y) <= tolerance
    ]

    return sorted(
        words,
        key=lambda word: word["x0"]
    )


def print_row_coordinates(page, target_y):
    """
    Print every word in a row with its x-coordinate.
    """

    words = get_row_words(page, target_y)

    print()
    print(f"Row around y={target_y}")
    print("-" * 80)

    for word in words:
        print(
            f"x={word['x0']:7.2f} | "
            f"text={word['text']}"
        )

def extract_row_values(page, target_y, tolerance=3):
    """
    Extract values from a table row and map them to model columns
    based on their horizontal positions.
    """

    # Get words from the requested row
    words = get_row_words(
        page,
        target_y,
        tolerance
    )

    # Detect model column positions
    models = detect_model_columns(page)

    results = []

    for word in words:

        # Ignore words that are part of the parameter name
        # by only considering words positioned after the first model column
        if word["x0"] >= models[0]["x"]:
            results.append(
                {
                    "text": word["text"],
                    "x": word["x0"]
                }
            )

    return results

if __name__ == "__main__":

    json_path = Path("data/extracted/source_2.json")

    pages = load_extracted_pdf(json_path)

    page = pages[1]  # page 2

    print_row_coordinates(page, 88.03)