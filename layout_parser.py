from pathlib import Path
import json
import re
from itertools import combinations


# ============================================================
# 1. PATHS
# ============================================================

INPUT_PATH = Path(
    r"D:\ai-assessment\data\extracted\source_2.json"
)

OUTPUT_PATH = Path(
    r"D:\ai-assessment\data\parsed\source_2.json"
)


# ============================================================
# 2. SOURCE 2 MODEL DEFINITIONS
# ============================================================

MODELS = [
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
# 3. SOURCE 2 SECTION HEADERS
# ============================================================

SECTION_HEADERS = {
    "Technical Data",
    "PV String Input Data",
    "AC Output Side",
    "Efficiency",
    "Equipment Protection",
    "Interface",
    "General Data",
    "Grid Regulation",
}


# ============================================================
# 4. PARAMETERS THAT ARE KNOWN TO HAVE CONTINUATION LINES
# ============================================================

KNOWN_PARAMETERS = {
    "No. of MPP Trackers/ No. of Strings per MPP Tracker",
    "Power Factor Adjustment Range",
    "Operating Temperature Range (°C)",
    "Type of Cooling",
    "Safety EMC/Standard",
}


# ============================================================
# 5. FOOTER / NON-TABLE CONTENT
# ============================================================

IGNORED_PARAMETER_PREFIXES = (
    "Ningbo Deye Inverter",
    "Add:",
    "Tel:",
    "E-mail:",
    "Stock Code:",
    "Technical Data www.",
)


# ============================================================
# 6. LOAD EXTRACTED PDF
# ============================================================

def load_extracted_pdf(json_path: Path) -> list:
    """
    Load word-level PDF extraction data.
    """

    if not json_path.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{json_path}"
        )

    with json_path.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# 7. TEXT NORMALIZATION
# ============================================================

def clean_text(text):
    """
    Normalize PDF text while preserving technical notation.
    """

    if text is None:
        return ""

    text = str(text).strip()

    # PDF ligatures / extraction artifacts
    text = text.replace("ﬁ", "fi")
    text = text.replace("ﬃ", "ffi")
    text = text.replace("ﬂ", "fl")

    # Normalize dashes
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Normalize multiplication symbols
    text = text.replace("×", "×")

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# 8. WORD POSITION HELPERS
# ============================================================

def word_x0(word):
    return float(
        word["x0"]
    )


def word_x1(word):
    return float(
        word.get(
            "x1",
            word["x0"]
        )
    )


def word_center_x(word):
    return (
        word_x0(word)
        +
        word_x1(word)
    ) / 2.0


def word_y(word):
    return float(
        word["y0"]
    )


# ============================================================
# 9. GROUP WORDS INTO STRICT VISUAL ROWS
# ============================================================

def group_words_into_rows(
    words,
    y_tolerance=3
):
    """
    Group words that belong to the SAME physical PDF line.

    IMPORTANT:
    We deliberately use a relatively small tolerance.

    Source 2 has normal table rows approximately 11-12 pixels
    apart, while words belonging to the same physical line have
    nearly identical Y coordinates.

    A larger tolerance can incorrectly merge:

        Weight
        Operating Temperature Range

    or:

        Natural Cooling
        Warranty
    """

    rows = []

    sorted_words = sorted(
        words,
        key=lambda w: (
            word_y(w),
            word_x0(w)
        )
    )

    for word in sorted_words:

        y = word_y(word)

        matched_row = None

        # Find the closest existing row.
        closest_distance = float("inf")

        for row in rows:

            distance = abs(
                y - row["y"]
            )

            if (
                distance <= y_tolerance
                and
                distance < closest_distance
            ):
                closest_distance = distance
                matched_row = row

        if matched_row is None:

            rows.append(
                {
                    "y": y,
                    "words": [word]
                }
            )

        else:

            matched_row["words"].append(
                word
            )

            # IMPORTANT:
            # Do NOT continuously update the row Y based on every
            # added word. That can cause rows to drift together.
            #
            # Keep the original representative Y.

    # --------------------------------------------------------
    # Sort words horizontally
    # --------------------------------------------------------

    for row in rows:

        row["words"].sort(
            key=lambda w: (
                word_y(w),
                word_x0(w)
            )
        )

    # --------------------------------------------------------
    # Sort rows vertically
    # --------------------------------------------------------

    rows.sort(
        key=lambda r: r["y"]
    )

    return rows


# ============================================================
# 10. DETECT MODEL COLUMNS
# ============================================================

