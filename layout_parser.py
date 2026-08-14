from pathlib import Path
import json
import re


# ============================================================
# 1. LOAD EXTRACTED PDF
# ============================================================

def load_extracted_pdf(json_path: Path) -> list:
    """Load word-level PDF extraction data."""

    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 2. GROUP WORDS INTO VISUAL ROWS
# ============================================================

def group_words_into_rows(words, y_tolerance=3):
    """
    Group words that appear on approximately the same visual line.
    """

    rows = []

    sorted_words = sorted(
        words,
        key=lambda word: (word["y0"], word["x0"])
    )

    for word in sorted_words:

        placed = False

        for row in rows:

            if abs(word["y0"] - row["y"]) <= y_tolerance:

                row["words"].append(word)

                row["y"] = sum(
                    w["y0"] for w in row["words"]
                ) / len(row["words"])

                placed = True
                break

        if not placed:

            rows.append({
                "y": word["y0"],
                "words": [word]
            })

    for row in rows:

        row["words"].sort(
            key=lambda word: word["x0"]
        )

    rows.sort(
        key=lambda row: row["y"]
    )

    return rows


# ============================================================
# 3. MODEL DETECTION
# ============================================================

MODEL_PATTERN = re.compile(
    r"SUN-\d+K-G06P3"
)


def detect_model_columns(page):
    """
    Detect model names and their x coordinates.
    """

    models = []

    for word in page["words"]:

        text = word["text"].strip()

        if MODEL_PATTERN.fullmatch(text):

            models.append({
                "model": text,
                "x": word["x0"]
            })

    # Remove duplicates while preserving x position
    unique = {}

    for model in models:
        unique[model["model"]] = model

    return sorted(
        unique.values(),
        key=lambda item: item["x"]
    )


# ============================================================
# 4. VALUE DETECTION
# ============================================================

def is_value(text):
    """
    Determine whether a token is likely to be a table value.

    IMPORTANT:
    We deliberately allow many formats because PDF tables contain
    values such as:

        1100
        120-1000
        13+13
        19.5+39
        6.1/5.8
        98.5%
        <3%
        4000m
        3L/N/PE
        IEC/EN
        G99
        R25
        VDE-AR-N
        61727
        62116
    """

    text = text.strip()

    if not text:
        return False

    # Pure numeric value
    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return True

    # Numeric ranges
    if re.fullmatch(
        r"-?\d+(?:\.\d+)?[-–]\d+(?:\.\d+)?",
        text
    ):
        return True

    # Numeric expressions: 13+13, 19.5+39
    if re.fullmatch(
        r"-?\d+(?:\.\d+)?(?:[+/]\d+(?:\.\d+)?)+",
        text
    ):
        return True

    # Values such as 6.1/5.8
    if re.fullmatch(
        r"-?\d+(?:\.\d+)?/\d+(?:\.\d+)?",
        text
    ):
        return True

    # Percentages
    if re.fullmatch(
        r"[<>]?\d+(?:\.\d+)?%",
        text
    ):
        return True

    # <3, >99
    if re.fullmatch(
        r"[<>]\d+(?:\.\d+)?",
        text
    ):
        return True

    # Number + unit/text
    # Examples: 4000m, 98.5%, 220/380V
    if re.search(r"\d", text):
        return True

    # Standards / codes without numbers
    # Examples: G99, R25 are already caught by digit rule.
    # Keep short alphanumeric codes.
    if re.fullmatch(
        r"[A-Za-z]+(?:[-/][A-Za-z0-9]+)+",
        text
    ):
        return True

    return False


# ============================================================
# 5. VALUE EXTRACTION
# ============================================================

def extract_row_values(row, models):
    """
    Extract values from the model/value area.

    We no longer require a value to match only a narrow numeric regex.
    """

    if not models:
        return []

    first_model_x = models[0]["x"]

    values = []

    for word in row["words"]:

        if word["x0"] < first_model_x:
            continue

        text = word["text"].strip()

        if is_value(text):

            values.append({
                "text": text,
                "x": word["x0"]
            })

    return sorted(
        values,
        key=lambda item: item["x"]
    )


