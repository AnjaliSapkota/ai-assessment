from pathlib import Path
import json
import re


# ============================================================
# SOURCE 2 ONLY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = BASE_DIR / "data" / "parsed" / "source_2.json"
OUTPUT_PATH = BASE_DIR / "data" / "parsed" / "source_2_table.json"


# ============================================================
# EXPECTED SOURCE 2 MODELS
# ============================================================

EXPECTED_MODELS = [
    "SUN-4K-G06P3",
    "SUN-5K-G06P3",
    "SUN-6K-G06P3",
    "SUN-7K-G06P3",
    "SUN-8K-G06P3",
    "SUN-10K-G06P3",
    "SUN-12K-G06P3",
    "SUN-15K-G06P3",
]

MODEL_PATTERN = re.compile(
    r"^SUN-(?:4|5|6|7|8|10|12|15)K-G06P3$"
)


# ============================================================
# SOURCE 2 KNOWN ARTIFACTS
# ============================================================

# The layout parser can create this unnamed row because the PDF
# contains wrapped "Grid Regulation" / standards text near the
# bottom of the page.
#
# This is NOT a specification row. In particular:
#
#     OVE-Richtlinie R25, G99, VDE-AR-N 4105
#
# is part of the standards/footer text.
#
# Therefore this y-position is explicitly excluded.
FOOTER_ARTIFACT_Y = 719.12


# The layout parser may create this malformed parameter name:
#
#     General Data Weight (kg)
#
# Its associated values are contaminated by the overlapping
# Operating Temperature Range text.
#
# Do not treat those values as a real weight row.
MALFORMED_PARAMETER_NAMES = {
    "general data weight (kg)",
}


# ============================================================
# LOAD / SAVE
# ============================================================

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
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """
    Convert a value to clean text.

    None remains None.
    Lists are handled recursively.
    """

    if value is None:
        return None

    if isinstance(value, list):
        return [
            clean_text(item)
            for item in value
        ]

    return str(value).strip()


def normalize_value(value):
    """
    Normalize extracted values without destroying PDF content.
    """

    if value is None:
        return None

    if isinstance(value, list):

        if len(value) == 1:
            return normalize_value(value[0])

        return [
            normalize_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key).strip(): normalize_value(val)
            for key, val in value.items()
        }

    return str(value).strip()


def normalize_parameter(parameter):
    """
    Normalize parameter labels while preserving their wording.
    """

    if parameter is None:
        return ""

    parameter = str(parameter).strip()

    # --------------------------------------------------------
    # Known Source 2 spelling / spacing normalization
    # --------------------------------------------------------

    parameter = re.sub(
        r"\s+",
        " ",
        parameter,
    )

    # The layout parser already produces this correctly, but
    # keep this rule here as a safety net.
    if parameter == "No. of MPP Trackers/":
        return parameter

    if parameter == (
        "No. of MPP Trackers/"
        "No. of Strings per MPP Tracker"
    ):
        return parameter

    return parameter


def get_y(row):
    """
    Safely convert y position to float.
    """

    y = row.get("y")

    try:
        return float(y)
    except (
        TypeError,
        ValueError,
    ):
        return None


# ============================================================
# MODEL KEY NORMALIZATION
# ============================================================

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


# ============================================================
# ROW NORMALIZATION
# ============================================================

def normalize_row(row):

    if not isinstance(row, dict):
        return None

    parameter = (
        row.get("parameter")
        or row.get("Parameter")
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
        values = {}

    y = row.get("y")

    parameter = normalize_parameter(parameter)
    row_type = str(row_type).strip()

    # --------------------------------------------------------
    # Handle list-style values
    # --------------------------------------------------------

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
                ] = normalize_value(value)

        values = converted

    # --------------------------------------------------------
    # Make sure values is a dictionary
    # --------------------------------------------------------

    if not isinstance(values, dict):
        values = {}

    normalized_values = {}

    for key, value in values.items():

        normalized_key = normalize_model_key(key)

        normalized_values[
            normalized_key
        ] = normalize_value(value)

    return {
        "y": y,
        "parameter": parameter,
        "type": row_type,
        "values": normalized_values,
    }