def detect_model_columns(page):
    """
    Detect the eight Source 2 model columns.
    """

    detected = []

    for word in page["words"]:

        text = clean_text(
            word["text"]
        )

        if MODEL_PATTERN.fullmatch(text):

            detected.append(
                {
                    "model": text,
                    "x": word_center_x(word)
                }
            )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    unique = {}

    for item in detected:

        unique[item["model"]] = item

    detected = list(
        unique.values()
    )

    # --------------------------------------------------------
    # Sort visually
    # --------------------------------------------------------

    detected.sort(
        key=lambda item: item["x"]
    )

    return detected


# ============================================================
# 11. MODEL SUFFIX DETECTION
# ============================================================

def is_model_suffix_row(row):
    """
    Detect the '-EU-AM2' continuation line below the model names.
    """

    texts = [
        clean_text(
            word["text"]
        )
        for word in row["words"]
    ]

    texts = [
        text
        for text in texts
        if text
    ]

    if not texts:
        return False

    return all(
        text == "-EU-AM2"
        for text in texts
    )


# ============================================================
# 12. LEFT-SIDE WORDS
# ============================================================

def get_left_words(
    row,
    first_model_x
):
    """
    Return words before the model/value area.
    """

    return [
        word
        for word in row["words"]
        if word_x0(word) < first_model_x
    ]


# ============================================================
# 13. GET PARAMETER TEXT FROM ONE PHYSICAL ROW
# ============================================================

def get_left_text(
    row,
    first_model_x
):
    """
    Extract parameter text from the left side of one row.
    """

    words = get_left_words(
        row,
        first_model_x
    )

    if not words:
        return ""

    words = sorted(
        words,
        key=lambda w: (
            word_y(w),
            word_x0(w)
        )
    )

    text = " ".join(
        clean_text(
            word["text"]
        )
        for word in words
    )

    return clean_text(
        text
    )


# ============================================================
# 14. VALUE-WORD DETECTION
# ============================================================

def looks_like_value_word(text):
    """
    Determine whether a word belongs to a technical value.

    This is intentionally broader than the previous is_value()
    function.

    We do NOT require every individual word to be numeric.

    Examples of valid value words:

        0.8
        leading
        to
        lagging
        Natural
        Cooling
        -25
        +60℃,
        Derating
        IEC
        61727,
        G99,
        4105
    """

    text = clean_text(text)

    if not text:
        return False

    # Explicit textual value words.
    if text in {
        "Yes",
        "No",
        "Natural",
        "Cooling",
        "Non-Isolated",
        "Derating",
        "leading",
        "lagging",
        "to",
        "TYPE",
        "II(DC),",
        "II(AC)",
    }:
        return True

    # Anything containing a number.
    if re.search(
        r"\d",
        text
    ):
        return True

    # Technical standard words.
    if re.fullmatch(
        r"[A-Za-z]+(?:/[A-Za-z0-9]+)*,?",
        text
    ):
        return True

    return False


# ============================================================
# 15. EXTRACT VALUE REGIONS
# ============================================================

def extract_value_regions(
    row,
    models
):
    """
    Extract complete value expressions from a physical row.

    Instead of treating each PDF word as an independent value,
    words are grouped into horizontal value regions.

    Example:

        0.8 leading to 0.8 lagging

    becomes ONE value.

    Likewise:

        Natural Cooling

    becomes ONE value.

    And:

        -25 to +60℃, >45℃ Derating

    becomes ONE value.
    """

    if not models:
        return []

    first_model_x = models[0]["x"]

    candidate_words = []

    for word in row["words"]:

        if word_x0(word) < first_model_x:
            continue

        text = clean_text(
            word["text"]
        )

        if not text:
            continue

        if not looks_like_value_word(
            text
        ):
            continue

        candidate_words.append(
            word
        )

    if not candidate_words:
        return []

    candidate_words.sort(
        key=word_center_x
    )

    # --------------------------------------------------------
    # Group horizontally adjacent words.
    #
    # The PDF's words within one value expression are close
    # together. Large gaps generally indicate separate cells.
    # --------------------------------------------------------

    regions = []

    current = [
        candidate_words[0]
    ]

    for word in candidate_words[1:]:

        previous = current[-1]

        gap = (
            word_x0(word)
            -
            word_x1(previous)
        )

        # Normal textual spacing is small.
        #
        # A large gap generally indicates a new model/cell.
        #
        # 30 px is deliberately conservative for this PDF.
        if gap <= 30:

            current.append(
                word
            )

        else:

            regions.append(
                current
            )

            current = [
                word
            ]

    regions.append(
        current
    )

    # --------------------------------------------------------
    # Build complete value objects
    # --------------------------------------------------------

    values = []

    for region in regions:

        region = sorted(
            region,
            key=word_center_x
        )

        text = " ".join(
            clean_text(
                word["text"]
            )
            for word in region
        )

        text = clean_text(
            text
        )

        if not text:
            continue

        x0 = min(
            word_x0(word)
            for word in region
        )

        x1 = max(
            word_x1(word)
            for word in region
        )

        values.append(
            {
                "text": text,
                "x": (x0 + x1) / 2.0,
                "x0": x0,
                "x1": x1,
                "y": min(
                    word_y(word)
                    for word in region
                )
            }
        )

    values.sort(
        key=lambda value: value["x"]
    )

    return values


