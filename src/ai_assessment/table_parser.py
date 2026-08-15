from pathlib import Path
import json
import re


# Paths
DATA_DIR = Path("data")

INPUT_DIR = Path("data") / "parsed"
OUTPUT_DIR = Path("data") / "tables"


# GGeneral settings

MODEL_PATTERN = re.compile(
    r"^SUN-(?:4|5|6|7|8|10|12|15)K-G06P3$"
)


#load/save

def load_json(path: Path):
 
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{path}"
        )
 
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)
 
 
def save_json(path: Path, data):
 
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
 
    with path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )
 


# Text normalization

def normalize_text(value):

    if value is None:
        return None

    if isinstance(value, list):

        return [
            normalize_text(item)
            for item in value
        ]

    if isinstance(value, dict):

        return {
            str(key).strip(): normalize_text(val)
            for key, val in value.items()
        }

    return str(value).strip()


def normalize_parameter(parameter):

    if parameter is None:
        return ""

    parameter = str(parameter).strip()

    parameter = re.sub(
        r"\s+",
        " ",
        parameter,
    )

    return parameter


# model normalization

def normalize_model_key(key):

    if not isinstance(key, str):
        return key

    key = key.strip()

    if key == "ALL_MODELS":
        return key

    if "," not in key:
        return key

    parts = [
        part.strip()
        for part in key.split(",")
        if part.strip()
    ]

    valid_parts = [
        part
        for part in parts
        if MODEL_PATTERN.fullmatch(part)
    ]

    if not valid_parts:
        return key

    return ", ".join(valid_parts)


def is_model_key(key):

    if not isinstance(key, str):
        return False

    if key == "ALL_MODELS":
        return True

    parts = [
        part.strip()
        for part in key.split(",")
        if part.strip()
    ]

    if not parts:
        return False

    return all(
        MODEL_PATTERN.fullmatch(part)
        for part in parts
    )


# row extraction
def extract_rows(parsed_data):

    if isinstance(parsed_data, list):
        return parsed_data

    if not isinstance(parsed_data, dict):
        return []

    for key in (
        "rows",
        "table_rows",
        "parameters",
        "fields",
    ):

        rows = parsed_data.get(key)

        if isinstance(rows, list):
            return rows

    pages = parsed_data.get("pages")

    if isinstance(pages, list):

        combined = []

        for page in pages:

            if not isinstance(page, dict):
                continue

            for key in (
                "rows",
                "table_rows",
                "parameters",
                "fields",
            ):

                page_rows = page.get(key)

                if isinstance(page_rows, list):
                    combined.extend(page_rows)

        return combined

    return []


# Row normalization

def normalize_row(row):

    if not isinstance(row, dict):
        return None

    parameter = (
        row.get("parameter")
        or row.get("Parameter")
        or row.get("label")
        or ""
    )

    row_type = (
        row.get("type")
        or row.get("Type")
        or ""
    )

    values = (
        row.get("values")
        if row.get("values") is not None
        else row.get("model_values")
    )

    if values is None:
        values = row.get("data")

    if values is None:
        values = row.get("per_model")

    if values is None:
        values = {}

    y = (
        row.get("y")
        if row.get("y") is not None
        else row.get("top")
    )

    confidence = row.get(
        "confidence",
        "unknown",
    )

    flags = row.get(
        "flags",
        [],
    )

    if not isinstance(flags, list):
        flags = [str(flags)]

    parameter = normalize_parameter(
        parameter
    )

    row_type = str(row_type).strip()

    # LIST-STYLE VALUES

    if isinstance(values, list):

        converted = {}

        for item in values:

            if not isinstance(item, dict):
                continue

            model = (
                item.get("model")
                or item.get("models")
                or item.get("name")
            )

            value = (
                item.get("value")
                if item.get("value") is not None
                else item.get("values")
            )

            if model:

                converted[
                    normalize_model_key(model)
                ] = normalize_text(value)

        values = converted

    # MAKE SURE VALUES ARE A DICT

    if not isinstance(values, dict):
        values = {}

    normalized_values = {}

    for key, value in values.items():

        normalized_key = normalize_model_key(
            key
        )

        if isinstance(value, dict):

            if "value" in value:

                normalized_values[
                    normalized_key
                ] = normalize_text(
                    value["value"]
                )

            else:

                normalized_values[
                    normalized_key
                ] = normalize_text(value)

        else:

            normalized_values[
                normalized_key
            ] = normalize_text(value)

    return {
        "y": y,
        "parameter": parameter,
        "type": row_type,
        "values": normalized_values,
        "confidence": confidence,
        "flags": flags,
    }


