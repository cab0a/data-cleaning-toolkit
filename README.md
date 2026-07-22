# Data Cleaning Toolkit

[![CI](https://github.com/cab0a/data-cleaning-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/cab0a/data-cleaning-toolkit/actions/workflows/ci.yml)

Inspect CSV structure, draft reviewable schema rules, and apply deterministic
value mapping, column, conditional-presence, and cross-column validation,
normalization, and deduplication from the command line.

**Primary outputs:** a cleaned CSV and machine-readable evidence that traces
the decisions made from input to output.

**Intended use:** local checks before analysis or machine learning, incoming
CSV validation, and reproducible preprocessing prototypes.

## Overview

Data Cleaning Toolkit is a small, deterministic command-line tool for
inspecting and cleaning UTF-8 CSV files. It separates three tasks:

1. `inspect` describes the table structure without guessing semantic types.
2. `suggest-schema` proposes conservative column rules and records the
   evidence behind each suggestion.
3. `clean` applies versioned, reviewable rules from a JSON schema.

Schema suggestions never modify data and are not treated as final rules. A
value changes only when a reviewed cleaning schema says how it should change.
Invalid values remain visible in an audit report even when the corresponding
rows are excluded from the clean output.

## Problem

Tabular data often arrives with whitespace differences, inconsistent casing,
non-canonical numbers, invalid dates, missing required values, duplicate
business keys, and rows whose field count does not match the header. Ad hoc
cleanup in a notebook can fix the immediate file while making it difficult to
answer:

- Which rules were applied?
- Which rows were removed, and why?
- Did two runs use the same configuration?
- Can the cleaned file be regenerated from committed inputs?

This project makes those decisions explicit and produces machine-readable
evidence alongside the cleaned data.

## Features

- Inspects column counts, empty cells, distinct non-empty values, exact
  duplicate rows, and malformed row widths
- Suggests conservative column types, required fields, and whitespace rules
- Reports boolean, integer, decimal, and date parse coverage for each column
- Preserves leading-zero identifiers as strings during schema suggestion
- Loads versioned cleaning rules from JSON
- Supports `string`, `integer`, `decimal`, `boolean`, and `date` columns
- Applies opt-in whitespace trimming and string case normalization
- Maps reviewed source values to explicit canonical values using exact,
  case-sensitive rules
- Summarizes exact mapping matches by column and across the full input
- Ranks unmatched mapping-source values by observed frequency
- Supports raw, redacted, or disabled unmatched-value summaries per column
- Canonicalizes integers, finite decimal values, booleans, and dates
- Validates required values, allowed values, regular expressions, and numeric
  minimum and maximum bounds
- Validates equality and ordering relationships between normalized columns
- Requires one normalized value when another normalized value is present
- Keeps, drops, or rejects columns not defined in the schema
- Keeps or drops invalid rows according to an explicit policy
- Removes duplicate normalized keys while retaining the first accepted row
- Writes deterministic UTF-8 CSV and JSON outputs
- Records SHA-256 digests for the input, schema, and clean CSV
- Exposes a typed public Python API from the package root
- Documents the version 1 cleaning-report compatibility contract
- Verifies 16 committed reference artifacts with a portable checksum manifest
- Replaces each output atomically after it has been written successfully
- Uses only the Python standard library at runtime
- Includes intentionally dirty and controlled demonstration datasets,
  reference outputs, focused tests, and CI for Python 3.10 through 3.14

## Quick Start

Python 3.10 or later is required.

```bash
git clone https://github.com/cab0a/data-cleaning-toolkit.git
cd data-cleaning-toolkit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Inspect a CSV before defining cleaning rules:

```bash
data-cleaning-toolkit inspect examples/demo_dirty.csv \
  --output output/inspection.json
```

Generate a reviewable schema candidate with per-column evidence:

```bash
data-cleaning-toolkit suggest-schema examples/schema_suggestion_demo.csv \
  --output output/schema_suggestion.json
```

Apply the example schema:

```bash
data-cleaning-toolkit clean examples/demo_dirty.csv \
  --schema examples/customer_schema.json \
  --output output/demo_clean.csv \
  --report output/demo_cleaning_report.json
```

Run the controlled explicit-value-mapping example:

```bash
data-cleaning-toolkit clean examples/value_mapping_demo.csv \
  --schema examples/value_mapping_schema.json \
  --output output/value_mapping_clean.csv \
  --report output/value_mapping_report.json
```

Run the controlled cross-column validation example:

```bash
data-cleaning-toolkit clean examples/cross_column_demo.csv \
  --schema examples/cross_column_schema.json \
  --output output/cross_column_clean.csv \
  --report output/cross_column_report.json
```

Run the controlled conditional-presence example:

```bash
data-cleaning-toolkit clean examples/conditional_presence_demo.csv \
  --schema examples/conditional_presence_schema.json \
  --output output/conditional_presence_clean.csv \
  --report output/conditional_presence_report.json
```

Run the controlled mapping-coverage example:

```bash
data-cleaning-toolkit clean examples/mapping_coverage_demo.csv \
  --schema examples/mapping_coverage_schema.json \
  --output output/mapping_coverage_clean.csv \
  --report output/mapping_coverage_report.json
```

Run the controlled unmatched-frequency example:

```bash
data-cleaning-toolkit clean examples/unmatched_frequency_demo.csv \
  --schema examples/unmatched_frequency_schema.json \
  --output output/unmatched_frequency_clean.csv \
  --report output/unmatched_frequency_report.json
```

Compare raw, redacted, and disabled frequency modes:

```bash
data-cleaning-toolkit clean examples/privacy_modes_demo.csv \
  --schema examples/privacy_modes_schema.json \
  --output output/privacy_modes_clean.csv \
  --report output/privacy_modes_report.json
```

The dirty-data demo is intentionally invalid, so `inspect` and `clean` write
their outputs and return exit code 1. The value-mapping example also returns 1
because its final row contains deliberately unmapped values. The cross-column
example returns 1 because it includes deliberate relationship violations. The
conditional-presence example returns 1 because it includes deliberately
missing dependent values. The mapping-coverage example returns 1 because it
includes one deliberately unknown value. The unmatched-frequency example
returns 1 because it includes four deliberately unknown values. The controlled
privacy-mode and `suggest-schema` examples return 0. These semantics make the
CLI usable as a data-quality gate in scripts and CI.

Regenerate the committed reference artifacts with:

```bash
python examples/run_demo.py
```

Run the tests with:

```bash
python -m pytest
```

Run the public Python API example:

```bash
python examples/public_api_demo.py
```

Verify the committed reference artifacts without regenerating them:

```bash
python examples/run_demo.py --verify-only
```

## Documentation

- [Public Python API](docs/public-api.md)
- [Cleaning Report Version 1](docs/cleaning-report-v1.md)
- [Reproducibility](docs/reproducibility.md)

## Demonstration Result

The example input contains seven rows:

- Three valid customer rows
- One duplicate customer key after normalization
- One row with a missing required name
- One row with an invalid email, country, date, and negative value
- One row with more fields than the header

The configured pipeline produces:

```text
Input rows: 7
Output rows: 3
Invalid rows: 3
Duplicate rows removed: 1
Mapped cells: 0
Transformed cells: 21
Cross-column failures: 0
Conditional presence failures: 0
```

The cleaned output is committed as
[`results/demo_clean.csv`](results/demo_clean.csv). The full row-level evidence
is in
[`results/demo_cleaning_report.json`](results/demo_cleaning_report.json).

The controlled schema-suggestion sample contains seven columns with known
intended types. The tool suggests all seven as expected, including an
optional text column and a leading-zero postal code that must remain a string:

| Expected type | Columns | Matched |
| --- | ---: | ---: |
| Boolean | 1 | 1 |
| Integer | 1 | 1 |
| Decimal | 1 | 1 |
| Date | 1 | 1 |
| String | 3 | 3 |
| **Total** | **7** | **7** |

This result verifies the implementation against a controlled case; it is not
an accuracy claim for arbitrary real-world datasets. The complete evidence is
committed as
[`results/demo_schema_suggestion.json`](results/demo_schema_suggestion.json).

### Explicit Value Mapping Result

The controlled mapping sample contains common aliases for country,
membership, and boolean values. Reviewed rules convert 13 cells across six
accepted rows. A seventh row contains three unregistered values and is dropped
with explicit validation evidence:

```text
Input rows: 7
Output rows: 6
Invalid rows: 1
Mapped cells: 13
Transformed cells: 14
Errors: 3
```

The clean CSV is committed as
[`results/value_mapping_clean.csv`](results/value_mapping_clean.csv), and the
row-level mapping and rejection evidence is in
[`results/value_mapping_report.json`](results/value_mapping_report.json).
This controlled result demonstrates behavior and reproducibility; it does not
claim that the configured vocabulary is complete for other datasets.

### Mapping Coverage Result

The controlled coverage sample contains one partially matched column, one
fully matched column, and one configured column without observed values. The
CLI makes the exact-match ratios visible without changing validation behavior:

```text
Mapping coverage:
  country: 3/6 (50.0%)
  priority: 6/6 (100.0%)
  unused_code: 0/0 (n/a)
  Overall: 9/12 (75.0%)
```

The `country` denominator includes two already-canonical values and one
unknown value. This demonstrates why an unmatched cell is not automatically
an error and why the percentage is not a data-quality score. The clean CSV is
committed as
[`results/mapping_coverage_clean.csv`](results/mapping_coverage_clean.csv),
and the column and overall summaries are in
[`results/mapping_coverage_report.json`](results/mapping_coverage_report.json).

### Unmatched Value Frequency Result

The controlled frequency sample contains repeated canonical and unknown values
that do not match the configured source keys. The CLI lists them by descending
count:

```text
category: 2/11 (18.2%)
  Unmatched values:
    "unknown": 4
    "alpha": 3
    "beta": 2
```

The sample verifies ordering and counting only. The values `alpha` and `beta`
are already canonical, while `unknown` fails the configured allowed-value
rule. This demonstrates why frequency alone cannot determine whether a new
mapping is appropriate. The clean CSV is committed as
[`results/unmatched_frequency_clean.csv`](results/unmatched_frequency_clean.csv),
and the complete controlled audit is in
[`results/unmatched_frequency_report.json`](results/unmatched_frequency_report.json).

### Privacy Mode Result

The controlled privacy sample applies all three `unmatched_value_mode` values
to columns with the same mapping coverage. The CLI retains actionable counts
while changing how unmatched values are represented:

```text
raw_category: 1/8 (12.5%)
  Unmatched values:
    "alpha": 3
    "beta": 2
    "unknown": 2
redacted_category: 1/8 (12.5%)
  Unmatched values (redacted):
    rank 1: 4
    rank 2: 2
    rank 3: 1
disabled_category: 1/8 (12.5%)
  Unmatched values: disabled
```

The redacted report contains counts and ranks without source strings. The
disabled report retains mapping coverage but sets distinct and truncation
metadata to `null` and writes no frequency entries. The clean CSV deliberately
retains the original non-mapped values: these modes protect only the frequency
summary, not the cleaned data or row-level issues. The controlled outputs are
committed as [`results/privacy_modes_clean.csv`](results/privacy_modes_clean.csv)
and [`results/privacy_modes_report.json`](results/privacy_modes_report.json).

### Cross-Column Validation Result

The controlled cross-column sample checks an ordered date period, an optional
numeric range, and matching confirmation codes. Three rows pass all configured
relationships. Four rows are dropped with six independent rule failures:

```text
Input rows: 7
Output rows: 3
Invalid rows: 4
Transformed cells: 2
Cross-column failures: 6
Errors: 6
```

The optional numeric pair is blank in one accepted row, demonstrating the
documented empty-value behavior. The clean CSV is committed as
[`results/cross_column_clean.csv`](results/cross_column_clean.csv), and the
rule identifiers, normalized values, and row-level failures are in
[`results/cross_column_report.json`](results/cross_column_report.json).

### Conditional Presence Result

The controlled conditional-presence sample checks two dependencies: a start
date is required when an end date is present, and a reviewer is required when
a review timestamp is present. Four rows satisfy the configured rules. Three
rows are dropped with four independent failures:

```text
Input rows: 7
Output rows: 4
Invalid rows: 3
Transformed cells: 2
Conditional presence failures: 4
Errors: 4
```

One accepted row maps `N/A` to an empty end date before rule evaluation. This
demonstrates that presence is determined from normalized values rather than
raw CSV text. The clean CSV is committed as
[`results/conditional_presence_clean.csv`](results/conditional_presence_clean.csv),
and the rule identifiers, trigger values, and row-level failures are in
[`results/conditional_presence_report.json`](results/conditional_presence_report.json).

## Commands

### Inspect

```text
data-cleaning-toolkit inspect INPUT.csv [--output REPORT.json]
```

When `--output` is omitted, the JSON report is written to standard output.
Inspection is structural: it does not infer whether a column is numeric, a
date, an identifier, or a category.

The report contains:

- Input row and column counts
- Empty and non-empty cell counts per column
- Distinct non-empty value counts per column
- Exact duplicate row count
- Rows whose field count differs from the header

### Suggest Schema

```text
data-cleaning-toolkit suggest-schema INPUT.csv \
  --output SUGGESTION.json \
  [--date-format FORMAT]
```

The command ignores empty cells while measuring parse coverage. A non-string
type is suggested only when every non-empty value matches that type. Candidate
precedence is boolean, integer, decimal, and date; otherwise the column remains
a string. Textual forms such as `true` and `false` may be suggested as boolean,
while `0` and `1` remain eligible for integer inference. Integer-shaped values
with leading zeros are kept as strings to avoid destructive normalization of
identifiers.

The JSON output includes a ready-to-review `suggested_schema` object plus
per-column counts, whitespace observations, leading-zero counts, and parse
coverage. Copy or extract the candidate only after reviewing it against the
dataset's meaning and downstream requirements.

### Clean

```text
data-cleaning-toolkit clean INPUT.csv \
  --schema SCHEMA.json \
  --output CLEAN.csv \
  [--report AUDIT.json]
```

If `--report` is omitted, `clean.csv` produces `clean.report.json`. The input
CSV and schema are protected sources: neither can also be used as the clean
CSV or report path.

## Schema Format

Schemas are JSON objects with `version: 1` and an ordered `columns` mapping.
Unknown schema keys are rejected so a misspelled rule cannot silently pass.

```json
{
  "version": 1,
  "unknown_columns": "drop",
  "invalid_rows": "drop",
  "deduplicate_by": ["customer_id"],
  "columns": {
    "customer_id": {
      "type": "integer",
      "required": true,
      "strip": true
    },
    "email": {
      "type": "string",
      "required": true,
      "strip": true,
      "case": "lower",
      "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
    },
    "country": {
      "type": "string",
      "strip": true,
      "value_mapping": {
        "JP": "Japan",
        "JPN": "Japan"
      },
      "allowed_values": ["Japan"]
    },
    "lifetime_value": {
      "type": "decimal",
      "strip": true,
      "min": 0
    },
    "period_start": {
      "type": "date"
    },
    "period_end": {
      "type": "date"
    }
  },
  "cross_column_rules": [
    {
      "name": "period_order",
      "left": "period_start",
      "operator": "less_than_or_equal",
      "right": "period_end"
    }
  ],
  "conditional_presence_rules": [
    {
      "name": "start_required_when_end_present",
      "when_present": "period_end",
      "require": "period_start"
    }
  ]
}
```

### Dataset Rules

| Rule | Values | Behavior |
| --- | --- | --- |
| `version` | `1` | Selects the supported schema format |
| `unknown_columns` | `keep`, `drop`, `error` | Controls input columns absent from the schema |
| `invalid_rows` | `keep`, `drop` | Controls rows with validation errors |
| `deduplicate_by` | list of schema columns | Keeps the first accepted normalized key |
| `cross_column_rules` | list of comparison rules | Validates relationships between normalized columns |
| `conditional_presence_rules` | list of presence rules | Requires one normalized value when another is present |
| `columns` | ordered object | Defines output order when unknown columns are dropped |

### Column Rules

| Rule | Applies to | Description |
| --- | --- | --- |
| `type` | all | `string`, `integer`, `decimal`, `boolean`, or `date` |
| `required` | all | Rejects empty or configured null values |
| `strip` | all | Removes leading and trailing whitespace before validation |
| `null_values` | all | Maps exact configured strings to an empty value |
| `value_mapping` | all | Maps exact, case-sensitive source strings to canonical strings |
| `unmatched_value_mode` | columns with `value_mapping` | `raw` (default), `redacted`, or `disabled` |
| `case` | string | `preserve`, `lower`, or `upper` |
| `allowed_values` | all | Accepts only the listed normalized strings |
| `pattern` | all | Requires a full regular-expression match |
| `min`, `max` | integer, decimal | Applies inclusive numeric bounds |
| `input_format` | date | `datetime.strptime` format used for parsing |
| `output_format` | date | `datetime.strftime` format used for output |
| `true_values` | boolean | Configured strings normalized to `true` |
| `false_values` | boolean | Configured strings normalized to `false` |

Whitespace trimming is opt-in. Mapping sources are compared after configured
null handling and trimming, then mapped targets continue through type and
validation rules. `allowed_values` can be used with `value_mapping` to reject
unregistered values. Blank optional values remain blank. Integer and decimal
parsing is locale-independent: thousands separators and localized decimal
symbols are not silently interpreted.

### Mapping Coverage

The `clean` command summarizes exact `value_mapping` matches for every column
that defines at least one mapping entry. Coverage uses values after configured
null handling and trimming but before value mapping, case conversion, type
conversion, and validation.

For each configured column, the report contains:

- `observed_non_empty_cells`: non-empty source cells eligible for an exact
  mapping match
- `mapped_cells`: cells that matched a configured source key
- `unmapped_cells`: observed non-empty cells that did not match a source key
- `coverage_rate`: `mapped_cells / observed_non_empty_cells`, rounded to six
  decimal places, or `null` when no non-empty cells were observed
- `unmatched_value_mode`: the configured frequency disclosure policy
- `distinct_unmatched_values`: number of distinct non-empty source values that
  did not match a mapping key, or `null` when frequency collection is disabled
- `unmatched_value_frequencies`: up to ten raw values and counts, ranked counts
  without values, or an empty list, depending on the configured mode
- `unmatched_values_truncated`: whether additional distinct values were
  omitted from the summary, or `null` when frequency collection is disabled

The report also includes the same counts across all mapping columns. Counts
cover all input rows, including rows later dropped by validation or
deduplication, because the summary describes the supplied data rather than
only the accepted output. The CLI renders the rate as a percentage and uses
`n/a` for a zero denominator.

`unmatched_value_mode` is configured per mapping column:

- `raw` preserves version 0.7 behavior. Values are sorted by descending count;
  ties use ascending case-sensitive value order. CLI values are JSON-encoded
  so control characters are escaped.
- `redacted` uses the same deterministic ordering but emits only one-based
  ranks and counts. The rank describes the current report order and is not a
  stable identifier across changed inputs.
- `disabled` retains observed, mapped, and unmapped cell counts but does not
  collect distinct values or frequencies for that column.

The redacted mode still stores source values in memory while calculating
counts; it controls only the report and CLI representation. Use `disabled`
when even frequency collection is inappropriate.

### Cross-Column Rules

Each rule has a unique `name`, a `left` column, an `operator`, and a `right`
column. Both columns must have the same configured type. Rules compare values
after mapping, type conversion, and per-column validation.

| Operator | Supported types | Relationship |
| --- | --- | --- |
| `equal` | all matching types | Left and right values are equal |
| `not_equal` | all matching types | Left and right values differ |
| `less_than` | integer, decimal, date | Left value is less than right value |
| `less_than_or_equal` | integer, decimal, date | Left value is less than or equal to right value |
| `greater_than` | integer, decimal, date | Left value is greater than right value |
| `greater_than_or_equal` | integer, decimal, date | Left value is greater than or equal to right value |

A rule is skipped when either value is empty or either referenced column
already has a validation error. Use `required: true` on the relevant columns
when empty values must fail. This avoids secondary relationship errors for a
value that could not be parsed or validated individually.

### Conditional Presence Rules

Each rule has a unique `name`, a `when_present` trigger column, and a `require`
target column. Both columns must be defined in the schema and must be
different. The target must not also use `required: true`, because that would
make the conditional rule redundant.

```json
{
  "name": "start_required_when_end_present",
  "when_present": "end_date",
  "require": "start_date"
}
```

Presence is evaluated after null handling, trimming, value mapping, and type
normalization. An empty normalized trigger skips the rule. A non-empty trigger
requires a non-empty normalized target. A non-empty trigger that fails its own
validation still counts as present, so the report can record both the invalid
trigger and the missing dependent value. Use the column-level `required` rule
for unconditional requirements.

## Processing Order

Each run follows a fixed sequence:

1. Read the UTF-8 CSV and verify that headers are non-empty and unique.
2. Record rows whose field count differs from the header.
3. Apply configured null handling and whitespace trimming.
4. Count non-empty mapping candidates, collect unmatched source frequencies
   according to each column's disclosure mode, apply exact value mappings, and
   record each match as `VALUE_MAPPED`.
5. Apply case, type, and date normalization.
6. Apply required, allowed-value, pattern, and numeric-bound validation.
7. Apply conditional-presence rules to normalized values.
8. Apply cross-column rules to normalized values without existing column
   errors.
9. Keep or drop invalid rows according to `invalid_rows`.
10. Deduplicate accepted rows using normalized key values.
11. Write the clean CSV and a row-level JSON audit report using atomic file
   replacement for each artifact.

An invalid row that is dropped does not reserve its deduplication key. This
allows a later valid row with the same key to be retained.

## Audit Report

The cleaning report includes:

- Input, output, schema, and report format identifiers
- SHA-256 digests for the input CSV, schema, and clean output CSV
- Input and output row counts
- Invalid and dropped-invalid row counts
- Duplicate rows removed
- Number of cells matched by explicit value mappings
- Mapping coverage counts and rates by configured column and overall
- Policy-aware unmatched source-value frequencies and truncation metadata by
  column
- Number of cells changed by configured normalization
- Number of failed cross-column rules
- Number of failed conditional-presence rules
- Error and warning counts
- Counts grouped by stable issue code
- Row number, column name, original value, and explanation for each issue

Examples of stable issue codes include `VALUE_MAPPED`,
`MISSING_REQUIRED_VALUE`, `INVALID_DATE`, `PATTERN_MISMATCH`,
`VALUE_BELOW_MINIMUM`, `CROSS_COLUMN_RULE_FAILED`, `DUPLICATE_KEY`, and
`ROW_WIDTH_MISMATCH`. Conditional failures use
`CONDITIONAL_REQUIRED_VALUE_MISSING`.
`VALUE_MAPPED` has `info` severity and does not affect the command exit code.
Each cross-column failure records the configured rule name and both normalized
values. Each conditional-presence failure records the rule name, target
column, and normalized trigger value.

## Exit Codes

| Code | Meaning |
| ---: | --- |
| `0` | Command completed without validation errors |
| `1` | Output was produced, but invalid or malformed rows were detected |
| `2` | Input, schema, configuration, or output path prevented normal processing |

Duplicate-key removal is reported as a warning and does not by itself cause
exit code 1.

## Evaluation

The test suite covers:

- UTF-8 BOM handling, malformed rows, and duplicate header rejection
- Empty-cell, distinct-value, and exact-duplicate inspection counts
- Schema typo, invalid regex, invalid bound, and undefined key rejection
- String, integer, decimal, boolean, and date normalization
- Required values, patterns, allowed values, and numeric bounds
- Exact, case-sensitive value mapping before type conversion and validation
- Mapping counts and row-level `VALUE_MAPPED` audit evidence
- Mapping coverage after null handling and trimming, including empty columns,
  invalid rows, per-column rates, overall rates, and CLI reporting
- Unmatched-value frequency ordering, stable tie-breaking, ten-value limits,
  truncation metadata, and CLI escaping
- Raw, redacted, and disabled frequency modes, including schema rejection,
  value non-disclosure, rank output, and disabled collection
- Equality checks across matching normalized types and ordering checks for
  integer, decimal, and date columns
- Cross-column schema rejection, empty-value behavior, error de-duplication,
  rule identifiers, and CLI reporting
- Conditional-presence schema rejection, post-normalization presence checks,
  invalid-trigger behavior, rule identifiers, and CLI reporting
- Keep, drop, and error policies for unknown columns
- Keep and drop policies for invalid rows
- Normalized-key deduplication
- CLI output, audit reports, default naming, and input overwrite protection
- Root-package API exports, in-memory schema construction, executable API
  examples, and typed-package metadata
- Portable reference checksums, changed-artifact detection, and committed
  manifest verification
- Conservative type suggestion, partial parse coverage, optional fields,
  whitespace evidence, alternate date formats, and leading-zero protection

GitHub Actions installs the package, checks the CLI and public API example,
runs the tests, regenerates the reference results, verifies their checksum
manifest, and requires those results to match the committed artifacts on
Python 3.10 through 3.14.

## Limitations

- Version 0.9.0 supports comma-delimited UTF-8 CSV only.
- Files are processed in memory and are intended for small and moderate local
  datasets, not distributed or out-of-core workloads.
- The clean CSV and JSON report are replaced atomically as individual files,
  but the pair is not committed as one filesystem transaction.
- Schema suggestions are syntactic, not semantic. Numeric-looking identifiers,
  category codes, timestamps, locale-specific values, and domain-specific null
  markers require human review.
- A suggestion reflects only the observed rows. Small, biased, or already
  filtered samples can produce misleading candidates.
- The suggested `required` flag means only that no observed value was empty;
  it does not establish a domain requirement.
- Automatic repair and probabilistic inference are intentionally excluded.
- Value mappings are exact and case-sensitive. They do not provide fuzzy
  matching, synonym discovery, or mapping suggestions; the configured
  vocabulary must be reviewed for each dataset.
- Mapping coverage is an exact-match rate, not a quality score. Unmapped cells
  may be valid canonical values, unknown values, or values handled by later
  normalization and validation rules.
- Raw frequency summaries expose normalized source values in the JSON audit
  and CLI output. Treat these artifacts as sensitive when inputs may contain
  confidential, personal, or identifying values.
- Redacted summaries hide source strings but retain frequency counts and
  distinct-value totals, which can still reveal information about a
  distribution. Source values are stored in memory during aggregation.
- Disabled frequency mode suppresses distinct-value and frequency details, but
  it does not redact the clean CSV, schema, source file, or row-level audit
  issues. Review every artifact before sharing it.
- Frequency summaries retain only the top ten distinct unmatched values per
  column. They are diagnostic samples, not complete frequency tables when
  `unmatched_values_truncated` is true.
- The tool does not infer whether an unmatched value is canonical, invalid, or
  a safe mapping candidate. Mapping changes require domain review.
- Cross-column rules compare two columns of the same type. Arithmetic
  expressions, multi-column formulas, and cross-row relationships remain
  outside the current scope.
- Empty cross-column operands are skipped. Required-value rules must be used
  when an empty operand should invalidate the row.
- Conditional-presence rules support one positive presence condition and one
  required target. They do not support absence conditions, value predicates,
  negation, or AND/OR expressions.
- Presence is independent of trigger validity: an invalid but non-empty
  trigger still activates the rule. Review both reported issues when this
  occurs.
- Regular expressions describe syntax, not semantic correctness. The example
  email expression is deliberately simple.
- Date parsing uses configured Python `datetime` formats and does not infer
  locale or timezone.
- Numeric parsing does not accept thousands separators or localized decimal
  symbols unless the input is transformed before this tool.
- CSV cells are not automatically escaped against spreadsheet formula
  injection because leading `=`, `+`, `-`, and `@` may be legitimate data.
- The tool does not anonymize, classify, or detect personally identifiable
  information.
- A clean file means that configured rules passed; it is not proof that the
  data is correct for a downstream model or business decision.

## Project Structure

```text
data-cleaning-toolkit/
├── .github/workflows/ci.yml
├── docs/
│   ├── cleaning-report-v1.md
│   ├── public-api.md
│   └── reproducibility.md
├── examples/
│   ├── customer_schema.json
│   ├── conditional_presence_demo.csv
│   ├── conditional_presence_schema.json
│   ├── cross_column_demo.csv
│   ├── cross_column_schema.json
│   ├── demo_dirty.csv
│   ├── mapping_coverage_demo.csv
│   ├── mapping_coverage_schema.json
│   ├── privacy_modes_demo.csv
│   ├── privacy_modes_schema.json
│   ├── public_api_demo.py
│   ├── schema_suggestion_demo.csv
│   ├── schema_suggestion_expected.json
│   ├── unmatched_frequency_demo.csv
│   ├── unmatched_frequency_schema.json
│   ├── value_mapping_demo.csv
│   ├── value_mapping_schema.json
│   └── run_demo.py
├── results/
│   ├── README.md
│   ├── checksums.sha256
│   ├── conditional_presence_clean.csv
│   ├── conditional_presence_report.json
│   ├── cross_column_clean.csv
│   ├── cross_column_report.json
│   ├── demo_clean.csv
│   ├── demo_cleaning_report.json
│   ├── demo_inspection.json
│   ├── demo_schema_suggestion.json
│   ├── mapping_coverage_clean.csv
│   ├── mapping_coverage_report.json
│   ├── privacy_modes_clean.csv
│   ├── privacy_modes_report.json
│   ├── unmatched_frequency_clean.csv
│   ├── unmatched_frequency_report.json
│   ├── value_mapping_clean.csv
│   └── value_mapping_report.json
├── src/data_cleaning_toolkit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cleaning.py
│   ├── cli.py
│   ├── csv_table.py
│   ├── inspection.py
│   ├── models.py
│   ├── py.typed
│   ├── reporting.py
│   ├── schema.py
│   └── suggestion.py
├── tests/
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── MANIFEST.in
├── README.md
└── pyproject.toml
```

## Roadmap

Version 0.9.0 defines the release-candidate public API, report contract, and
reproducibility workflow. Version 1.0.0 will focus on final compatibility,
documentation, installation, and release review rather than new cleaning
features. Configurable delimiters, streaming processing, richer conditions,
and JSON Lines remain post-1.0 candidates.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for
details.