# ============================================================
# 16. SECTION HEADER DETECTION
# ============================================================

def is_section_header(parameter):
    """
    Identify structural headings.
    """

    return parameter in SECTION_HEADERS


# ============================================================
# 17. IGNORE NON-TABLE ROWS
# ============================================================

def should_ignore_row(
    row,
    parameter
):
    """
    Determine whether a physical row is structural/footer
    content.
    """

    parameter = clean_text(
        parameter
    )

    if is_model_suffix_row(
        row
    ):
        return True

    if is_section_header(
        parameter
    ):
        return True

    for prefix in IGNORED_PARAMETER_PREFIXES:

        if parameter.startswith(
            prefix
        ):
            return True

    return False


# ============================================================
# 18. NEAREST MODEL
# ============================================================

def nearest_model(
    value_x,
    models
):
    """
    Return the nearest model column.
    """

    return min(
        models,
        key=lambda model:
        abs(
            value_x
            -
            model["x"]
        )
    )


# ============================================================
# 19. MAP ONE VALUE PER MODEL
# ============================================================

def map_model_row(
    values,
    models
):
    """
    Map one value to each model.
    """

    result = {}

    for value in values:

        model = nearest_model(
            value["x"],
            models
        )

        result[
            model["model"]
        ] = value["text"]

    return result


# ============================================================
# 20. GROUPED VALUE MAPPING
# ============================================================

def calculate_group_center(
    models,
    start,
    end
):
    """
    Calculate visual center of a contiguous model group.
    """

    group = models[
        start:end
    ]

    return sum(
        model["x"]
        for model in group
    ) / len(group)


def grouped_mapping_cost(
    values,
    models,
    split_points
):
    """
    Calculate the visual grouping cost.
    """

    boundaries = (
        [0]
        +
        list(split_points)
        +
        [len(models)]
    )

    cost = 0.0

    for i, value in enumerate(values):

        start = boundaries[i]
        end = boundaries[i + 1]

        center = calculate_group_center(
            models,
            start,
            end
        )

        distance = (
            value["x"]
            -
            center
        )

        cost += distance ** 2

    return cost


def find_best_grouping(
    values,
    models
):
    """
    Find the most likely contiguous model groups.
    """

    value_count = len(
        values
    )

    model_count = len(
        models
    )

    if value_count == 0:
        return []

    if value_count == 1:

        return [
            (
                0,
                model_count
            )
        ]

    if value_count > model_count:
        return []

    best_split = None
    best_cost = float(
        "inf"
    )

    for split_points in combinations(
        range(
            1,
            model_count
        ),
        value_count - 1
    ):

        cost = grouped_mapping_cost(
            values,
            models,
            split_points
        )

        if cost < best_cost:

            best_cost = cost
            best_split = split_points

    if best_split is None:
        return []

    boundaries = (
        [0]
        +
        list(best_split)
        +
        [model_count]
    )

    return [
        (
            boundaries[i],
            boundaries[i + 1]
        )
        for i in range(
            value_count
        )
    ]


def map_grouped_row(
    values,
    models
):
    """
    Map values to contiguous model groups.
    """

    if not values or not models:
        return {}

    values = sorted(
        values,
        key=lambda value:
        value["x"]
    )

    if len(values) == 1:

        return {
            "ALL_MODELS":
                values[0]["text"]
        }

    groups = find_best_grouping(
        values,
        models
    )

    if not groups:
        return {}

    result = {}

    for value, (
        start,
        end
    ) in zip(
        values,
        groups
    ):

        group_models = models[
            start:end
        ]

        if not group_models:
            continue

        model_names = [
            model["model"]
            for model in group_models
        ]

        result[
            ", ".join(model_names)
        ] = value["text"]

    return result


