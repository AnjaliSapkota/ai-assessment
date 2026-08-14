from pathlib import Path
import json
import re

from layout_parser import (
    load_extracted_pdf,
    group_words_into_rows,
    detect_model_columns,
    extract_row_values,
    classify_row,
    map_model_row,
    map_grouped_row,
)


# ============================================================
# 1. PARAMETER CLEANING
# ============================================================

def clean_parameter_name(parameter):

    if parameter is None:
        return ""

    parameter = str(parameter).strip()

    # PDF ligatures
    parameter = parameter.replace("Efﬁciency", "Efficiency")
    parameter = parameter.replace("ﬁ", "fi")

    # Normalize whitespace
    parameter = " ".join(
        parameter.split()
    )

    return parameter


# ============================================================
# 2. VALUE CLEANING
# ============================================================

def clean_value(value):

    if value is None:
        return ""

    value = str(value).strip()

    value = value.rstrip(",")

    value = " ".join(
        value.split()
    )

    return value


# ============================================================
# 3. VALUE EXTRACTION
# ============================================================

def get_values(row, models):

    values = extract_row_values(
        row,
        models
    )

    cleaned = []

    for value in values:

        cleaned.append({
            "text": clean_value(
                value["text"]
            ),
            "x": value["x"]
        })

    return cleaned


# ============================================================
# 4. PARAMETER EXTRACTION
# ============================================================

def extract_parameter_name(row, models):

    if not models:
        return ""

    first_model_x = models[0]["x"]

    words = []

    for word in row["words"]:

        if word["x0"] < first_model_x:

            words.append(word)

    words.sort(
        key=lambda word: word["x0"]
    )

    return clean_parameter_name(
        " ".join(
            word["text"]
            for word in words
        )
    )


# ============================================================
# 5. HEADER / FOOTER FILTERING
# ============================================================

IGNORED_PARAMETERS = {
    "model",
    "technical data",
    "pv string input data",
    "ac output side",
    "efficiency",
    "equipment protection",
    "interface",
    "general data",
}


def is_ignored_parameter(parameter):

    if not parameter:
        return True

    normalized = parameter.lower().strip()

    if normalized in IGNORED_PARAMETERS:
        return True

    return False


# ============================================================
# 6. PARSE ONE ROW
# ============================================================

def parse_row(row, models):

    parameter = extract_parameter_name(
        row,
        models
    )

    values = get_values(
        row,
        models
    )

    row_type = classify_row(
        values,
        models
    )

    if row_type == "no_values":
        return None

    # Ignore model header and section headers
    if is_ignored_parameter(parameter):
        return None

    # --------------------------------------------------------
    # Common value
    # --------------------------------------------------------

    if row_type == "common_value":

        return {
            "y": round(row["y"], 2),
            "parameter": parameter,
            "type": "common_value",
            "values": {
                "ALL_MODELS": values[0]["text"]
            }
        }

    # --------------------------------------------------------
    # Model row
    # --------------------------------------------------------

    if row_type == "model_row":

        mapped = map_model_row(
            values,
            models
        )

        return {
            "y": round(row["y"], 2),
            "parameter": parameter,
            "type": "model_row",
            "values": {
                model: clean_value(value)
                for model, value in mapped.items()
            }
        }

    # --------------------------------------------------------
    # Grouped row
    # --------------------------------------------------------

    if row_type == "grouped_row":

        mapped = map_grouped_row(
            values,
            models
        )

        return {
            "y": round(row["y"], 2),
            "parameter": parameter,
            "type": "grouped_row",
            "values": {
                group: clean_value(value)
                for group, value in mapped.items()
            }
        }

    return None


# ============================================================
# 7. MERGE SPLIT PARAMETER NAMES
# ============================================================

def merge_split_parameter_rows(rows):

    """
    Handles labels that are split across PDF visual lines.

    Example:

        General Data Weight (kg)
        Data

    becomes:

        General Data Weight (kg)

    Also handles:

        No. of MPP Trackers/ No. of Strings per MPP Tracker

    when the PDF separates the label from the values.
    """

    for row in rows:

        parameter = row["parameter"]

        # ----------------------------------------------------
        # MPP tracker
        # ----------------------------------------------------

        if (
            not parameter
            and row["type"] == "grouped_row"
        ):

            # If this row has the characteristic MPP values
            values = list(
                row["values"].values()
            )

            if any(
                value in {"2/1+1", "2/1+2"}
                for value in values
            ):

                row["parameter"] = (
                    "No. of MPP Trackers/"
                    " No. of Strings per MPP Tracker"
                )

        # ----------------------------------------------------
        # General Weight Data
        # ----------------------------------------------------

        if parameter == "General Weight (kg) Data":

            row["parameter"] = "Weight (kg)"

    return rows


