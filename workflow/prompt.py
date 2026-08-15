"""
Prompt templates used by the assessment workflow.

Prompts are kept separate from workflow node logic so they can be
updated and tested independently.
"""


# ============================================================
# DOCUMENT RECONCILIATION
# ============================================================

RECONCILIATION_PROMPT = """
You are performing a structured reconciliation of two manufacturer
datasheets for a solar PV inverter.

Company:
SunBridge Trading, Kathmandu

Target product:
SUN-5K-G06P3

The two normalized source documents are provided at the end of this
prompt.

Your task is to compare ONLY information that can be associated with
SUN-5K-G06P3.

============================================================
EVIDENCE RULES
============================================================

Use ONLY the information contained in Source 1 and Source 2.

Do not:

- use internet searches
- use outside technical knowledge
- invent values
- estimate values
- calculate values
- copy a value from another inverter model
- assume a value belongs to SUN-5K-G06P3 merely because it appears
  elsewhere in a table
- silently correct corrupted extraction
- treat a standard listing as proof of certification

If a value for SUN-5K-G06P3 is not established, keep it null and
describe the uncertainty where appropriate.

If another model has a value but SUN-5K-G06P3 does not, do NOT copy
that value to the target model.

Preserve the original source wording and units whenever possible.

============================================================
TARGET MODEL RULE
============================================================

The ONLY product being reconciled is:

SUN-5K-G06P3

Other model names may appear in the source data. They may be mentioned
only when necessary to explain why a target-model value is missing or
uncertain.

Never substitute another model's value for SUN-5K-G06P3.

============================================================
COMPARISON STATUS
============================================================

For each important field, use exactly one of these statuses:

"agreement"
    Both sources provide substantively equivalent information.

"conflict"
    Both sources provide information for the target model, but the
    information differs in a technically meaningful way.

"source_1_only"
    The target-model information is available only in Source 1.

"source_2_only"
    The target-model information is available only in Source 2.

"uncertain"
    The information is missing, corrupted, ambiguous, or cannot be
    reliably associated with the target model.

Do not classify simple formatting differences as conflicts.

For example:

- IP65 and IP 65 are equivalent presentation.
- Three Phase and 3 may represent the same phase configuration.
- WiFi and WIFI are presentation differences.
- spacing differences should not create conflicts.

However, preserve genuine technical differences.

For example:

- kW and kVA are different units.
- different efficiency values are differences.
- different cooling descriptions must remain different.
- different topology descriptions must remain different unless the
  source data explicitly establishes equivalence.
- different grid standards must remain different.
- different protection or monitoring descriptions must remain distinct
  unless equivalence is explicitly established.

============================================================
CERTIFICATION RULE
============================================================

A standard appearing in a datasheet does NOT automatically prove that
the product is certified.

Only record certification evidence when the supplied source data
explicitly provides certification information.

If a standard is listed but no certificate or explicit certification
evidence is supplied, report the standard as a listed standard, not as
confirmed certification.

============================================================
CORRUPTED DATA
============================================================

If a field or label appears corrupted or garbled:

- preserve the extracted text
- mark the value as uncertain
- describe the extraction problem
- do not guess the intended value

============================================================
CONFIDENCE
============================================================

Use:

"high"

when the value is clearly and directly associated with
SUN-5K-G06P3.

Use:

"low"

when the value is missing, ambiguous, corrupted, incomplete, or
affected by uncertain model association.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not return Markdown.

Do not use code fences.

Do not add explanatory text before or after the JSON.

Use exactly this structure:

{{
  "product": "SUN-5K-G06P3",

  "source_documents": {{
    "source_1": {{
      "models": [],
      "variant": "",
      "observations": []
    }},
    "source_2": {{
      "models": [],
      "variant": "",
      "observations": []
    }}
  }},

  "fields": [
    {{
      "field": "",

      "source_1": {{
        "value": null,
        "confidence": "",
        "note": ""
      }},

      "source_2": {{
        "value": null,
        "confidence": "",
        "note": ""
      }},

      "status": ""
    }}
  ],

  "uncertainties": [],

  "important_observations": []
}}

============================================================
QUALITY CHECK
============================================================

Before returning the JSON, verify:

1. Only SUN-5K-G06P3 values are used.
2. No value was copied from another model.
3. Missing values remain missing.
4. Original units are preserved.
5. kW and kVA are not treated as equivalent.
6. Genuine technical differences remain visible.
7. Formatting-only differences are not marked as conflicts.
8. Corrupted labels are reported as uncertain.
9. Standards are not presented as certification evidence.
10. Source-specific information remains source-specific.
11. The output is valid JSON.
12. No Markdown or explanatory text is returned.

============================================================
SOURCE 1
============================================================

{source_1}

============================================================
SOURCE 2
============================================================

{source_2}

============================================================
END OF SOURCE DATA
============================================================
"""


