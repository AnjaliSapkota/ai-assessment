"""
Prompt templates for the Cantordust Task 1 assessment workflow.

The prompts are kept separate from workflow node logic so they can be
revised and tested independently.
"""


# ============================================================
# 1. DOCUMENT RECONCILIATION PROMPT
# ============================================================

RECONCILIATION_PROMPT = """
You are reviewing two manufacturer datasheets for a solar PV inverter
as part of an import-document assessment.

Company:
SunBridge Trading, Kathmandu

Target product:
SUN-5K-G06P3

Two normalized manufacturer datasheets are provided below.

Your task is to compare the two sources and reconcile information for
the TARGET MODEL ONLY.

The normalized data may contain multiple inverter models. Never use a
value belonging to another model as the value of SUN-5K-G06P3.


============================================================
EVIDENCE RULES
============================================================

Use only the information contained in Source 1 and Source 2.

Do not:

- search the internet
- use outside technical knowledge
- invent values
- estimate missing values
- calculate values
- infer values from another model
- silently repair corrupted extraction
- assume two different technical terms mean the same thing

If a SUN-5K-G06P3 value is unavailable, preserve it as null or mark
the field as uncertain.

If another model has a value but SUN-5K-G06P3 does not, do not copy
that value to the target model.

Preserve original wording, numbers, and units whenever possible.


============================================================
COMPARISON LOGIC
============================================================

For every meaningful technical field found in either source, compare
the values associated specifically with SUN-5K-G06P3.

Use exactly one of these statuses:

"agreement"
    Both sources contain substantively equivalent information.

"conflict"
    Both sources contain information for the same field but the
    information differs in a technically meaningful way.

"source_1_only"
    A target-model value is available only in Source 1.

"source_2_only"
    A target-model value is available only in Source 2.

"uncertain"
    The value is missing, corrupted, ambiguous, or cannot reliably
    be associated with SUN-5K-G06P3.


============================================================
IMPORTANT DISTINCTIONS
============================================================

Do not turn simple presentation differences into technical conflicts.

Examples of presentation differences include:

- IP65 versus IP 65
- 4000 versus 4000m
- capitalization differences
- spacing differences
- punctuation differences
- equivalent formatting of the same value

Preserve the original source representation even when the status is
agreement.

However, genuine technical differences must remain visible.

Examples:

- kW versus kVA
- different efficiency percentages
- different cooling descriptions
- different grid standards
- different frequency ranges
- different protection specifications
- "Transformerless" versus "Non-Isolated"

Do not automatically declare two different technical terms equivalent.


============================================================
SOURCE TRACEABILITY
============================================================

For important values, provide a short note identifying how the value
appears in the corresponding source.

If a label is corrupted or garbled, preserve the original corrupted
text and describe it as an extraction issue.

Do not guess what a corrupted label means.

A standard or regulation listed in a datasheet is not automatically
evidence that the product has been certified.

Only report certification evidence when the supplied source data
explicitly contains certification information.


============================================================
TARGET MODEL
============================================================

The only product being evaluated is:

SUN-5K-G06P3

Other models may be mentioned only when useful for explaining an
extraction or model-specific missing-data issue.

Do not substitute values from:

- SUN-4K-G06P3
- SUN-6K-G06P3
- SUN-7K-G06P3
- SUN-8K-G06P3
- SUN-10K-G06P3
- SUN-12K-G06P3
- SUN-15K-G06P3

or any other model.


============================================================
OUTPUT REQUIREMENTS
============================================================

Return ONLY valid JSON.

Do not return Markdown.
Do not use JSON code fences.
Do not write explanations before or after the JSON.

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
CONFIDENCE
============================================================

Use:

"high"

when the value is clearly and directly associated with
SUN-5K-G06P3 in the normalized data.

Use:

"low"

when the value is missing, partial, corrupted, ambiguous, or affected
by extraction uncertainty.


============================================================
QUALITY CONTROL
============================================================

Before returning the JSON, check all of the following:

1. Every technical value belongs specifically to SUN-5K-G06P3.

2. No value has been copied from another model.

3. Missing target-model values remain missing.

4. Original units are preserved.

5. kW and kVA are not treated as equivalent.

6. Genuine technical differences remain visible.

7. Formatting-only differences are not incorrectly reported as
   technical conflicts.

8. Corrupted labels are reported as extraction issues.

9. Standards are not presented as certification evidence unless
   certification evidence is explicitly present.

10. Source-specific information is correctly classified.

11. The response is valid JSON.

12. Do not add fields that are unsupported by the normalized data.


============================================================
SOURCE 1 NORMALIZED DATA
============================================================

{source_1}


============================================================
SOURCE 2 NORMALIZED DATA
============================================================

{source_2}


============================================================
END OF INPUT
============================================================
"""


# ============================================================
# 2. REPORT GENERATION PROMPT
# ============================================================