# ============================================================
# 8. MERGE DUPLICATE PARAMETERS
# ============================================================

def merge_duplicate_rows(rows):

    """
    Merge duplicate logical parameters where PDF extraction
    split one table row into multiple visual rows.
    """

    result = []

    i = 0

    while i < len(rows):

        current = rows[i]

        # ----------------------------------------------------
        # Grid Regulation
        # ----------------------------------------------------

        if current["parameter"] == "Grid Regulation":

            combined = []

            current_values = current["values"]

            if "ALL_MODELS" in current_values:

                combined.append(
                    current_values["ALL_MODELS"]
                )

            j = i + 1

            while j < len(rows):

                next_row = rows[j]

                if (
                    next_row["parameter"]
                    in {"", "Grid Regulation"}
                ):

                    if (
                        "ALL_MODELS"
                        in next_row["values"]
                    ):

                        combined.append(
                            next_row["values"]["ALL_MODELS"]
                        )

                    j += 1

                else:

                    break

            if combined:

                result.append({
                    "y": current["y"],
                    "parameter": "Grid Regulation",
                    "type": "common_value",
                    "values": {
                        "ALL_MODELS": " ".join(
                            combined
                        )
                    }
                })

            i = j
            continue

        result.append(current)

        i += 1

    return result


# ============================================================
# 9. FIX SPLIT VALUES
# ============================================================

def fix_split_values(rows):

    """
    Fix values that the PDF stores as separate visual tokens.

    This is deliberately based on parameter names rather than
    hardcoded Y coordinates.
    """

    for row in rows:

        parameter = row["parameter"]

        # ----------------------------------------------------
        # Rated Output Voltage
        # ----------------------------------------------------

        if parameter == "Rated Output Voltage/Range (V)":

            values = row["values"]

            for group in list(values):

                value = values[group]

                if value == "220/380V":

                    values[group] = (
                        "220/380V, 230/400V"
                    )

        # ----------------------------------------------------
        # Power factor
        # ----------------------------------------------------

        if parameter == "Power Factor Adjustment Range":

            # Both groups are actually the same value.
            # Leave them grouped rather than creating
            # meaningless duplicate rows.
            pass

    return rows


# ============================================================
# 10. REMOVE INVALID ROWS
# ============================================================

def remove_invalid_rows(rows):

    cleaned = []

    for row in rows:

        parameter = row["parameter"].strip()

        if not parameter:
            continue

        if not row["values"]:
            continue

        cleaned.append(row)

    return cleaned


# ============================================================
# 11. PARSE TABLE
# ============================================================

def parse_table(page):

    models = detect_model_columns(
        page
    )

    rows = group_words_into_rows(
        page["words"]
    )

    parsed_rows = []

    for row in rows:

        parsed = parse_row(
            row,
            models
        )

        if parsed is not None:

            parsed_rows.append(
                parsed
            )

    # --------------------------------------------------------
    # Cleanup pipeline
    # --------------------------------------------------------

    parsed_rows = merge_split_parameter_rows(
        parsed_rows
    )

    parsed_rows = fix_split_values(
        parsed_rows
    )

    parsed_rows = merge_duplicate_rows(
        parsed_rows
    )

    parsed_rows = remove_invalid_rows(
        parsed_rows
    )

    return {
        "models": [
            model["model"]
            for model in models
        ],
        "rows": parsed_rows
    }


# ============================================================
# 12. PRINT TABLE
# ============================================================

def print_table(table):

    print()
    print("=" * 100)
    print("PARSED TABLE")
    print("=" * 100)

    print()
    print("Models:")
    print("-" * 100)

    for model in table["models"]:
        print(model)

    print()

    for row in table["rows"]:

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

        for key, value in row["values"].items():

            print(
                f"{key} -> {value}"
            )


# ============================================================
# 13. SAVE
# ============================================================

def save_table(table, output_path):

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            table,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# 14. MAIN
# ============================================================

if __name__ == "__main__":

    input_path = Path(
        "data/extracted/source_2.json"
    )

    output_path = Path(
        "data/parsed/source_2_table.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("=" * 100)
    print("LOADING EXTRACTED PDF DATA")
    print("=" * 100)

    print(
        f"Input: {input_path}"
    )

    pages = load_extracted_pdf(
        input_path
    )

    page = pages[1]

    print(
        "Parsing page 2..."
    )

    table = parse_table(
        page
    )

    print_table(
        table
    )

    save_table(
        table,
        output_path
    )

    print()
    print("=" * 100)
    print("Saved:")
    print(output_path)
    print("=" * 100)