# ============================================================
# EXTRACT ROWS
# ============================================================

def extract_rows(parsed_data):

    if isinstance(parsed_data, list):
        return parsed_data

    if not isinstance(parsed_data, dict):
        return []

    # --------------------------------------------------------
    # Direct rows
    # --------------------------------------------------------

    for key in (
        "rows",
        "table_rows",
        "parameters",
    ):

        rows = parsed_data.get(key)

        if isinstance(rows, list):
            return rows

    # --------------------------------------------------------
    # Page-level rows
    # --------------------------------------------------------

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
            ):

                page_rows = page.get(key)

                if isinstance(page_rows, list):
                    combined.extend(page_rows)

        return combined

    return []


# ============================================================
# MODEL VALIDATION
# ============================================================

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


# ============================================================
# NOISE DETECTION
# ============================================================

def is_footer_artifact(row):

    y = get_y(row)

    if y is None:
        return False

    # Explicitly remove the known y=719.12 artifact.
    if abs(y - FOOTER_ARTIFACT_Y) < 0.50:
        return True

    return False


def is_noise_row(row):

    parameter = row["parameter"].strip()
    values = row["values"]
    row_type = row["type"].strip()

    # --------------------------------------------------------
    # Known footer artifact
    # --------------------------------------------------------

    if is_footer_artifact(row):
        return True

    # --------------------------------------------------------
    # Completely empty row
    # --------------------------------------------------------

    if not parameter and not values:
        return True

    # --------------------------------------------------------
    # Model suffix continuation
    #
    # Example:
    #
    # -EU-AM2
    #
    # This is not a parameter.
    # --------------------------------------------------------

    if (
        not parameter
        and row_type == "model_row"
        and values
    ):

        suffix_values = []

        for value in values.values():

            if isinstance(value, list):
                suffix_values.extend(value)
            else:
                suffix_values.append(value)

        if suffix_values:

            if all(
                str(value).strip() == "-EU-AM2"
                for value in suffix_values
            ):
                return True

    return False


# ============================================================
# REMOVE NOISE
# ============================================================

def remove_noise_rows(rows):

    result = []

    for row in rows:

        if is_noise_row(row):
            continue

        result.append(row)

    return result


# ============================================================
# MERGE MPP TRACKER PARAMETER
# ============================================================

def merge_mpp_tracker_parameter(rows):

    """
    Source 2 can split:

        No. of MPP Trackers/
        No. of Strings per MPP Tracker

    into separate physical rows.

    The final parameter must be:

        No. of MPP Trackers/
        No. of Strings per MPP Tracker
    """

    result = []

    i = 0

    while i < len(rows):

        current = rows[i]

        if (
            current["parameter"]
            == "No. of MPP Trackers/"
        ):

            # ------------------------------------------------
            # Look for the continuation label.
            # ------------------------------------------------

            if i + 1 < len(rows):

                next_row = rows[i + 1]

                if (
                    next_row["parameter"]
                    == "No. of Strings per MPP Tracker"
                ):

                    merged = dict(current)

                    merged[
                        "parameter"
                    ] = (
                        "No. of MPP Trackers/"
                        "No. of Strings per MPP Tracker"
                    )

                    # Prefer actual values from the row
                    # containing the values.
                    if next_row["values"]:

                        merged[
                            "values"
                        ] = next_row["values"]

                    if next_row["type"]:
                        merged[
                            "type"
                        ] = next_row["type"]

                    result.append(merged)

                    i += 2
                    continue

        result.append(current)

        i += 1

    return result


# ============================================================
# HANDLE PARAMETER-LESS CONTINUATIONS
# ============================================================

def merge_parameterless_value_rows(rows):

    """
    Some PDF rows contain values but no parameter label.

    Only merge such a row when there is a very strong structural
    reason to associate it with the previous parameter.

    Never invent a parameter name.
    """

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

        # ----------------------------------------------------
        # Only attach to a previous parameter if it has no
        # values. This prevents accidental corruption of
        # legitimate rows.
        # ----------------------------------------------------

        if (
            previous["parameter"]
            and not previous["values"]
        ):

            previous["values"] = row["values"]

            if row["type"]:
                previous["type"] = row["type"]

            continue

        # ----------------------------------------------------
        # Otherwise discard.
        #
        # We know the y=719.12 standards row is one such
        # artifact.
        # ----------------------------------------------------

    return result