# ============================================================
# 6. MAP MODEL ROW
# ============================================================

def map_model_row(values, models):

    result = {}

    for value, model in zip(values, models):

        result[model["model"]] = value["text"]

    return result


# ============================================================
# 7. MAP GROUPED ROW
# ============================================================

def map_grouped_row(values, models):
    """
    Map values to groups according to horizontal position.
    """

    if not values:
        return {}

    values = sorted(
        values,
        key=lambda value: value["x"]
    )

    # One value applies to all models
    if len(values) == 1:

        return {
            "ALL_MODELS": values[0]["text"]
        }

    boundaries = []

    for i in range(len(values) - 1):

        boundaries.append(
            (
                values[i]["x"]
                + values[i + 1]["x"]
            ) / 2
        )

    groups = [[] for _ in values]

    for model in models:

        group_index = 0

        while (
            group_index < len(boundaries)
            and model["x"] > boundaries[group_index]
        ):
            group_index += 1

        groups[group_index].append(
            model["model"]
        )

    result = {}

    for value, group in zip(values, groups):

        if group:

            result[
                ", ".join(group)
            ] = value["text"]

    return result


# ============================================================
# 8. CLASSIFY ROW
# ============================================================

def classify_row(values, models):

    if not values:
        return "no_values"

    if len(values) == 1:
        return "common_value"

    if len(values) == len(models):
        return "model_row"

    return "grouped_row"


# ============================================================
# 9. PARAMETER NAME
# ============================================================

def extract_parameter_name(row, models, all_rows=None):

    if not models:
        return ""

    first_model_x = models[0]["x"]

    words = [
        word
        for word in row["words"]
        if word["x0"] < first_model_x
    ]

    words.sort(
        key=lambda word: (word["y0"], word["x0"])
    )

    parameter = " ".join(
        word["text"]
        for word in words
    ).strip()

    return parameter


# ============================================================
# 10. PARSE ONE ROW
# ============================================================

def parse_row(row, models, all_rows=None):

    values = extract_row_values(
        row,
        models
    )

    row_type = classify_row(
        values,
        models
    )

    parameter = extract_parameter_name(
        row,
        models,
        all_rows
    )

    return {
        "y": round(row["y"], 2),
        "parameter": parameter,
        "type": row_type,
        "values": values
    }


# ============================================================
# 11. PARSE TABLE PAGE
# ============================================================

def parse_table_page(page):

    models = detect_model_columns(page)

    rows = group_words_into_rows(
        page["words"]
    )

    parsed_rows = []

    for row in rows:

        parsed_rows.append(
            parse_row(
                row,
                models,
                rows
            )
        )

    return models, parsed_rows


# ============================================================
# 12. PRINT
# ============================================================

def print_parsed_table(models, rows):

    print()
    print("=" * 100)
    print("MODELS")
    print("=" * 100)

    for model in models:

        print(
            f"{model['model']:20} "
            f"x={model['x']:.2f}"
        )

    print()

    for row in rows:

        if row["type"] == "no_values":
            continue

        print("=" * 100)

        print(
            f"Y         : {row['y']:.2f}"
        )

        print(
            f"Parameter : {row['parameter']}"
        )

        print(
            f"Type      : {row['type']}"
        )

        print("-" * 100)

        for value in row["values"]:

            print(
                f"x={value['x']:.2f} -> {value['text']}"
            )


# ============================================================
# 13. MAIN
# ============================================================

if __name__ == "__main__":

    input_path = Path(
        "data/extracted/source_2.json"
    )

    output_path = Path(
        "data/parsed/source_2.json"
    )

    pages = load_extracted_pdf(
        input_path
    )

    page = pages[1]

    models, rows = parse_table_page(
        page
    )

    parsed_data = {
        "models": [
            model["model"]
            for model in models
        ],
        "rows": rows
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            parsed_data,
            f,
            indent=4,
            ensure_ascii=False
        )

    print_parsed_table(
        models,
        rows
    )

    print()
    print("=" * 100)
    print(
        f"Parsed JSON saved to: {output_path}"
    )
    print("=" * 100)