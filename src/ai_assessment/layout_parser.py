import json
import re
from pathlib import Path


# CONFIGURATION
ROW_TOL = 3.0
LABEL_MAX_X = 180.0
MERGE_GAP = 10.0


# LOAD EXTRACTED PDF DATA
def load_extracted_words(path: Path):
    """
    Load word-level data produced by pdf_extractor.py.

    Expected structure:

    [
        {
            "page": 1,
            "width": ...,
            "height": ...,
            "words": [
                {
                    "text": "...",
                    "x0": ...,
                    "x1": ...,
                    "top": ...,
                    "bottom": ...
                }
            ]
        }
    ]
    """

    with path.open("r", encoding="utf-8") as f:
        pages = json.load(f)

    return pages


EXPECTED_MODEL_COLUMNS = 8


def get_relevant_page(pages):

    best_page = None
    best_count = 0

    for page in pages:

        words = page["words"]

        model_words = [
            word
            for word in words
            if word["text"].startswith("SUN-")
        ]

        if len(model_words) > best_count:
            best_count = len(model_words)
            best_page = page

    if best_page is None or best_count < 2:
        raise ValueError(
            "Could not find a page containing a multi-model "
            "table header (no page had more than one 'SUN-' "
            "prefixed word)."
        )

    if best_count != EXPECTED_MODEL_COLUMNS:
        print(
            f"WARNING: expected {EXPECTED_MODEL_COLUMNS} model "
            f"columns (this pipeline's known document layout), "
            f"found {best_count} on the best-matching page "
            f"(page {best_page.get('page')}). Proceeding, but "
            f"verify the extracted table against the source PDF."
        )

    return best_page


# ROW CLUSTERING
def cluster_rows(words, tolerance=ROW_TOL):

    words = sorted(
        words,
        key=lambda word: (
            word["top"],
            word["x0"],
        ),
    )

    rows = []

    current_row = []
    current_top = None

    for word in words:

        if current_top is None:

            current_row = [word]
            current_top = word["top"]

            continue

        if abs(word["top"] - current_top) <= tolerance:

            current_row.append(word)

        else:

            rows.append(current_row)

            current_row = [word]
            current_top = word["top"]

    if current_row:
        rows.append(current_row)

    return rows


# FIND MODEL HEADER

def find_header(rows):
    """
    Find the row containing the eight model columns.

    Expected models:

        SUN-4K-G06P3
        SUN-5K-G06P3
        SUN-6K-G06P3
        SUN-7K-G06P3
        SUN-8K-G06P3
        SUN-10K-G06P3
        SUN-12K-G06P3
        SUN-15K-G06P3
    """

    for row in rows:

        model_tokens = [
            word
            for word in row
            if word["text"].startswith("SUN-")
        ]

        if len(model_tokens) == 8:

            model_tokens = sorted(
                model_tokens,
                key=lambda word: word["x0"],
            )

            return model_tokens

    raise ValueError(
        "Could not find the 8-column model header."
    )


# MODEL COLUMN CENTERS

def build_column_bins(header_tokens):
    """
    Build the model-column map from the actual PDF header.

    We use the horizontal center of each model header as the
    anchor for assigning values below it.
    """

    model_names = [
        token["text"]
        for token in header_tokens
    ]

    centers = [
        (token["x0"] + token["x1"]) / 2
        for token in header_tokens
    ]

    return model_names, centers


# NEAREST MODEL COLUMN

def nearest_column(x, centers):
    """
    Find the model column whose center is closest to x.
    """

    distances = [
        abs(x - center)
        for center in centers
    ]

    index = distances.index(min(distances))

    return index, min(distances)


# NUMERIC / TECHNICAL TOKEN DETECTION

def is_numeric_token(text):
    """
    Determine whether a token looks like a technical/numeric value.

    Examples:

        5
        5.5
        98.2%
        13+13
        600V
        <0.5%
        3L/N/PE
    """

    pattern = r"^[<>]?[\d./%+~\-]+[a-zA-Z%]*$"

    return bool(re.match(pattern, text))


# MERGE WRAPPED TABLE ROWS

def merge_wrapped_rows(rows):
    """
    Merge a label-only row followed by a value-only row.

    Some PDF tables wrap long labels onto one visual line and
    place the corresponding values on the next visual line.

    Example:

        Long technical specification label
                                      5  5  5  5 ...

    becomes one logical row.
    """

    merged = []

    i = 0

    while i < len(rows):

        row = rows[i]

        label_words = [
            word
            for word in row
            if word["x0"] < LABEL_MAX_X
        ]

        value_words = [
            word
            for word in row
            if word["x0"] >= LABEL_MAX_X
        ]

        # Current row contains a label but no values.
        if (
            label_words
            and not value_words
            and i + 1 < len(rows)
        ):

            next_row = rows[i + 1]

            next_label_words = [
                word
                for word in next_row
                if word["x0"] < LABEL_MAX_X
            ]

            next_value_words = [
                word
                for word in next_row
                if word["x0"] >= LABEL_MAX_X
            ]

            # Following row contains values but no label.
            if (
                not next_label_words
                and next_value_words
                and (
                    next_row[0]["top"] - row[0]["top"]
                    <= MERGE_GAP
                )
            ):

                merged.append(
                    row + next_row
                )

                i += 2

                continue

        merged.append(row)

        i += 1

    return merged


