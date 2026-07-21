# Reference Results

These files are deterministic outputs from three synthetic, non-sensitive
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

Regenerate them from the repository root with:

```bash
python examples/run_demo.py
```

The demo deliberately contains invalid and malformed rows. The underlying
`inspect` and `clean` commands therefore return exit code 1. The value-mapping
sample also returns 1 because its final row is deliberately invalid. The
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