REPORT_GENERATION_PROMPT = """
Prepare a professional draft import-document assessment for:

SunBridge Trading, Kathmandu

Target product:

SUN-5K-G06P3

The report must be generated ONLY from the reconciliation data
provided below.


============================================================
REPORTING RULES
============================================================

Use only the reconciliation data.

Do not:

- use outside knowledge
- search the internet
- invent information
- calculate missing values
- fill missing values using another inverter model
- silently choose one source when two sources disagree
- change the original source values
- claim facts that are not present in the reconciliation

When information cannot be established, write:

"Not established from the supplied documents."

Keep Source 1 and Source 2 values visible when they differ.

Preserve the original units.

Do not treat kW and kVA as interchangeable.

Do not automatically treat different technical terminology as
equivalent.

Formatting differences such as capitalization, spacing, punctuation,
or presentation should not be described as substantive technical
conflicts.

Corrupted or garbled labels must be described as extraction issues.
Do not guess their intended meaning.

A standard listed in a datasheet does not by itself establish
certification.

If certification evidence is not explicitly present, state that
certification evidence is not established from the supplied
documents.

The final document is a DRAFT. Do not present it as a final legal,
customs, engineering, or regulatory determination.


============================================================
REPORT STRUCTURE
============================================================

Create clean professional Markdown using exactly these sections:


# SunBridge Trading — Import Compliance Draft

## 1. Executive summary

Summarize:

- target product
- overall consistency between the two sources
- important agreements
- important conflicts
- important missing or uncertain information
- whether manufacturer clarification is required

Do not make a final compliance or customs-clearance decision.


## 2. Product identification

Include:

- Model
- Product type, if established
- Manufacturer, if established

If unavailable, write:

"Not established from the supplied documents."


## 3. Manufacturer / document observations

Summarize relevant observations about Source 1 and Source 2.

Include useful information such as:

- model coverage
- document variant
- extraction problems
- model-specific missing values
- other important document-level observations

Do not invent manufacturer information.


## 4. Technical specifications for SUN-5K-G06P3

Create a Markdown table using:

| Parameter | Source 1 | Source 2 | Status |
| :--- | :--- | :--- | :--- |

Include important technical fields found in the reconciliation.

Preserve original values and units.

For unavailable information, write:

"Not established from the supplied documents."


## 5. Cross-document comparison

Explain the most important substantive differences.

Useful categories include:

- electrical ratings
- power units
- voltage
- frequency
- phase
- efficiency
- protection
- topology
- cooling
- grid standards
- other technical terminology

Do not hide or silently resolve conflicts.

Do not turn formatting-only differences into technical conflicts.


## 6. Testing and standards evidence

Report only standards and evidence contained in the reconciliation.

Clearly distinguish between:

- standards listed in the datasheets
- actual certification evidence

Do not claim certification without explicit evidence.

If standards are listed but certification evidence is absent, state:

"Certification evidence is not established from the supplied documents."


## 7. Labeling / nameplate information

Report actual labeling or nameplate information contained in the
reconciliation.

If a label is corrupted or garbled, describe it as an extraction
issue instead of guessing its meaning.


## 8. Uncertainties and extraction issues

List important:

- missing values
- null values
- ambiguous values
- corrupted labels
- model-specific extraction problems
- source-only information
- other uncertainties


## 9. Items requiring confirmation from manufacturer

Provide a numbered list of concrete clarification requests.

Only include issues that are actually supported by the
reconciliation.

Prioritize technically important unresolved differences and missing
model-specific information.


## 10. Short methodology note

Briefly explain that:

- PDF information was extracted and normalized
- two manufacturer datasheets were compared
- Gemini was used for reconciliation
- no outside knowledge was used
- missing and conflicting information was preserved
- values from other models were not substituted

Make clear that the document is an AI-assisted draft for review.


============================================================
RECONCILIATION DATA
============================================================

{reconciliation}


============================================================
FINAL QUALITY CHECK
============================================================

Before returning the report:

1. Keep the report focused on SUN-5K-G06P3.

2. Do not introduce outside information.

3. Do not invent missing specifications.

4. Do not copy specifications from another model.

5. Do not silently resolve disagreements between Source 1 and Source 2.

6. Preserve source units.

7. Keep meaningful conflicts visible.

8. Do not describe formatting differences as technical conflicts.

9. Do not claim certification without evidence.

10. Report corrupted extraction labels as uncertainties.

11. Keep the document clearly identified as a DRAFT.
"""


# ============================================================
# 3. OPTIONAL PDF EXTRACTION PROMPT
# ============================================================

PDF_EXTRACTION_PROMPT = """
You are extracting structured technical information from a
manufacturer datasheet for a solar PV inverter.

File:
{filename}

Extract information directly from the supplied document.

The purpose of the extraction is to support a later comparison of
two manufacturer datasheets. Accuracy and source traceability are
more important than filling every field.


============================================================
EXTRACTION TARGETS
============================================================

Look for:

1. Product and model information
2. Product variant information
3. Manufacturer information
4. DC input specifications
5. AC output specifications
6. Efficiency
7. Protection functions
8. Environmental specifications
9. Physical specifications
10. Grid connection standards
11. Safety and EMC standards
12. Interfaces and features
13. Labeling or nameplate information
14. Extraction problems or unusual labels


============================================================
EXTRACTION RULES
============================================================

Extract values as they appear in the document.

Do not:

- invent values
- calculate values
- estimate unreadable values
- copy a value between models
- assume a value belongs to a model when the table structure does
  not clearly establish the association
- convert or normalize units unnecessarily
- treat standards as certification evidence

Preserve:

- original wording
- original units
- model names
- source page numbers
- unusual or corrupted text

If information is absent, use null.

If text appears corrupted or garbled, preserve the extracted text
and add an entry to extraction_issues.

When the document contains multiple models, associate a technical
value with a model only when the document layout makes that
association reasonably clear.


============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

Do not use Markdown.
Do not use code fences.
Do not add explanatory prose.

Use this structure:

{{
  "product_name": null,

  "product_variant": null,

  "manufacturer": {{
    "company_name": null,
    "address": null,
    "website": null,
    "country": null
  }},

  "models": [],

  "technical_specs": [],

  "standards": [],

  "labeling": [],

  "extraction_issues": []
}}


Each technical specification should follow this structure:

{{
  "field": "",
  "value": null,
  "unit": null,
  "model": null,
  "source_page": null
}}


============================================================
DOCUMENT
============================================================

{document_text}


============================================================
END OF DOCUMENT
============================================================
"""