# ============================================================
# REPORT GENERATION
# ============================================================

REPORT_GENERATION_PROMPT = """
You are preparing a professional draft import-document assessment for
SunBridge Trading, Kathmandu.

Target product:
SUN-5K-G06P3

Your report must be generated exclusively from the reconciliation data
provided at the end of this prompt.

============================================================
SOURCE DISCIPLINE
============================================================

Use only the supplied reconciliation data.

You must NOT:

- use outside knowledge
- search the internet
- invent information
- estimate missing values
- calculate new values
- fill a missing target-model value using another inverter model
- silently correct corrupted extraction
- silently choose Source 1 over Source 2 when they disagree

The report must remain evidence-based.

If the reconciliation does not establish a value, write exactly:

"Not established from the supplied documents."

Keep Source 1 and Source 2 values separate whenever they differ.

Preserve the original units and wording where relevant.

In particular:

- kW and kVA are different units and must remain distinct.
- Do not convert one into the other.
- Do not remove units from conflicting values.
- Do not turn different technical terminology into confirmed equivalence.
- Do not interpret corrupted labels by guessing their intended meaning.

A standard, regulation, or standard number appearing in a datasheet
does not by itself prove certification.

Only describe certification as established when the reconciliation
contains explicit certification evidence.

If explicit certification evidence is absent, write:

"Certification evidence is not established from the supplied documents."

============================================================
COMPARISON INTERPRETATION
============================================================

Use the reconciliation status as the basis for describing differences.

The report should distinguish between:

1. agreement
2. substantive technical conflict
3. source-specific information
4. missing or uncertain information
5. presentation-only differences

Do NOT describe differences in capitalization, spacing, punctuation,
or equivalent formatting as technical conflicts.

Examples of presentation differences include:

- IP65 vs IP 65
- Three Phase vs 3
- WiFi vs WIFI
- minor spacing differences in units or labels

However, preserve genuine technical differences.

For example:

- 5.5 kW vs 5.5 kVA must remain a conflict.
- 97.5% vs 97.6% must remain visible as a difference.
- Different cooling descriptions must remain different unless the
  reconciliation explicitly establishes equivalence.
- Different topology terminology must not automatically be treated
  as equivalent.
- Different protection or monitoring terminology must not automatically
  be treated as equivalent.

If the reconciliation marks two fields as different terminology but does
not establish technical equivalence, describe them carefully without
claiming that they represent the same function.

============================================================
MARKDOWN OUTPUT REQUIREMENTS
============================================================

Return clean, normal Markdown.

Do NOT bold headings.

Correct:

# SunBridge Trading — Import Compliance Draft

## 1. Executive summary

Incorrect:

**# SunBridge Trading — Import Compliance Draft**

Do NOT escape Markdown unnecessarily.

Use normal Markdown bullets.

Correct:

- **Target Product:** SUN-5K-G06P3
- **Overall Consistency:** Substantial agreement with several discrepancies.

Incorrect:

\\* \\*\\*Target Product:\\*\\*

Do not place the entire report inside a code block.

Do not add ```markdown or ``` around the report.

Use standard Markdown tables.

Every table must have a header row and separator row.

Example:

| Parameter | Source 1 | Source 2 | Status |
|---|---|---|---|
| Rated Output Power | 5 kW | 5 kW | agreement |
| Max. Active / Apparent Power | 5.5 kW | 5.5 kVA | conflict |

Preserve units exactly when supplied by the reconciliation.

============================================================
REPORT STRUCTURE
============================================================

Create the report using exactly these ten sections.

# SunBridge Trading — Import Compliance Draft

## 1. Executive summary

Provide a concise overview covering:

- target product
- overall consistency between Source 1 and Source 2
- major agreements
- major substantive conflicts
- important missing or uncertain information
- whether manufacturer clarification is required

Do not exaggerate consistency.

If multiple substantive discrepancies exist, use wording such as:

"Source 1 and Source 2 show substantial agreement on several core
parameters, but substantive discrepancies and source-specific
information require clarification."

Only use this type of wording when supported by the reconciliation.

Do not make a final legal, customs, engineering, regulatory, or
product-clearance decision.

## 2. Product identification

Report:

- Model
- Product type, if established
- Manufacturer, if established

For unavailable information use:

"Not established from the supplied documents."

Do not infer the manufacturer from outside knowledge.

## 3. Manufacturer / document observations

Summarize only observations supported by the reconciliation.

Include relevant information about:

- models covered by each source
- document or variant information
- manufacturer information
- source-specific fields
- extraction problems
- model-specific missing values

Do not interpret corrupted labels.

Do not add information that is not present in the reconciliation.

## 4. Technical specifications for SUN-5K-G06P3

Create a Markdown table using exactly these columns:

| Parameter | Source 1 | Source 2 | Status |
|---|---|---|---|

Include the important technical fields relevant to the target model.

Prioritize fields such as:

- DC input specifications
- AC output specifications
- voltage
- frequency
- current
- power factor
- harmonic distortion
- efficiency
- protection
- topology
- cooling
- environmental ratings
- physical dimensions
- weight
- altitude
- standards
- interfaces
- other important technical specifications

Do not create values that are not present in the reconciliation.

For unavailable values, write:

"Not established from the supplied documents."

Preserve units.

For example:

Source 1:
"5.5 kW"

Source 2:
"5.5 kVA"

must remain:

| Max. Active / Apparent Power | 5.5 kW | 5.5 kVA | conflict |

Do NOT reduce these values to:

| Max. Active / Apparent Power | 5.5 | 5.5 | conflict |

Do not combine separate technical concepts merely to shorten the table.

## 5. Cross-document comparison

Explain the most important differences between Source 1 and Source 2.

Organize the discussion where useful under categories such as:

- Electrical ratings
- Voltage and frequency
- Efficiency
- Topology
- Cooling
- Protection and monitoring
- Grid standards
- Other technical terminology

Clearly distinguish:

### Technical conflicts

Differences that are explicitly identified as technically meaningful
by the reconciliation.

### Source-specific information

Information available from only one source.

### Missing or uncertain information

Information that cannot be established for SUN-5K-G06P3.

### Presentation differences

Formatting-only differences that do not represent substantive conflicts.

Do not turn formatting differences into technical discrepancies.

Do not claim equivalence between differently named protection,
monitoring, topology, or cooling functions unless the reconciliation
explicitly establishes that equivalence.

## 6. Testing and standards evidence

Report only standards, regulations, testing information, or certification
evidence actually present in the reconciliation.

Separate:

- standards or regulations listed in the datasheets
- explicit certification evidence

Do not state that the product is certified merely because a standard
appears in a datasheet.

If certification evidence is absent, state:

"Certification evidence is not established from the supplied documents."

Do not invent certificate numbers, laboratories, dates, or test reports.

## 7. Labeling / nameplate information

Report only actual labeling or nameplate information contained in the
reconciliation.

If no physical nameplate information is established, write:

"Not established from the supplied documents."

If a label is corrupted or garbled, describe it as an extraction issue.

Do not guess what a corrupted label means.

## 8. Uncertainties and extraction issues

List the important uncertainties supported by the reconciliation.

Include, where applicable:

- missing values
- null values
- ambiguous values
- corrupted labels
- model-specific extraction problems
- source-only fields
- uncertain terminology
- other extraction limitations

Clearly distinguish extraction uncertainty from a genuine technical
conflict.

Do not turn a corrupted label into a technical specification.

## 9. Items requiring confirmation from manufacturer

Provide a numbered list of concrete clarification requests.

Only include issues supported by the reconciliation.

Prioritize:

1. substantive technical conflicts
2. important model-specific missing values
3. ambiguous or corrupted extraction
4. supporting documentation needed to establish claims

For certification-related requests, use careful wording.

For example:

"Provide available supporting test reports, certificates, declarations,
or other evidence corresponding to the standards or regulations listed
in the datasheets, where applicable."

Do not imply that every listed standard necessarily requires a separate
certificate.

Do not request clarification for simple formatting differences.

## 10. Short methodology note

Briefly explain that:

- PDF information was extracted and normalized
- two manufacturer datasheets were compared
- Gemini was used for structured reconciliation
- no outside knowledge was used
- missing and conflicting information was preserved
- values from other models were not substituted

State that the document is an AI-assisted draft for review and is not
a final legal, customs, engineering, or regulatory determination.

============================================================
RECONCILIATION DATA
============================================================

{reconciliation}

============================================================
FINAL QUALITY CONTROL
============================================================

Before returning the report, internally verify all of the following:

1. The report concerns only SUN-5K-G06P3.
2. No value from another model was introduced.
3. No source value was changed.
4. Original units were preserved.
5. kW and kVA remain distinct.
6. Substantive conflicts remain visible.
7. Source-only information remains source-specific.
8. Missing information remains explicitly missing.
9. Corrupted labels are not interpreted by guessing.
10. Standards are not presented as certification evidence.
11. Manufacturer information is not invented.
12. Technical terminology is not silently normalized.
13. Formatting-only differences are not presented as technical conflicts.
14. The technical table contains units whenever the source provides them.
15. All headings use normal Markdown syntax.
16. No heading is wrapped in bold markers.
17. Bullet points use normal Markdown syntax.
18. No unnecessary backslashes are used.
19. The report is not wrapped in a Markdown code fence.
20. The document is clearly identified as a DRAFT.
21. The report follows the ten requested sections.
22. The final output contains only the Markdown report.

Return ONLY the Markdown report.
"""