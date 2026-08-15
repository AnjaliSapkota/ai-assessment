from pathlib import Path
import json
import sys


# ============================================================
# 1. SOURCE CONFIGURATION
# ============================================================

# Usage:
#   uv run python normalize_parser.py source_1
#   uv run python normalize_parser.py source_2
#
# If no argument is provided, source_1 is used.

SOURCE = sys.argv[1] if len(sys.argv) > 1 else "source_1"

if SOURCE not in {"source_1", "source_2"}:
    raise ValueError(
        "Invalid source. Use 'source_1' or 'source_2'."
    )


# ============================================================
# 2. PATHS
# ============================================================

INPUT_PATH = Path(
    f"data/tables/{SOURCE}_table.json"
)

OUTPUT_PATH = Path(
    f"data/normalized/{SOURCE}.json"
)


# ============================================================
# 3. LOAD TABLE DATA
# ============================================================

def load_table_data(path: Path):
    """Load output produced by table_parser.py."""

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# 4. NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    """
    Clean small OCR / encoding issues without changing
    the underlying technical meaning.
    """

    if text is None:
        return None

    text = str(text).strip()

    if not text:
        return None

    replacements = {
        # Encoding issues
        "Â°C": "°C",
        "Ã—": "×",
        "Â": "",

        # Ligatures
        "ﬁ": "fi",
        "ﬂ": "fl",
        "Efﬁciency": "Efficiency",

        # Common encoding variants
        "â€“": "–",
        "â€”": "—",
        "â€™": "’",
        "â€œ": "“",
        "â€": "”",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove unnecessary trailing commas
    text = text.rstrip(",")

    # Normalize repeated whitespace
    text = " ".join(text.split())

    return text


# ============================================================
# 5. NORMALIZE ONE ROW
# ============================================================

def normalize_row(row, models):
    """
    Normalize one table-parser row.

    Expected input:

        {
            "parameter": "...",
            "values": {
                "SUN-5K-G06P3": "6.5"
            },
            "confidence": "...",
            "flags": [...]
        }

    Missing model values remain None.
    """

    parameter = normalize_text(
        row.get("parameter", "")
    )

    values = row.get(
        "values",
        {}
    )

    normalized_values = {
        model: None
        for model in models
    }

    if not isinstance(values, dict):
        return parameter, normalized_values

    for model, value in values.items():

        if model in normalized_values:

            normalized_values[model] = normalize_text(
                value
            )

    return parameter, normalized_values


# ============================================================
# 6. NORMALIZE COMPLETE TABLE
# ============================================================

def normalize_table(table_data):

    models = table_data.get(
        "models",
        []
    )

    rows = table_data.get(
        "rows",
        []
    )

    parameters = {}

    # --------------------------------------------------------
    # Process every row
    # --------------------------------------------------------

    for row in rows:

        parameter, values = normalize_row(
            row,
            models
        )

        if not parameter:
            print(
                "WARNING: Skipping row without parameter:",
                row
            )
            continue

        parameters[parameter] = values

    # --------------------------------------------------------
    # Build model-centric structure
    # --------------------------------------------------------

    by_model = {}

    for model in models:

        by_model[model] = {}

        for parameter, values in parameters.items():

            by_model[model][parameter] = values.get(
                model
            )

    # --------------------------------------------------------
    # Final structure
    # --------------------------------------------------------

    normalized_data = {
        "source": table_data.get(
            "source",
            SOURCE
        ),
        "models": models,
        "parameters": parameters,
        "by_model": by_model
    }

    return normalized_data


# ============================================================
# 7. PRINT SUMMARY
# ============================================================

def print_summary(data):

    models = data["models"]

    parameters = data["parameters"]

    print()
    print("=" * 100)
    print("NORMALIZATION COMPLETE")
    print("=" * 100)

    print(
        f"Source: {data.get('source')}"
    )

    print(
        f"Models: {len(models)}"
    )

    print(
        f"Parameters: {len(parameters)}"
    )

    # --------------------------------------------------------
    # Missing-value summary
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("MISSING VALUES")
    print("=" * 100)

    for model in models:

        missing = 0

        for parameter, values in parameters.items():

            if values.get(model) is None:
                missing += 1

        print(
            f"{model}: {missing} missing"
        )

    # --------------------------------------------------------
    # Example model
    # --------------------------------------------------------

    if models:

        example_model = models[0]

        print()
        print("=" * 100)
        print(
            f"EXAMPLE: {example_model}"
        )
        print("=" * 100)

        for parameter, values in parameters.items():

            value = values.get(
                example_model
            )

            print(
                f"{parameter}: {value}"
            )


# ============================================================
# 8. SAVE JSON
# ============================================================

def save_json(data, path: Path):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# 9. MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("NORMALIZE PARSER")
    print("=" * 100)

    print(
        f"Source: {SOURCE}"
    )

    print(
        f"Input:  {INPUT_PATH}"
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print()
    print(
        "Loading table data..."
    )

    table_data = load_table_data(
        INPUT_PATH
    )

    models = table_data.get(
        "models",
        []
    )

    rows = table_data.get(
        "rows",
        []
    )

    print(
        f"Models found: {len(models)}"
    )

    for model in models:

        print(
            f"  - {model}"
        )

    print(
        f"Rows found: {len(rows)}"
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    print()
    print(
        "Normalizing..."
    )

    normalized_data = normalize_table(
        table_data
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_json(
        normalized_data,
        OUTPUT_PATH
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print_summary(
        normalized_data
    )

    print()
    print("=" * 100)
    print(
        f"Output saved to: {OUTPUT_PATH}"
    )
    print("=" * 100)


# ============================================================
# 10. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()