from pathlib import Path
import json


# Load normalized JSON

def load_normalized_json(json_path: Path) -> dict:

    print()
    print("=" * 100)
    print("LOADING NORMALIZED TABLE")
    print("=" * 100)
    print(f"Input: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# Validate models

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


# Validate parameters
def validate_parameters(data):

    models = data.get("models", [])
    parameters = data.get("parameters", {})

    errors = []
    warnings = []

    if not parameters:
        errors.append("No parameters found.")

    if not isinstance(parameters, dict):
        errors.append("'parameters' is not a dictionary.")
        return errors, warnings

    for parameter, values in parameters.items():

        if not parameter or not str(parameter).strip():
            warnings.append("Found a blank parameter name.")

        if not isinstance(values, dict):
            errors.append(
                f"Parameter '{parameter}': values is not "
                f"a dictionary."
            )
            continue

        # Every declared model should have an entry (even if
        # the value itself is None / not established).

        for model in models:

            if model not in values:

                errors.append(
                    f"Parameter '{parameter}': missing entry "
                    f"for model '{model}'."
                )

            elif values[model] is None:

                warnings.append(
                    f"Parameter '{parameter}': no value for "
                    f"model '{model}' (null after normalization)."
                )

        # Flag keys that aren't declared models at all.

        for model in values:

            if model not in models:

                warnings.append(
                    f"Parameter '{parameter}': unknown model "
                    f"key '{model}'."
                )

    return errors, warnings


# Check suspicious values

def check_suspicious_values(data):

    warnings = []

    parameters = data.get("parameters", {})

    if not isinstance(parameters, dict):
        return warnings

    for parameter, values in parameters.items():

        if not isinstance(values, dict):
            continue

        for model, value in values.items():
            if str(value).strip() == "4105":

                warnings.append(
                    f"Possible extraction artifact: "
                    f"parameter='{parameter}', model='{model}', "
                    f"value='4105'."
                )

    return warnings


# Print validation report

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


#  VALIDATE ONE NORMALIZED SOURCE

def validate_source(source_id: str, verbose: bool = True):
    """
    Validate data/normalized/{source_id}.json.

    Returns (errors, warnings). Does not raise on errors -- the
    caller decides whether to treat them as fatal. This mirrors how
    main.py wants to keep going and surface problems in the report
    rather than crash the whole pipeline over one dirty field.
    """

    input_path = Path(f"data/normalized/{source_id}.json")

    data = load_normalized_json(input_path) if verbose else json.loads(
        input_path.read_text(encoding="utf-8")
    )

    model_errors, model_warnings = validate_models(data)
    param_errors, param_warnings = validate_parameters(data)
    suspicious_warnings = check_suspicious_values(data)

    errors = model_errors + param_errors
    warnings = model_warnings + param_warnings + suspicious_warnings

    if verbose:
        print_report(data, errors, warnings)

    return errors, warnings


# CLI ENTRY POINT

if __name__ == "__main__":

    import sys

    source_id = sys.argv[1] if len(sys.argv) > 1 else "source_1"
    validate_source(source_id)