# ============================================================
# 21. CLASSIFY ROW
# ============================================================

def classify_row(
    values,
    models
):
    """
    Classify the number of value regions.
    """

    value_count = len(
        values
    )

    model_count = len(
        models
    )

    if value_count == 0:
        return "no_values"

    if value_count == 1:
        return "common_value"

    if value_count == model_count:
        return "model_row"

    return "grouped_row"


# ============================================================
# 22. MERGE CONTINUATION ROWS
# ============================================================

def merge_continuation_rows(
    rows,
    models
):
    """
    Merge physical PDF lines that belong to one logical table row.

    This handles cases such as:

        No. of MPP Trackers/
        No. of Strings per MPP Tracker

    and:

        Safety EMC/Standard
        OVE-Richtlinie R25, G99, VDE-AR-N 4105

    and multi-line technical values.

    The function works conservatively:

    - It does NOT merge ordinary adjacent table rows.
    - It only merges rows when the parameter/value structure
      strongly indicates continuation.
    """

    if not rows:
        return []

    merged = []

    i = 0

    while i < len(rows):

        current = rows[i]

        parameter = clean_text(
            current.get(
                "parameter",
                ""
            )
        )

        # ----------------------------------------------------
        # Known wrapped parameter:
        #
        # No. of MPP Trackers/
        # No. of Strings per MPP Tracker
        # ----------------------------------------------------

        if (
            parameter
            ==
            "No. of MPP Trackers/"
            and
            i + 1 < len(rows)
        ):

            next_row = rows[i + 1]

            next_parameter = clean_text(
                next_row.get(
                    "parameter",
                    ""
                )
            )

            if (
                next_parameter
                ==
                "No. of Strings per MPP Tracker"
            ):

                current["parameter"] = (
                    "No. of MPP Trackers/ "
                    "No. of Strings per MPP Tracker"
                )

                # Keep the values from the first physical row.
                # The second physical row has no model values
                # in the actual table.
                i += 2

                merged.append(
                    current
                )

                continue

        # ----------------------------------------------------
        # Safety/EMC continuation
        #
        # The standard list can wrap across physical lines.
        # ----------------------------------------------------

        if (
            parameter
            ==
            "Safety EMC/Standard"
        ):

            combined_values = []

            # Current row values
            if current.get("values"):
                combined_values.extend(
                    current["values"].items()
                )

            j = i + 1

            while j < len(rows):

                candidate = rows[j]

                candidate_parameter = clean_text(
                    candidate.get(
                        "parameter",
                        ""
                    )
                )

                candidate_values = candidate.get(
                    "values",
                    {}
                )

                # Continuation lines have no parameter text
                # and contain standard-like values.
                if (
                    not candidate_parameter
                    and
                    candidate_values
                ):

                    combined_values.extend(
                        candidate_values.items()
                    )

                    j += 1

                else:
                    break

            # Rebuild grouped values by model-group key.
            #
            # If continuation values belong to the same group,
            # concatenate them.
            result_values = {}

            for key, value in combined_values:

                if key in result_values:

                    result_values[key] = (
                        result_values[key]
                        + " "
                        + value
                    )

                else:

                    result_values[key] = value

            current["values"] = result_values

            i = j

            merged.append(
                current
            )

            continue

        # ----------------------------------------------------
        # Default:
        # keep row unchanged.
        # ----------------------------------------------------

        merged.append(
            current
        )

        i += 1

    return merged


# ============================================================
# 23. PARSE ONE PHYSICAL ROW
# ============================================================

def parse_physical_row(
    row,
    models
):
    """
    Parse one physical PDF row.
    """

    if not models:

        return {
            "y": round(
                row["y"],
                2
            ),
            "type": "no_values",
            "parameter": "",
            "values": {}
        }

    first_model_x = models[0]["x"]

    parameter = get_left_text(
        row,
        first_model_x
    )

    if should_ignore_row(
        row,
        parameter
    ):
        return None

    values = extract_value_regions(
        row,
        models
    )

    row_type = classify_row(
        values,
        models
    )

    # --------------------------------------------------------
    # No values
    # --------------------------------------------------------

    if row_type == "no_values":

        return {
            "y": round(
                row["y"],
                2
            ),
            "type": "no_values",
            "parameter": parameter,
            "values": {}
        }

    # --------------------------------------------------------
    # Common value
    # --------------------------------------------------------

    if row_type == "common_value":

        return {
            "y": round(
                row["y"],
                2
            ),
            "type": "common_value",
            "parameter": parameter,
            "values": {
                "ALL_MODELS":
                    values[0]["text"]
            }
        }

    # --------------------------------------------------------
    # One value per model
    # --------------------------------------------------------

    if row_type == "model_row":

        return {
            "y": round(
                row["y"],
                2
            ),
            "type": "model_row",
            "parameter": parameter,
            "values": map_model_row(
                values,
                models
            )
        }

    # --------------------------------------------------------
    # Grouped values
    # --------------------------------------------------------

    if row_type == "grouped_row":

        return {
            "y": round(
                row["y"],
                2
            ),
            "type": "grouped_row",
            "parameter": parameter,
            "values": map_grouped_row(
                values,
                models
            )
        }

    return {
        "y": round(
            row["y"],
            2
        ),
        "type": "unknown",
        "parameter": parameter,
        "values": {}
    }


