from pathlib import Path
import json
import re

# 1. LOAD EXTRACTED PDF JSON

def load_extracted_pdf(json_path: Path) -> list:
    """
    Load word-level PDF extraction data from a JSON file.

    Each word contains information such as:
        - text
        - x0
        - y0
    """

    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# 2. GROUP WORDS INTO VISUAL ROWS

def group_words_into_rows(words, y_tolerance=3):
    """
    Group words that appear on approximately the same
    horizontal line.

    PDF extraction gives individual words with x/y coordinates.
    Words belonging to the same visual row may have slightly
    different y values, so we use a tolerance.
    """

    rows = []

    # Sort:
    #   1. top to bottom using y
    #   2. left to right using x
    sorted_words = sorted(
        words,
        key=lambda word: (word["y0"], word["x0"])
    )

    for word in sorted_words:

        placed = False

        # Try to place the word into an existing row
        for row in rows:

            # Check whether the word is horizontally aligned
            # with this row
            if abs(word["y0"] - row["y"]) <= y_tolerance:

                row["words"].append(word)

                # Recalculate the row's average y-coordinate
                row["y"] = (
                    sum(w["y0"] for w in row["words"])
                    / len(row["words"])
                )

                placed = True
                break

        # If the word doesn't belong to an existing row,
        # create a new row
        if not placed:

            rows.append(
                {
                    "y": word["y0"],
                    "words": [word],
                }
            )

    # Sort words inside each row from left to right
    for row in rows:
        row["words"].sort(
            key=lambda word: word["x0"]
        )

    # Sort rows from top to bottom
    rows.sort(
        key=lambda row: row["y"]
    )

    return rows


# 3. PRINT RECONSTRUCTED ROWS

def print_rows(rows):
    """
    Print reconstructed visual rows.
    """

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


# 4. INSPECT PDF

def inspect_pdf(json_path: Path):
    """
    Inspect all pages of an extracted PDF.

    This is mainly a debugging/development function.
    """

    pages = load_extracted_pdf(json_path)

    for page in pages:

        print()
        print("=" * 100)

        print(
            f"PAGE {page['page']} "
            f"({page['width']:.1f} x {page['height']:.1f})"
        )

        print("=" * 100)

        rows = group_words_into_rows(
            page["words"]
        )

        print_rows(rows)


# 5. MODEL DETECTION

MODEL_PATTERN = re.compile(
    r"SUN-\d+K-G06P3"
)


def detect_model_columns(page):
    """
    Detect model names in the table header.

    Example:

        SUN-4K-G06P3
        SUN-5K-G06P3
        SUN-6K-G06P3
        ...

    Returns their horizontal x-coordinate positions.
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

    # Sort models from left to right
    return sorted(
        model_columns,
        key=lambda item: item["x"]
    )


# ============================================================
# 6. PRINT MODEL COLUMNS
# ============================================================

def print_model_columns(page):
    """
    Print detected model columns and their x positions.
    """

    models = detect_model_columns(page)

    print()
    print("Detected model columns:")
    print("-" * 60)

    if not models:
        print("No model columns detected.")
        return

    for model in models:

        print(
            f"{model['model']:20} "
            f"x={model['x']:.2f}"
        )


# 7. GET WORDS FROM A SPECIFIC ROW

def get_row_words(page, target_y, tolerance=3):
    """
    Return all words belonging to a particular visual row.

    Words are sorted from left to right.
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


# 8. PRINT WORDS + X COORDINATES

def print_row_coordinates(
    page,
    target_y,
    tolerance=3
):
    """
    Print every word in a row together with its x-coordinate.

    Useful for understanding the PDF table layout.
    """

    words = get_row_words(
        page,
        target_y,
        tolerance
    )

    print()
    print(
        f"Row around y={target_y}"
    )
    print("-" * 80)

    for word in words:

        print(
            f"x={word['x0']:7.2f} | "
            f"text={word['text']}"
        )


# 9. EXTRACT VALUES FROM A ROW

def extract_row_values(
    page,
    target_y,
    tolerance=3
):
    """
    Extract table values from a particular row.

    The left side of the row contains the specification name,
    while the values begin around the model columns.

    Example:

        Max. PV Input Power (kW)  5.2  6.5  7.8 ...

    This function returns the values and their x positions.
    """

    # Get all words in this visual row
    words = get_row_words(
        page,
        target_y,
        tolerance
    )

    # Detect model columns
    models = detect_model_columns(page)

    # If model detection failed, return nothing
    if not models:
        return []

    # First model column marks approximately where
    # the specification values begin
    first_model_x = models[0]["x"]

    results = []

    for word in words:

        # Ignore specification-name words on the left.
        #
        # Only keep words at or after the first model column.
        if word["x0"] >= first_model_x:

            results.append(
                {
                    "text": word["text"],
                    "x": word["x0"]
                }
            )

    return results


# 10. FIND CLOSEST MODEL TO A VALUE

def find_closest_model(x, models):
    """
    Find the model column closest to a value's x-coordinate.

    Example:

        value x = 209.7

        model positions:
            195.4 -> SUN-4K
            240.6 -> SUN-5K

        209.7 is closer to 195.4,
        therefore the value belongs to SUN-4K.
    """

    if not models:
        return None

    closest = min(
        models,
        key=lambda model: abs(
            model["x"] - x
        )
    )

    return closest


# 11. MAP ROW VALUES TO MODELS

def map_row_values_to_models(
    page,
    target_y,
    tolerance=3
):
    """
    Extract values from a table row and map each value
    to the closest model column.

    Returns something like:

        {
            "SUN-4K-G06P3": "5.2",
            "SUN-5K-G06P3": "6.5",
            "SUN-6K-G06P3": "7.8",
            ...
        }
    """

    # Detect model columns
    models = detect_model_columns(page)

    if not models:
        return {}

    # Extract values from the row
    values = extract_row_values(
        page,
        target_y,
        tolerance
    )

    result = {}

    for value in values:

        closest_model = find_closest_model(
            value["x"],
            models
        )

        if closest_model:

            result[
                closest_model["model"]
            ] = value["text"]

    return result


# 12. MAIN


if __name__ == "__main__":

    json_path = Path(
        "data/extracted/source_2.json"
    )

    pages = load_extracted_pdf(
        json_path
    )

    # Page 2
    page = pages[1]

    # Show detected model columns

    print_model_columns(page)

    # Inspect one table row

    print_row_coordinates(
        page,
        88.03
    )

    # Extract values from that row

    values = extract_row_values(
        page,
        88.03
    )

    print()
    print("Extracted row values:")
    print("-" * 60)

    for value in values:

        print(
            f"x={value['x']:7.2f} | "
            f"value={value['text']}"
        )

    # Map values to models

    mapped = map_row_values_to_models(
        page,
        88.03
    )

    print()
    print("Mapped values:")
    print("-" * 60)

    for model, value in mapped.items():

        print(
            f"{model:20} -> {value}"
        )