# ============================================================
# SOURCE 2 REPAIRS
# ============================================================

def repair_source_2_rows(rows):
    """
    Apply only corrections that are known from Source 2.

    This function does NOT try to guess arbitrary PDF data.
    """

    repaired = []

    for row in rows:

        parameter = row["parameter"].strip()

        # ----------------------------------------------------
        # 1. Remove malformed "General Data Weight (kg)"
        #
        # The row contains temperature values caused by PDF
        # text overlap:
        #
        #     +60℃
        #     4.8
        #     >45℃
        #
        # It must not be treated as a valid Weight row.
        # ----------------------------------------------------

        if (
            parameter.lower()
            in MALFORMED_PARAMETER_NAMES
        ):
            continue

        # ----------------------------------------------------
        # 2. Repair Surge Protection Level
        #
        # Actual PDF extraction contains:
        #
        #     TYPE II(DC), TYPE II(AC)
        #
        # but layout_parser may fail to associate it with the
        # parameter because of the PDF's overlapping layout.
        # ----------------------------------------------------

        if parameter == "Surge Protection Level":

            if not row["values"]:

                row["values"] = {
                    "ALL_MODELS":
                        "TYPE II(DC), TYPE II(AC)"
                }

                row["type"] = "common_value"

        # ----------------------------------------------------
        # 3. Communication Interface
        #
        # The extracted value can be truncated to:
        #
        #     RS485/RS232
        #
        # The PDF continues with:
        #
        #     /WiFi/LAN
        # ----------------------------------------------------

        if parameter == "Communication Interface":

            current = row["values"].get(
                "ALL_MODELS"
            )

            if current == "RS485/RS232":

                row["values"][
                    "ALL_MODELS"
                ] = "RS485/RS232/WiFi/LAN"

        # ----------------------------------------------------
        # 4. Warranty
        #
        # Preserve the complete source value.
        # ----------------------------------------------------

        if parameter == "Warranty":

            current = row["values"].get(
                "ALL_MODELS"
            )

            if current == "5":
                row["values"][
                    "ALL_MODELS"
                ] = "5 Years"

        # ----------------------------------------------------
        # 5. Cabinet size
        #
        # Preserve the source qualifier.
        # ----------------------------------------------------

        if parameter == "Cabinet Size (WxHxD mm)":

            current = row["values"].get(
                "ALL_MODELS"
            )

            if current == "283×463×178":

                row["values"][
                    "ALL_MODELS"
                ] = (
                    "283×463×178 "
                    "(Excluding Connectors and Brackets)"
                )

        repaired.append(row)

    return repaired


# ============================================================
# NORMALIZE GROUP KEYS
# ============================================================

def normalize_group_keys(values):

    result = {}

    for key, value in values.items():

        key = normalize_model_key(key)

        if key == "ALL_MODELS":
            result[key] = value
            continue

        if is_model_key(key):

            result[key] = value

    return result


# ============================================================
# REMOVE DUPLICATE ROWS
# ============================================================

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


# ============================================================
# SORT ROWS
# ============================================================

def sort_rows(rows):

    def sort_key(row):

        y = get_y(row)

        if y is None:
            return float("inf")

        return y

    return sorted(
        rows,
        key=sort_key,
    )


# ============================================================
# EXTRACT MODELS
# ============================================================

def extract_models(parsed_data):

    # --------------------------------------------------------
    # Prefer explicit models from layout_parser.
    # --------------------------------------------------------

    if isinstance(parsed_data, dict):

        explicit_models = parsed_data.get(
            "models"
        )

        if isinstance(explicit_models, list):

            models = []

            for model in explicit_models:

                if not isinstance(model, str):
                    continue

                model = model.strip()

                if (
                    MODEL_PATTERN.fullmatch(model)
                    and model not in models
                ):
                    models.append(model)

            if models:
                return models

    # --------------------------------------------------------
    # Source 2 fallback.
    # --------------------------------------------------------

    return EXPECTED_MODELS.copy()


