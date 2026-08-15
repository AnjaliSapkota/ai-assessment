from pathlib import Path
import json
import sys


# SOURCE CONFIGURATION

VALID_SOURCES = {"source_1", "source_2"}


def _paths_for(source_id: str):

    if source_id not in VALID_SOURCES:
        raise ValueError(
            "Invalid source. Use 'source_1' or 'source_2'."
        )

    input_path = Path(f"data/tables/{source_id}_table.json")
    output_path = Path(f"data/normalized/{source_id}.json")

    return input_path, output_path


# LOAD TABLE DATA

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


# NORMALIZE TEXT

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


#  NORMALIZE ONE ROW

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

    for key, value in values.items():

        if key == "ALL_MODELS":
            target_models = list(normalized_values.keys())

        elif "," in key:
            target_models = [
                part.strip()
                for part in key.split(",")
                if part.strip() in normalized_values
            ]

        elif key in normalized_values:
            target_models = [key]

        else:
            target_models = []

        for model in target_models:
            normalized_values[model] = normalize_text(value)

    return parameter, normalized_values


#  NORMALIZE COMPLETE TABLE

def normalize_table(table_data, source_id):

    models = table_data.get(
        "models",
        []
    )

    rows = table_data.get(
        "rows",
        []
    )

    parameters = {}

    # Process every row

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

    # Build model-centric structure

    by_model = {}

    for model in models:

        by_model[model] = {}

        for parameter, values in parameters.items():

            by_model[model][parameter] = values.get(
                model
            )

    # Final structure

    normalized_data = {
        "source": table_data.get(
            "source",
            source_id
        ),
        "models": models,
        "parameters": parameters,
        "by_model": by_model
    }

    return normalized_data


#  PRINT SUMMARY

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

    # Missing-value summary

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

    # Example model

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


# SAVE JSON

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


# NORMALIZE ONE SOURCE (callable from main.py or the CLI)

def normalize_source(source_id: str, verbose: bool = True) -> Path:
    """
    Normalize data/tables/{source_id}_table.json into
    data/normalized/{source_id}.json.

    Returns the output path. This is the function main.py calls
    for each source, so the whole pipeline can run in one command
    instead of requiring two separate `uv run python
    normalize_parser.py source_N` invocations by hand.
    """

    input_path, output_path = _paths_for(source_id)

    if verbose:
        print()
        print("=" * 100)
        print("NORMALIZE PARSER")
        print("=" * 100)
        print(f"Source: {source_id}")
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print()
        print("Loading table data...")

    table_data = load_table_data(input_path)

    models = table_data.get("models", [])
    rows = table_data.get("rows", [])

    if verbose:
        print(f"Models found: {len(models)}")
        for model in models:
            print(f"  - {model}")
        print(f"Rows found: {len(rows)}")
        print()
        print("Normalizing...")

    normalized_data = normalize_table(table_data, source_id)

    save_json(normalized_data, output_path)

    if verbose:
        print_summary(normalized_data)
        print()
        print("=" * 100)
        print(f"Output saved to: {output_path}")
        print("=" * 100)

    return output_path


# CLI ENTRY POINT

def main():

    source_id = sys.argv[1] if len(sys.argv) > 1 else "source_1"
    normalize_source(source_id)


if __name__ == "__main__":
    main()