# NOISE DETECTION

def is_noise_row(row):

    parameter = row["parameter"].strip()
    values = row["values"]

    # Completely empty row
    if not parameter and not values:
        return True

    if (
        not parameter
        and values
    ):

        all_values = []

        for value in values.values():

            if isinstance(value, list):
                all_values.extend(value)
            else:
                all_values.append(value)

        if all_values:

            if all(
                str(value).strip()
                in (
                    "-EU-AM2",
                    "-EU-AM2-P1",
                )
                for value in all_values
            ):
                return True

    return False


def remove_noise_rows(rows):

    return [
        row
        for row in rows
        if not is_noise_row(row)
    ]


# MERGE PARAMETERLESS ROWS

def merge_parameterless_value_rows(rows):

    result = []

    for row in rows:

        if row["parameter"]:

            result.append(row)
            continue

        if not row["values"]:
            continue

        if not result:
            continue

        previous = result[-1]

        if not previous["parameter"]:
            # No real field to attach this continuation to.
            continue

        merged_any = False

        for model, value in row["values"].items():

            if not value:
                continue

            existing = previous["values"].get(model)

            if not existing:
                previous["values"][model] = value

            elif value not in existing:
                previous["values"][model] = f"{existing} {value}"

            merged_any = True

        if not merged_any:
            continue

        if row["type"]:
            previous["type"] = row["type"]

        previous["confidence"] = "merged_wrapped_continuation"

        previous["flags"].append(
            "merged_wrapped_value_continuation_row_level"
        )

        previous["flags"].extend(
            row["flags"]
        )

    return result


# MERGE MPP TRACKER LABEL

def merge_mpp_tracker_parameter(rows):

    result = []

    i = 0

    while i < len(rows):

        current = rows[i]

        if (
            current["parameter"]
            == "No. of MPP Trackers/"
        ):

            if i + 1 < len(rows):

                next_row = rows[i + 1]

                if (
                    next_row["parameter"]
                    == "No. of Strings per MPP Tracker"
                ):

                    merged = dict(current)

                    merged["parameter"] = (
                        "No. of MPP Trackers/"
                        "No. of Strings per MPP Tracker"
                    )

                    if next_row["values"]:
                        merged["values"] = (
                            next_row["values"]
                        )

                    merged["flags"] = (
                        current["flags"]
                        + next_row["flags"]
                    )

                    merged["confidence"] = (
                        next_row["confidence"]
                        or current["confidence"]
                    )

                    result.append(merged)

                    i += 2
                    continue

        result.append(current)

        i += 1

    return result


# GROUP-SPAN DETECTION

def detect_group_span(row):

    """
    Detect fields where fewer values than model columns
    were extracted.

    Example:

        13+13    13+26

    across an 8-model table.

    These must NOT automatically be treated as ordinary
    per-model values.
    """

    values = row["values"]

    model_keys = [
        key
        for key in values
        if is_model_key(key)
        and key != "ALL_MODELS"
    ]

    if len(model_keys) < 8:

        if len(model_keys) == 2:

            row["flags"].append(
                "possible_group_span"
            )

            row["confidence"] = (
                "spanning_or_partial"
            )

    return row


# DUPLICATE REMOVAL

def remove_duplicate_rows(rows):

    seen = set()
    result = []

    for row in rows:

        signature = (
            row["parameter"],
            json.dumps(
                row["values"],
                sort_keys=True,
                ensure_ascii=False,
            ),
        )

        if signature in seen:
            continue

        seen.add(signature)
        result.append(row)

    return result


# SORT

def get_y(row):

    try:
        return float(row["y"])
    except (
        TypeError,
        ValueError,
    ):
        return float("inf")


def sort_rows(rows):

    return sorted(
        rows,
        key=get_y,
    )


# EXTRACT MODELS