# ============================================================
# 24. PARSE SOURCE 2 TABLE PAGE
# ============================================================

def parse_table_page(page):
    """
    Parse page 2 of Source 2.
    """

    models = detect_model_columns(
        page
    )

    # --------------------------------------------------------
    # Validate models
    # --------------------------------------------------------

    detected_names = [
        model["model"]
        for model in models
    ]

    expected_names = MODELS

    if detected_names != expected_names:

        raise ValueError(
            "\n"
            "Source 2 model detection failed.\n"
            f"Expected:\n{expected_names}\n"
            f"Detected:\n{detected_names}\n"
        )

    # --------------------------------------------------------
    # Group physical PDF lines
    # --------------------------------------------------------

    physical_rows = group_words_into_rows(
        page["words"],
        y_tolerance=3
    )

    # --------------------------------------------------------
    # Parse each physical row
    # --------------------------------------------------------

    parsed_rows = []

    for row in physical_rows:

        parsed = parse_physical_row(
            row,
            models
        )

        if parsed is None:
            continue

        parsed_rows.append(
            parsed
        )

    # --------------------------------------------------------
    # Merge logical continuation rows
    # --------------------------------------------------------

    parsed_rows = merge_continuation_rows(
        parsed_rows,
        models
    )

    return models, parsed_rows


# ============================================================
# 25. PRINT MODELS
# ============================================================

def print_models(
    models
):

    print()
    print("=" * 100)
    print("MODELS")
    print("=" * 100)

    for model in models:

        print(
            f"{model['model']:20} "
            f"x={model['x']:.2f}"
        )


# ============================================================
# 26. PRINT PARSED TABLE
# ============================================================

def print_parsed_table(
    models,
    rows
):

    print_models(
        models
    )

    for row in rows:

        if row["type"] == "no_values":
            continue

        print()
        print("=" * 100)

        print(
            f"Y         : "
            f"{row['y']:.2f}"
        )

        print(
            f"Parameter : "
            f"{row['parameter']}"
        )

        print(
            f"Type      : "
            f"{row['type']}"
        )

        print("-" * 100)

        for key, value in row["values"].items():

            print(
                f"{key} -> {value}"
            )


# ============================================================
# 27. BUILD OUTPUT
# ============================================================

def build_output(
    models,
    rows
):
    """
    Build final parsed JSON.
    """

    return {
        "source": "source_2",
        "page": 2,
        "models": [
            model["model"]
            for model in models
        ],
        "rows": rows
    }


# ============================================================
# 28. SAVE OUTPUT
# ============================================================

def save_output(
    output_path,
    data
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
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
# 29. MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("SOURCE 2 LAYOUT PARSER")
    print("=" * 100)

    print(
        f"Input : {INPUT_PATH}"
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )

    # --------------------------------------------------------
    # Load extracted PDF
    # --------------------------------------------------------

    pages = load_extracted_pdf(
        INPUT_PATH
    )

    if len(pages) < 2:

        raise ValueError(
            "source_2.json does not contain page 2."
        )

    # Python index 1 = PDF page 2
    page = pages[1]

    # --------------------------------------------------------
    # Parse
    # --------------------------------------------------------

    models, rows = parse_table_page(
        page
    )

    # --------------------------------------------------------
    # Build output
    # --------------------------------------------------------

    parsed_data = build_output(
        models,
        rows
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_output(
        OUTPUT_PATH,
        parsed_data
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print_parsed_table(
        models,
        rows
    )

    print()
    print("=" * 100)

    print(
        f"Parsed JSON saved to: "
        f"{OUTPUT_PATH}"
    )

    print("=" * 100)


# ============================================================
# 30. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()