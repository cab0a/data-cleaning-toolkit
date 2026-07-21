# Reference Results

These files are deterministic outputs from two synthetic, non-sensitive
examples:

- `demo_inspection.json`, `demo_clean.csv`, and
  `demo_cleaning_report.json` come from the intentionally dirty CSV in
  `examples/demo_dirty.csv` and the versioned rules in
  `examples/customer_schema.json`.
- `demo_schema_suggestion.json` comes from the controlled type sample in
  `examples/schema_suggestion_demo.csv`.

Regenerate them from the repository root with:

```bash
python examples/run_demo.py
```

The demo deliberately contains invalid and malformed rows. The underlying
`inspect` and `clean` commands therefore return exit code 1, while the wrapper
accepts that documented result and exits successfully after writing those
artifacts and the schema-suggestion evidence.

The schema-suggestion sample defines seven expected column types in
`examples/schema_suggestion_expected.json`. The reproduction script verifies
that every observed suggestion matches that controlled reference. This is a
deterministic functional evaluation, not a benchmark for arbitrary datasets.
