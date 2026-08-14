from pathlib import Path
import json


# ============================================================
# 1. LOAD NORMALIZED JSON
# ============================================================

def load_normalized_json(json_path: Path) -> dict:

    print()
    print("=" * 100)
    print("LOADING NORMALIZED TABLE")
    print("=" * 100)
    print(f"Input: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 2. VALIDATE MODELS
# ============================================================

def validate_models(data):

    models = data.get("models", [])

    errors = []
    warnings = []

    if not models:
        errors.append("No models found.")

    if len(models) != len(set(models)):
        errors.append("Duplicate model names found.")

    for model in models:
        if not isinstance(model, str) or not model.strip():
            errors.append("Invalid model name found.")

    return errors, warnings


# ============================================================
# 3. VALIDATE ROWS
# ============================================================

def validate_rows(data):

    models = data.get("models", [])
    rows = data.get("rows", [])

    errors = []
    warnings = []

    if not rows:
        errors.append("No rows found.")

    seen_y = set()

    for i, row in enumerate(rows):

        y = row.get("y")
        parameter = row.get("parameter", "")
        values = row.get("values", {})

        # ----------------------------------------------------
        # Check Y
        # ----------------------------------------------------

        if y is None:
            errors.append(
                f"Row {i}: missing Y coordinate."
            )

        elif y in seen_y:
            warnings.append(
                f"Row {i}: duplicate Y coordinate: {y}"
            )

        else:
            seen_y.add(y)

        # ----------------------------------------------------
        # Check parameter
        # ----------------------------------------------------

        if not parameter or not parameter.strip():

            warnings.append(
                f"Row {i}: missing parameter name "
                f"(Y = {y})."
            )

        # ----------------------------------------------------
        # Check values
        # ----------------------------------------------------

        if not isinstance(values, dict):

            errors.append(
                f"Row {i}: values is not a dictionary."
            )

            continue

        # ----------------------------------------------------
        # Check every model
        # ----------------------------------------------------

        for model in models:

            if model not in values:

                errors.append(
                    f"Row {i}: missing value for "
                    f"{model} (Y = {y})."
                )

            elif values[model] is None:

                warnings.append(
                    f"Row {i}: None value for "
                    f"{model} (Y = {y})."
                )

        # ----------------------------------------------------
        # Check for unknown models
        # ----------------------------------------------------

        for model in values:

            if model not in models:

                warnings.append(
                    f"Row {i}: unknown model "
                    f"'{model}'."
                )

    return errors, warnings


# ============================================================
# 4. CHECK SUSPICIOUS ROWS
# ============================================================

def check_suspicious_rows(data):

    warnings = []

    for row in data.get("rows", []):

        y = row.get("y")
        parameter = row.get("parameter", "")
        values = row.get("values", {})

        # ----------------------------------------------------
        # Missing parameter
        # ----------------------------------------------------

        if not parameter.strip():

            warnings.append(
                f"Suspicious row: Y = {y} has no parameter name."
            )

        # ----------------------------------------------------
        # Suspicious 4105 artifact
        # ----------------------------------------------------

        if any(
            str(value).strip() == "4105"
            for value in values.values()
        ):

            warnings.append(
                f"Possible extraction artifact: "
                f"Y = {y}, value = 4105."
            )

    return warnings


# ============================================================
# 5. PRINT VALIDATION REPORT
# ============================================================

def print_report(data, errors, warnings):

    print()
    print("=" * 100)
    print("VALIDATION REPORT")
    print("=" * 100)

    print(
        f"Models: {len(data.get('models', []))}"
    )

    print(
        f"Rows: {len(data.get('rows', []))}"
    )

    print()

    if errors:

        print("ERRORS")
        print("-" * 80)

        for error in errors:
            print(f"✗ {error}")

    else:

        print("ERRORS")
        print("-" * 80)
        print("✓ No errors found.")

    print()

    if warnings:

        print("WARNINGS")
        print("-" * 80)

        for warning in warnings:
            print(f"⚠ {warning}")

    else:

        print("WARNINGS")
        print("-" * 80)
        print("✓ No warnings found.")

    print()

    print("=" * 100)

    if errors:

        print("VALIDATION STATUS: FAILED")

    elif warnings:

        print("VALIDATION STATUS: PASSED WITH WARNINGS")

    else:

        print("VALIDATION STATUS: PASSED")

    print("=" * 100)


# ============================================================
# 6. MAIN
# ============================================================

if __name__ == "__main__":

    input_path = Path(
        "data/normalized/source_2.json"
    )

    data = load_normalized_json(
        input_path
    )

    # Validate models
    model_errors, model_warnings = validate_models(
        data
    )

    # Validate rows
    row_errors, row_warnings = validate_rows(
        data
    )

    # Check suspicious rows
    suspicious_warnings = check_suspicious_rows(
        data
    )

    # Combine results
    errors = (
        model_errors
        + row_errors
    )

    warnings = (
        model_warnings
        + row_warnings
        + suspicious_warnings
    )

    # Print report
    print_report(
        data,
        errors,
        warnings
    )