# LABEL GARBLING DETECTION

def detect_label_flags(label):
    """
    Detect possible PDF text-layer corruption.

    Illustrator-generated PDFs can contain overlapping text runs
    that become character-interleaved during extraction.
    """

    flags = []

    compact_label = label.replace(" ", "")

    if re.search(
        r"[a-z][A-Z][a-z][A-Z]",
        compact_label,
    ):
        flags.append(
            "possible_interleaved_label_garbling"
        )

    return flags


# PARSE TABLE PAGE

def parse_page(page):
    """
    Parse the technical specification table on one PDF page.

    The parser does NOT assume fixed model x-coordinates.

    Instead:

        1. Find the 8 model headers.
        2. Calculate their x-coordinate centers.
        3. Cluster text into rows.
        4. Separate labels from values.
        5. Assign values to the nearest model column.
        6. Flag incomplete/spanning rows.
        7. Preserve raw values for later reconciliation.
    """

    words = page["words"]

    # CLUSTER WORDS INTO VISUAL ROWS

    rows_raw = cluster_rows(words)

    #  FIND MODEL HEADER

    header_tokens = find_header(rows_raw)

    model_names, centers = build_column_bins(
        header_tokens
    )

    header_top = min(
        token["top"]
        for token in header_tokens
    )

    #  MERGE WRAPPED LABEL ROWS

    rows = merge_wrapped_rows(rows_raw)

    #  PARSE EACH TABLE ROW

    fields = []

    for row in rows:

        top = min(
            word["top"]
            for word in row
        )

        # Ignore content above table

        if top < 70:
            continue

        # Ignore model header row

        if abs(top - header_top) <= ROW_TOL:
            continue

        # Ignore footer area
        if top > page["height"] - 40:
            continue

        # Separate label and value zones
        label_words = sorted(
            [
                word
                for word in row
                if word["x0"] < LABEL_MAX_X
            ],
            key=lambda word: word["x0"],
        )

        value_words = sorted(
            [
                word
                for word in row
                if word["x0"] >= LABEL_MAX_X
            ],
            key=lambda word: word["x0"],
        )

        # Build label
        label = " ".join(
            word["text"]
            for word in label_words
        ).strip()

        # Build value tokens
        value_tokens = [
            (
                word["text"],
                word["x0"],
            )
            for word in value_words
        ]

        # Detect parsing problems
        flags = detect_label_flags(label)

        # No value found
        if not value_tokens:

            fields.append(
                {
                    "label": label,
                    "top": top,
                    "per_model": {},
                    "raw_values": [],
                    "confidence": "no_value_found",
                    "flags": flags,
                }
            )

            continue

        # Identify numeric/technical tokens
        numeric_tokens = [
            text
            for text, _ in value_tokens
            if is_numeric_token(text)
        ]

        # Determine whether row is columnar
        is_columnar = (
            len(value_tokens) >= 2
            and len(value_tokens) <= 8
            and len(numeric_tokens) == len(value_tokens)
        )

        # COLUMNAR VALUES
        if is_columnar:

            per_model = {}

            used_columns = set()

            for text, x in value_tokens:

                column_index, distance = nearest_column(
                    x,
                    centers,
                )

                # Detect two values assigned to same column
                if column_index in used_columns:

                    flags.append(
                        f"column_collision_at_x={x}"
                    )

                used_columns.add(column_index)

                model = model_names[column_index]

                per_model[model] = {
                    "value": text,
                    "col_dist_pts": round(
                        distance,
                        1,
                    ),
                }

            # Full 8-column row
            if len(value_tokens) == 8:

                confidence = "per_model_columnar"

            # Partial / spanning row
            else:

                confidence = "spanning_or_partial"

                flags.append(
                    f"only_{len(value_tokens)}_of_8_values_present"
                )

            fields.append(
                {
                    "label": label,
                    "top": top,
                    "per_model": per_model,
                    "raw_values": [
                        text
                        for text, _ in value_tokens
                    ],
                    "confidence": confidence,
                    "flags": flags,
                }
            )

        # SHARED VALUE
        else:

            shared_text = " ".join(
                text
                for text, _ in value_tokens
            )

            fields.append(
                {
                    "label": label,
                    "top": top,
                    "per_model": {
                        model: {
                            "value": shared_text,
                            "col_dist_pts": None,
                        }
                        for model in model_names
                    },
                    "raw_values": [
                        shared_text
                    ],
                    "confidence": "shared_across_all_models",
                    "flags": flags,
                }
            )

    # RETURN PARSED TABLE
    return {
        "model_columns": model_names,
        "fields": fields,
    }


# PARSE EXTRACTED PDF JSON
def parse_pdf(
    extracted_path: Path,
    output_path: Path,
):
    """
    Parse an extracted PDF JSON file into structured table data.

    Input:

        data/extracted/source_1.json

    Output:

        data/parsed/source_1.json
    """

    pages = load_extracted_words(
        extracted_path
    )

    # Find table page automatically
    page = get_relevant_page(
        pages
    )

    # Parse table
    result = parse_page(
        page
    )

    # Add source metadata
    result["source_path"] = str(
        extracted_path
    )

    result["page"] = page["page"]

    # Save output
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False,
        )

    return output_path