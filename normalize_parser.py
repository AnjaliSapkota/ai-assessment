from pathlib import Path
import json
import re


# ============================================================
# 1. PATHS
# ============================================================

INPUT_PATH = Path(
    "data/parsed/source_2.json"
)

OUTPUT_PATH = Path(
    "data/normalized/source_2.json"
)


# ============================================================
# 2. LOAD PARSED DATA
# ============================================================

def load_parsed_data(path: Path):
    """Load the output produced by layout_parser.py."""

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# 3. NORMALIZE TEXT
# ============================================================

def normalize_text(text):
    """
    Clean small OCR / encoding issues.
    """

    if text is None:
        return None

    text = str(text).strip()

    # Fix common UTF-8/Latin-1 corruption
    replacements = {
        "Â°C": "°C",
        "Efﬁciency": "Efficiency",
        "Efﬁciency": "Efficiency",
        "ﬁ": "fi",
        "ﬂ": "fl",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove trailing commas caused by PDF extraction
    text = text.rstrip(",")

    return text


# ============================================================
# 4. EXPAND GROUPED MODELS
# ============================================================

def expand_group_models(group_string):
    """
    Convert:

        'SUN-4K-G06P3, SUN-5K-G06P3'

    into:

        ['SUN-4K-G06P3', 'SUN-5K-G06P3']
    """

    if not group_string:
        return []

    models = []

    for model in group_string.split(","):

        model = model.strip()

        if model:
            models.append(model)

    return models


# ============================================================
# 5. CREATE EMPTY MODEL DICTIONARY
# ============================================================

def empty_model_dict(models):
    """
    Create:

        {
            model1: None,
            model2: None,
            ...
        }
    """

    return {
        model: None
        for model in models
    }


# ============================================================
# 6. NORMALIZE ONE ROW
# ============================================================

def normalize_row(row, models):
    """
    Convert one parsed row into:

        {
            model1: value,
            model2: value,
            ...
        }

    regardless of whether the source row is:

        common_value
        model_row
        grouped_row
    """

    row_type = row.get("type")
    parameter = normalize_text(
        row.get("parameter", "")
    )

    result = empty_model_dict(models)

    # --------------------------------------------------------
    # COMMON VALUE
    # --------------------------------------------------------

    if row_type == "common_value":

        value = normalize_text(
            row.get("value")
        )

        for model in models:

            result[model] = value

        return parameter, result


    # --------------------------------------------------------
    # MODEL ROW
    # --------------------------------------------------------

    if row_type == "model_row":

        values = row.get(
            "values",
            {}
        )

        for model in models:

            if model in values:

                result[model] = normalize_text(
                    values[model]
                )

        return parameter, result


    # --------------------------------------------------------
    # GROUPED ROW
    # --------------------------------------------------------

    if row_type == "grouped_row":

        values = row.get(
            "values",
            {}
        )

        for model_group, value in values.items():

            group_models = expand_group_models(
                model_group
            )

            clean_value = normalize_text(
                value
            )

            for model in group_models:

                if model in result:

                    result[model] = clean_value

        return parameter, result


    # --------------------------------------------------------
    # UNKNOWN / EMPTY ROW
    # --------------------------------------------------------

    return parameter, result


# ============================================================
# 7. NORMALIZE COMPLETE TABLE
# ============================================================

def normalize_table(parsed_data):

    models = parsed_data.get(
        "models",
        []
    )

    rows = parsed_data.get(
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

        # Ignore rows without a parameter name
        if not parameter:

            print(
                "WARNING: Skipping row without parameter:",
                row
            )

            continue

        # Store parameter
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
        "models": models,
        "parameters": parameters,
        "by_model": by_model
    }

    return normalized_data


# ============================================================
# 8. PRINT SUMMARY
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

    print()

    # --------------------------------------------------------
    # Show model example
    # --------------------------------------------------------

    if models:

        example_model = models[0]

        print("=" * 100)
        print(
            f"EXAMPLE: {example_model}"
        )
        print("=" * 100)

        for parameter, values in data["parameters"].items():

            value = values.get(
                example_model
            )

            print(
                f"{parameter}: {value}"
            )


# ============================================================
# 9. SAVE JSON
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
# 10. MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 100)
    print("LOADING PARSED DATA")
    print("=" * 100)

    parsed_data = load_parsed_data(
        INPUT_PATH
    )

    print(
        f"Models found: {len(parsed_data['models'])}"
    )

    for model in parsed_data["models"]:

        print(
            f"  - {model}"
        )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    normalized_data = normalize_table(
        parsed_data
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