import json
import re
from pathlib import Path


# Configuration

ROW_TOL = 3.0
LABEL_MAX_X = 180.0
MERGE_GAP = 10.0


# load extracted pdf data

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


# Find relevant table page containing the technical specification table

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


# Row clustering

def cluster_rows(words, tolerance=ROW_TOL):
    """
    Group words that appear on the same visual row.

    PDF text extraction does not necessarily preserve table rows,
    so words are grouped using their vertical 'top' coordinate.
    """

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


# Find model header

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

def looks_like_continuation(value_words):

    if not value_words:
        return False

    texts = [word["text"] for word in value_words]

    if len(texts) > 8:
        return True

    numeric_like = sum(
        1
        for text in texts
        if is_numeric_token(text)
    )

    return numeric_like < len(texts) / 2


def merge_wrapped_rows(rows):
    """
    Merge a wrapped field back into a single logical row.

    Two distinct wrapping patterns show up in these datasheets:

    1. A label-only row followed by a value-only row:

           Long technical specification label
                                         5  5  5  5 ...

    2. A row that already has a label AND the start of a value,
       where the value itself is too long to fit on one line and
       spills onto one or more further value-only rows:

           Grid Regulation   IEC 61727, IEC 62116, CEI 0-21, ...
                              ..., OVE-Richtlinie R25, G99, VDE-AR-N 4105

    Both become one logical row. Case 2 previously was not handled:
    only a label-only row triggered a merge, so a field that already
    had *some* value text on its first line silently lost every
    later continuation line (or, depending on layout, kept only the
    trailing fragment) -- producing truncated values and false
    cross-source conflicts instead of a fuller, non-conflicting
    picture. The loop below keeps absorbing follow-on rows as long
    as they carry no label of their own and look like a text
    continuation rather than a fresh per-model value row, which also
    naturally handles a value wrapping across more than two lines.
    """

    merged = []

    i = 0

    while i < len(rows):

        row = rows[i]

        combined_row = list(row)

        last_row = row

        while i + 1 < len(rows):

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

            # A continuation line never carries its own label, and
            # it must actually have some value text to be worth
            # absorbing.
            if next_label_words or not next_value_words:
                break

            gap = next_row[0]["top"] - last_row[0]["top"]

            if gap > MERGE_GAP:
                break

            current_value_words = [
                word
                for word in combined_row
                if word["x0"] >= LABEL_MAX_X
            ]

            current_label_words = [
                word
                for word in combined_row
                if word["x0"] < LABEL_MAX_X
            ]

            # Case 1: label so far, no value yet at all.
            is_label_only_so_far = (
                bool(current_label_words)
                and not current_value_words
            )

            # Case 2: we already have some value text, and the next
            # line reads like more of the same wrapped text rather
            # than a fresh, independent per-model value row.
            is_text_continuation = (
                bool(current_value_words)
                and looks_like_continuation(next_value_words)
            )

            if not (is_label_only_so_far or is_text_continuation):
                break

            combined_row = combined_row + next_row

            last_row = next_row

            i += 1

        merged.append(combined_row)

        i += 1

    return merged


# Detect possible PDF text-layer corruption like overlapping texts


def detect_label_flags(label):

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

    words = page["words"]

    # CLUSTER WORDS INTO VISUAL ROWS

    rows_raw = cluster_rows(words)

    # FIND MODEL HEADER

    header_tokens = find_header(rows_raw)

    model_names, centers = build_column_bins(
        header_tokens
    )

    header_top = min(
        token["top"]
        for token in header_tokens
    )

    # MERGE WRAPPED LABEL ROWS

    rows = merge_wrapped_rows(rows_raw)

    # PARSE EACH TABLE ROW

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

        # Separate label and value zones\
        label_words = sorted(
            [
                word
                for word in row
                if word["x0"] < LABEL_MAX_X
            ],
            key=lambda word: (word["top"], word["x0"]),
        )

        value_words = sorted(
            [
                word
                for word in row
                if word["x0"] >= LABEL_MAX_X
            ],
            key=lambda word: (word["top"], word["x0"]),
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


# MANUFACTURER IDENTITY 

# get_relevant_page() picks exactly one page -- the one that scores
# best as a spec-*table* page -- and parse_page() only ever looks at
# words inside that table's row/column structure. Manufacturer name
# and address in this document family live in ordinary page-footer
# text, not in a labeled table row, so that pipeline structurally
# never sees them: it isn't that the value gets extracted and then
# lost, it's never in scope to extract at all. This is a separate,
# independent pass over every page's free text.

MANUFACTURER_NAME_PATTERN = re.compile(
    r"([A-Z][A-Za-z0-9&,.\-\s]{0,80}?\bCo\.,?\s*Ltd\.?)"
)

ADDRESS_HINT_PATTERN = re.compile(
    r"(Road|Street|Ave|District|Zhejiang|China|No\.\s*\d+)",
    re.IGNORECASE,
)


def _page_lines(page):
    """
    Reconstruct simple top-to-bottom, left-to-right text lines for
    a page, independent of any table/column structure. This is what
    lets us search ordinary prose (titles, footers, boilerplate)
    that the table-row parser above never looks at.
    """

    rows = cluster_rows(page["words"])

    lines = []

    for row in rows:

        row_sorted = sorted(
            row,
            key=lambda word: word["x0"],
        )

        lines.append(
            {
                "text": " ".join(
                    word["text"]
                    for word in row_sorted
                ),
                "top": min(
                    word["top"]
                    for word in row
                ),
            }
        )

    return lines


def extract_manufacturer_info(pages):
    """
    Find manufacturer legal name / address by scanning the free
    text of EVERY page, not just the spec-table page.

    Deliberately independent of get_relevant_page() and the
    table-row pipeline above -- see module note. Returns a dict
    describing what was found (and where), or an explicit
    found=False so callers can say "pending" honestly instead of
    silently omitting the field.
    """

    for page in pages:

        for index, line in enumerate(_page_lines(page)):

            match = MANUFACTURER_NAME_PATTERN.search(
                line["text"]
            )

            if not match:
                continue

            name = match.group(1).strip()

            context_lines = _page_lines(page)[index: index + 3]

            address_parts = [
                context_line["text"].strip()
                for context_line in context_lines
                if ADDRESS_HINT_PATTERN.search(context_line["text"])
            ]

            return {
                "found": True,
                "name": name,
                "address": " ".join(address_parts) if address_parts else None,
                "source_page": page.get("page"),
                "raw_line": line["text"].strip(),
                "extraction_method": "footer_free_text_regex",
            }

    return {
        "found": False,
        "name": None,
        "address": None,
        "source_page": None,
        "raw_line": None,
        "extraction_method": "footer_free_text_regex",
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

    # Manufacturer identity -- searched across ALL pages, since
    # it is not part of the table region parse_page() looked at.

    result["manufacturer"] = extract_manufacturer_info(pages)

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