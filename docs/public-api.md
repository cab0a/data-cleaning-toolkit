# Public Python API

Version 1.0.0 defines the supported programmatic interface at the
`data_cleaning_toolkit` package root. The command-line interface remains the
recommended path when atomic file output and SHA-256 provenance are required.

## Stability Boundary

Names listed in `data_cleaning_toolkit.__all__` are public. Imports from
submodules such as `data_cleaning_toolkit.cleaning` are implementation details
and may change without notice.

The package includes a `py.typed` marker, so type checkers can use its inline
annotations. Runtime dependencies remain limited to the Python standard
library.

During the 1.x series, documented public names will not be removed or renamed,
and their required parameters and documented meanings will not change
incompatibly. Compatible releases may add public names, optional parameters,
or model fields. A change that requires existing callers to be rewritten will
require a new major package version.

The public compatibility boundary does not include exception message text,
human-readable console wording, ordering of undocumented collections, or
imports from package submodules. The CLI commands, required arguments, and
documented exit-code meanings are supported throughout the 1.x series. JSON
consumers should follow the separate `report_version` contract rather than
parsing console output.

## Example

```python
from data_cleaning_toolkit import clean_table, load_schema, read_csv_table

table = read_csv_table("examples/privacy_modes_demo.csv")
schema = load_schema("examples/privacy_modes_schema.json")
result = clean_table(table, schema)

print(result.input_rows)
print(len(result.rows))
print(result.error_count)
```

The executable equivalent is
[`examples/public_api_demo.py`](../examples/public_api_demo.py).

## Functions

| Function | Purpose |
| --- | --- |
| `read_csv_table(path)` | Read a UTF-8 CSV into a `CsvTable` and retain structural issues |
| `load_schema(path)` | Load and validate a versioned JSON cleaning schema |
| `schema_from_mapping(raw)` | Validate an in-memory mapping as a cleaning schema |
| `clean_table(table, schema)` | Normalize, validate, and deduplicate a table in memory |
| `inspect_table(table)` | Return structural inspection evidence as a dictionary |
| `suggest_schema(table, date_format=...)` | Return a conservative schema candidate and its evidence |

`read_csv_table` does not raise for malformed row widths; it records those
rows as issues so inspection and cleaning can report them. Empty files and
duplicate or empty headers raise the public `CsvFormatError`. Invalid schemas,
unreadable files, invalid UTF-8, and filesystem errors raise exceptions rather
than producing partial output.

## Data Models

The root package exports the models used in public function signatures:

- `CsvTable` and `TableRow` represent parsed source data; `CsvFormatError`
  identifies table structures that cannot be represented safely.
- `CleaningSchema`, `ColumnRule`, `CrossColumnRule`, and
  `ConditionalPresenceRule` represent validated rules.
- `CleaningResult`, `MappingCoverage`, and `DataIssue` represent cleaning
  output and evidence.

`CleaningResult.rows` contains normalized string values in output order.
`CleaningResult.issues` contains informational mapping events, validation
errors, and deduplication warnings. No files are written by `clean_table`.

## Version Access

```python
from data_cleaning_toolkit import __version__

print(__version__)
```

Code that depends on a report field should also check `report_version`; the
package version and report format version are separate contracts.

## CLI and API Responsibilities

Use the Python API for in-memory composition, tests, and notebooks. Use the CLI
when the workflow requires:

- atomic clean CSV and JSON report replacement;
- input, schema, and output SHA-256 digests;
- standardized exit codes for CI or shell scripts; or
- the documented console summary.

The API does not silently reproduce the CLI's file-writing and provenance
steps. This separation keeps side effects explicit.
