# Reference Results

These files are deterministic outputs from eight synthetic, non-sensitive
examples:

- `demo_inspection.json`, `demo_clean.csv`, and
  `demo_cleaning_report.json` come from the intentionally dirty CSV in
  `examples/demo_dirty.csv` and the versioned rules in
  `examples/customer_schema.json`.
- `demo_schema_suggestion.json` comes from the controlled type sample in
  `examples/schema_suggestion_demo.csv`.
- `value_mapping_clean.csv` and `value_mapping_report.json` come from the
  controlled aliases and deliberately unregistered values in
  `examples/value_mapping_demo.csv`, using
  `examples/value_mapping_schema.json`.
- `cross_column_clean.csv` and `cross_column_report.json` come from the
  controlled relationship cases in `examples/cross_column_demo.csv`, using
  `examples/cross_column_schema.json`.
- `conditional_presence_clean.csv` and `conditional_presence_report.json`
  come from the controlled dependency cases in
  `examples/conditional_presence_demo.csv`, using
  `examples/conditional_presence_schema.json`.
- `mapping_coverage_clean.csv` and `mapping_coverage_report.json` come from
  the controlled partial, complete, and empty mapping cases in
  `examples/mapping_coverage_demo.csv`, using
  `examples/mapping_coverage_schema.json`.
- `unmatched_frequency_clean.csv` and `unmatched_frequency_report.json` come
  from the controlled repeated unmatched values in
  `examples/unmatched_frequency_demo.csv`, using
  `examples/unmatched_frequency_schema.json`.
- `privacy_modes_clean.csv` and `privacy_modes_report.json` compare raw,
  redacted, and disabled frequency disclosure using
  `examples/privacy_modes_demo.csv` and `examples/privacy_modes_schema.json`.

Regenerate them from the repository root with:

```bash
python examples/run_demo.py
```

The demo deliberately contains invalid and malformed rows. The underlying
`inspect` and `clean` commands therefore return exit code 1. The value-mapping
sample also returns 1 because its final row is deliberately invalid. The
cross-column sample returns 1 because it contains deliberate relationship
failures. The conditional-presence sample returns 1 because it contains
deliberately missing dependent values. The mapping-coverage sample returns 1
because it contains one deliberately unknown value. The unmatched-frequency
sample returns 1 because it contains four deliberately unknown values. The
privacy-mode sample returns 0 because it contains no validation errors. The
wrapper accepts those documented results and exits successfully after writing
all artifacts and validating the controlled summaries.

The schema-suggestion sample defines seven expected column types in
`examples/schema_suggestion_expected.json`. The reproduction script verifies
that every observed suggestion matches that controlled reference. This is a
deterministic functional evaluation, not a benchmark for arbitrary datasets.

The value-mapping check verifies six accepted rows, 13 mapped cells, 13
`VALUE_MAPPED` audit events, and three validation errors for the unregistered
row. It demonstrates deterministic rule application, not vocabulary coverage
for other datasets.

The cross-column check verifies three accepted rows, four invalid rows, and six
`CROSS_COLUMN_RULE_FAILED` audit events across date ordering, numeric ordering,
and string equality. It demonstrates deterministic comparison behavior, not
domain completeness for other datasets.

The conditional-presence check verifies four accepted rows, three invalid
rows, and four `CONDITIONAL_REQUIRED_VALUE_MISSING` audit events across two
named dependencies. One null marker and one whitespace-only value are
normalized before rule evaluation. This demonstrates deterministic dependency
checking, not domain completeness for other datasets.

The mapping-coverage check verifies three exact matches across six observed
country values, six matches across six observed priority values, and a
configured mapping column with no observed values. The combined result is 9
matches across 12 non-empty cells. It demonstrates deterministic counting and
zero-denominator behavior, not mapping quality for other datasets.

The unmatched-frequency check verifies descending counts of four for
`unknown`, three for `alpha`, and two for `beta`. The latter two are valid
canonical values, while `unknown` is deliberately invalid. This demonstrates
frequency ordering and the need for domain review, not automatic mapping
recommendations.

The privacy-mode check verifies identical mapping coverage across three
columns while varying disclosure. Raw mode preserves values, redacted mode
retains ranked counts of 4, 2, and 1 without source strings, and disabled mode
retains no distinct-value or frequency detail. The clean CSV still contains
non-mapped values, demonstrating that these modes protect frequency summaries
rather than anonymizing every output artifact.
