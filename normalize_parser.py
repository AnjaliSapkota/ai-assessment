from pathlib import Path
import json


# ============================================================
# 1. PATHS
# ============================================================

INPUT_PATH = Path(
    "data/tables/source_2_table.json"
)

OUTPUT_PATH = Path(
    "data/normalized/source_2.json"
)


# ============================================================
# 2. LOAD TABLE DATA
# ============================================================

def load_table_data(path: Path):
    """Load output produced by table_parser.py."""

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 3. NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    """Clean small OCR / encoding issues."""

    if text is None:
        return None

    text = str(text).strip()

    replacements = {
        "Â°C": "°C",
        "Efﬁciency": "Efficiency",
        "ﬁ": "fi",
        "ﬂ": "fl",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.rstrip(",")

    return text


# ============================================================
# 4. NORMALIZE ONE ROW
# ============================================================

def normalize_row(row, models):
    """
    Normalize one table-parser row.

    The table parser produces:

        {
            "parameter": "...",
            "values": {
                "MODEL": "VALUE"
            },
            "confidence": "...",
            "flags": [...]
        }

    Missing model values remain None.
    """

    parameter = normalize_text(
        row.get("parameter", "")
    )

    values = row.get("values", {})

    normalized_values = {
        model: None
        for model in models
    }

    for model, value in values.items():

        if model in normalized_values:

            normalized_values[model] = normalize_text(
                value
            )

    return parameter, normalized_values


# ============================================================
# 5. NORMALIZE COMPLETE TABLE
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
        "source": table_data.get("source"),
        "models": models,
        "parameters": parameters,
        "by_model": by_model
    }

    return normalized_data


# ============================================================
# 6. PRINT SUMMARY
# ============================================================

def print_summary(data):

    models = data["models"]

    parameters = data["parameters"]

    print()
    print("=" * 100)
    print("NORMALIZATION COMPLETE")
    print("=" * 100)

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
# 7. SAVE JSON
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
# 8. MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 100)
    print("LOADING TABLE DATA")
    print("=" * 100)

    table_data = load_table_data(
        INPUT_PATH
    )

    print(
        f"Source: {table_data.get('source')}"
    )

    print(
        f"Models found: {len(table_data['models'])}"
    )

    for model in table_data["models"]:

        print(
            f"  - {model}"
        )

    print(
        f"Rows found: {len(table_data['rows'])}"
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

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
    # Print summary
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