def extract_models(parsed_data):

    # Explicit models

    if isinstance(parsed_data, dict):

        explicit_models = parsed_data.get(
            "models"
        )

        if isinstance(
            explicit_models,
            list,
        ):

            models = []

            for model in explicit_models:

                if not isinstance(
                    model,
                    str,
                ):
                    continue

                model = model.strip()

                if (
                    MODEL_PATTERN.fullmatch(model)
                    and model not in models
                ):
                    models.append(model)

            if models:
                return models

        # Layout parser output

        columns = parsed_data.get(
            "model_columns"
        )

        if isinstance(
            columns,
            list,
        ):

            return [
                model
                for model in columns
                if isinstance(model, str)
            ]

    # Fallback: inspect values

    models = []

    for row in extract_rows(parsed_data):

        if not isinstance(row, dict):
            continue

        values = (
            row.get("values")
            or row.get("per_model")
            or {}
        )

        if not isinstance(values, dict):
            continue

        for key in values:

            if (
                key != "ALL_MODELS"
                and is_model_key(key)
            ):

                for model in key.split(","):

                    model = model.strip()

                    if model not in models:
                        models.append(model)

    return models


# BUILD TABLE

def build_table(parsed_data, source_id):

    raw_rows = extract_rows(
        parsed_data
    )

    if not raw_rows:

        raise ValueError(
            "No table rows found."
        )

    # Normalize
    rows = []

    for raw_row in raw_rows:

        row = normalize_row(
            raw_row
        )

        if row is not None:
            rows.append(row)

    # Remove obvious noise
    rows = remove_noise_rows(
        rows
    )

    # Merge wrapped labels
    rows = merge_mpp_tracker_parameter(
        rows
    )

    # Handle parameterless continuation rows
    rows = merge_parameterless_value_rows(
        rows
    )

    # Detect possible group spans
    rows = [
        detect_group_span(row)
        for row in rows
    ]

    # Remove duplicates
    rows = remove_duplicate_rows(
        rows
    )

    # Sort by PDF position
    rows = sort_rows(
        rows
    )

    models = extract_models(
        parsed_data
    )

    manufacturer = (
        parsed_data.get("manufacturer")
        if isinstance(parsed_data, dict)
        else None
    )

    return {
        "source": source_id,
        "models": models,
        "rows": rows,
        "manufacturer": manufacturer,
    }


# VALIDATION

def validate_table(table):

    errors = []

    # Models

    if not table["models"]:

        errors.append(
            "No models detected."
        )

    # Rows

    for index, row in enumerate(
        table["rows"],
        start=1,
    ):

        if not row["parameter"]:

            errors.append(
                f"Row {index} has no parameter."
            )

        if not isinstance(
            row["values"],
            dict,
        ):

            errors.append(
                f"Row {index} has invalid values."
            )

        for key in row["values"]:

            if not is_model_key(key):

                errors.append(
                    f"Row {index} has invalid model "
                    f"key: {key}"
                )

    if errors:

        raise ValueError(
            "\n".join(errors)
        )


# PRINT SUMMARY

def print_summary(table):

    print()
    print("=" * 80)
    print(
        f"SOURCE: {table['source']}"
    )
    print("=" * 80)

    print(
        f"Models detected: "
        f"{len(table['models'])}"
    )

    print(
        f"Rows extracted: "
        f"{len(table['rows'])}"
    )

    confidence_counts = {}

    for row in table["rows"]:

        confidence = row.get(
            "confidence",
            "unknown",
        )

        confidence_counts[
            confidence
        ] = (
            confidence_counts.get(
                confidence,
                0,
            ) + 1
        )

    print()
    print("Confidence:")

    for confidence, count in (
        confidence_counts.items()
    ):

        print(
            f"  {confidence}: {count}"
        )

    flagged = [
        row
        for row in table["rows"]
        if row.get("flags")
    ]

    print()
    print(
        f"Rows with flags: "
        f"{len(flagged)}"
    )

    for row in flagged:

        print(
            f"  - {row['parameter']}: "
            f"{row['flags']}"
        )


# MAIN

def parse_source(source_id):

    input_path = (
        INPUT_DIR
        / f"{source_id}.json"
    )

    output_path = (
        OUTPUT_DIR
        / f"{source_id}_table.json"
    )

    print()
    print("=" * 80)
    print(
        f"PARSING TABLE: {source_id}"
    )
    print("=" * 80)

    print(
        f"Input : {input_path}"
    )

    print(
        f"Output: {output_path}"
    )

    parsed_data = load_json(
        input_path
    )

    table = build_table(
        parsed_data,
        source_id,
    )

    validate_table(
        table
    )

    save_json(
        output_path,
        table,
    )

    print_summary(
        table
    )

    print()
    print(
        f"Saved: {output_path}"
    )

    return output_path


def main():

    parse_source("source_1")
    parse_source("source_2")