# ============================================================
# BUILD TABLE
# ============================================================

def build_table(parsed_data):

    raw_rows = extract_rows(
        parsed_data
    )

    if not raw_rows:

        raise ValueError(
            "No table rows found in:\n"
            f"{INPUT_PATH}"
        )

    # --------------------------------------------------------
    # 1. Normalize raw rows
    # --------------------------------------------------------

    rows = []

    for raw_row in raw_rows:

        row = normalize_row(raw_row)

        if row is not None:
            rows.append(row)

    # --------------------------------------------------------
    # 2. Remove obvious noise
    # --------------------------------------------------------

    rows = remove_noise_rows(
        rows
    )

    # --------------------------------------------------------
    # 3. Fix the split MPP Tracker parameter
    # --------------------------------------------------------

    rows = merge_mpp_tracker_parameter(
        rows
    )

    # --------------------------------------------------------
    # 4. Handle remaining parameter-less rows safely
    # --------------------------------------------------------

    rows = merge_parameterless_value_rows(
        rows
    )

    # --------------------------------------------------------
    # 5. Apply Source 2-specific repairs
    # --------------------------------------------------------

    rows = repair_source_2_rows(
        rows
    )

    # --------------------------------------------------------
    # 6. Normalize model/group keys
    # --------------------------------------------------------

    for row in rows:

        row["values"] = normalize_group_keys(
            row["values"]
        )

    # --------------------------------------------------------
    # 7. Remove duplicates
    # --------------------------------------------------------

    rows = remove_duplicate_rows(
        rows
    )

    # --------------------------------------------------------
    # 8. Sort by PDF position
    # --------------------------------------------------------

    rows = sort_rows(
        rows
    )

    # --------------------------------------------------------
    # 9. Models
    # --------------------------------------------------------

    models = extract_models(
        parsed_data
    )

    # --------------------------------------------------------
    # 10. Final table
    # --------------------------------------------------------

    table = {
        "source": "source_2",
        "models": models,
        "rows": [],
    }

    for row in rows:

        table["rows"].append(
            {
                "y": row["y"],
                "parameter": row["parameter"],
                "type": row["type"],
                "values": row["values"],
            }
        )

    return table


# ============================================================
# VALIDATION
# ============================================================

def validate_models(table):

    if table["models"] != EXPECTED_MODELS:

        raise ValueError(
            "Unexpected model list.\n"
            f"Expected: {EXPECTED_MODELS}\n"
            f"Found:    {table['models']}"
        )


def validate_rows(table):

    errors = []

    parameters = set()

    for index, row in enumerate(
        table["rows"],
        start=1,
    ):

        parameter = row["parameter"].strip()
        values = row["values"]

        # ----------------------------------------------------
        # Parameter must exist
        # ----------------------------------------------------

        if not parameter:

            errors.append(
                f"Row {index} has no parameter: {row}"
            )

        parameters.add(parameter)

        # ----------------------------------------------------
        # Values must be dict
        # ----------------------------------------------------

        if not isinstance(values, dict):

            errors.append(
                f"Row {index} has invalid values: {row}"
            )

        # ----------------------------------------------------
        # Model keys must be valid
        # ----------------------------------------------------

        for key in values:

            if not is_model_key(key):

                errors.append(
                    f"Row {index} has invalid model key "
                    f"'{key}': {row}"
                )

    if errors:

        raise ValueError(
            "\n".join(errors)
        )

    return parameters


# ============================================================
# REQUIRED PARAMETERS
# ============================================================

REQUIRED_PARAMETERS = {
    "Max. PV Input Power (kW)",
    "Max. PV Input Voltage (V)",
    "Start-up Voltage (V)",
    "MPPT Voltage Range (V)",
    "Rated PV Input Voltage (V)",
    "Max. Operating PV Input Current (A)",
    "Max. Input Short Circuit Current (A)",
    "No. of MPP Trackers/No. of Strings per MPP Tracker",
    "Rated AC Output Active Power (kW)",
    "Max. AC Output Apparent Power (kVA)",
    "Rated AC Output Current (A)",
    "Max. AC Output Current (A)",
    "Rated Output Voltage/Range (V)",
    "Grid Connection Form",
    "Rated Output Grid Frequency/Range(Hz)",
    "Power Factor Adjustment Range",
    "Total Current Harmonic Distortion THDi",
    "DC Injection Current",
    "Max. Efficiency",
    "Euro Efficiency",
    "MPPT Efficiency",
    "DC Polarity Reverse Connection Protection",
    "AC Output Overcurrent Protection",
    "AC Output Overvoltage Protection",
    "AC Output Short Circuit Protection",
    "Thermal Protection",
    "DC Terminal Insulation Impedance Monitoring",
    "DC Component Monitoring",
    "Ground Fault Current Monitoring",
    "Power Network Monitoring",
    "Island Protection Monitoring",
    "Earth Fault Detection",
    "Overvoltage Load Drop Protection",
    "Residual Current (RCD) Detection",
    "Surge Protection Level",
    "Communication Interface",
    "Operating Temperature Range (°C)",
    "Permissible Ambient Humidity",
    "Permissible Altitude (m)",
    "Noise (dB)",
    "Ingress Protection(IP) Rating",
    "Inverter Topology",
    "Cabinet Size (WxHxD mm)",
    "Weight (kg)",
    "Warranty",
    "Type of Cooling",
    "Safety EMC/Standard",
}


# ============================================================
# VALIDATE REQUIRED PARAMETERS
# ============================================================

def validate_required_parameters(table):

    parameters = {
        row["parameter"]
        for row in table["rows"]
    }

    missing = (
        REQUIRED_PARAMETERS
        - parameters
    )

    if missing:

        print()
        print("=" * 100)
        print("WARNING: REQUIRED PARAMETERS MISSING")
        print("=" * 100)

        for parameter in sorted(missing):
            print(
                f"  - {parameter}"
            )

        print()


# ============================================================
# VALIDATE EMPTY VALUES
# ============================================================

def validate_empty_values(table):

    empty_rows = []

    for index, row in enumerate(
        table["rows"],
        start=1,
    ):

        if not row["values"]:

            empty_rows.append(
                (
                    index,
                    row["parameter"],
                )
            )

    if empty_rows:

        print()
        print("=" * 100)
        print("WARNING: ROWS WITH NO VALUES")
        print("=" * 100)

        for index, parameter in empty_rows:

            print(
                f"  Row {index}: {parameter}"
            )

        print()

        return False

    return True


# ============================================================
# FULL VALIDATION
# ============================================================

def validate_table(table):

    validate_models(
        table
    )

    validate_rows(
        table
    )

    validate_required_parameters(
        table
    )

    validate_empty_values(
        table
    )


# ============================================================
# PRINT TABLE
# ============================================================

def print_table(table):

    print()
    print("=" * 100)
    print("PARSED SOURCE 2 TABLE")
    print("=" * 100)

    print()
    print("Models:")
    print("-" * 100)

    for model in table["models"]:
        print(model)

    for row in table["rows"]:

        print()
        print("=" * 100)

        print(
            f"Y         : {row['y']}"
        )

        print(
            f"Parameter : {row['parameter']}"
        )

        print(
            f"Type      : {row['type']}"
        )

        print("-" * 100)

        values = row["values"]

        if not values:

            print("(no values)")
            continue

        for key, value in values.items():

            if isinstance(value, list):

                value = ", ".join(
                    str(item)
                    for item in value
                )

            print(
                f"{key} -> {value}"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("SOURCE 2 TABLE PARSER")
    print("=" * 100)

    print()
    print(
        f"Input : {INPUT_PATH}"
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )

    print()

    # --------------------------------------------------------
    # Load layout-parser output
    # --------------------------------------------------------

    parsed_data = load_json(
        INPUT_PATH
    )

    # --------------------------------------------------------
    # Build normalized table
    # --------------------------------------------------------

    table = build_table(
        parsed_data
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_table(
        table
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_json(
        OUTPUT_PATH,
        table
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print_table(
        table
    )

    print()
    print("=" * 100)
    print(
        f"Parsed table saved to: {OUTPUT_PATH}"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()