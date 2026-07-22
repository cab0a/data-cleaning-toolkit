# Cleaning Report Version 1

The `clean` command writes a UTF-8 JSON audit with `report_version` set to `1`.
This document defines the version 1 contract used by Data Cleaning Toolkit
0.9.0.

## Compatibility Policy

Consumers must inspect `report_version` before interpreting a report. Existing
version 1 fields and their meanings will not be removed or changed without a
new report version. Additive fields may be introduced, so consumers should
ignore unknown keys.

The package version and report version are independent. A package update can
retain `report_version: 1` when the serialized contract remains compatible.

## Identity and Provenance

| Field | Type | Meaning |
| --- | --- | --- |
| `report_version` | integer | Report contract version; currently `1` |
| `source` | string | Input path exactly as supplied to the CLI |
| `source_sha256` | string | Lowercase SHA-256 of the input bytes |
| `schema` | string | Schema path exactly as supplied to the CLI |
| `schema_version` | integer | Version declared by the cleaning schema |
| `schema_sha256` | string | Lowercase SHA-256 of the schema bytes |
| `output` | string | Clean CSV path exactly as supplied to the CLI |
| `output_sha256` | string | Lowercase SHA-256 of the clean CSV bytes |

Paths are evidence, not portable identifiers. Use the digests to compare file
contents across locations.

## Run Summary

| Field | Type | Meaning |
| --- | --- | --- |
| `input_rows` | integer | Data rows read after the header |
| `output_rows` | integer | Rows written to the clean CSV |
| `invalid_rows` | integer | Input rows with at least one error |
| `dropped_invalid_rows` | integer | Invalid rows removed by policy |
| `duplicate_rows_removed` | integer | Accepted rows removed by normalized key |
| `mapped_cells` | integer | Cells matching an explicit mapping source |
| `transformed_cells` | integer | Cells whose output differs from raw input |
| `cross_column_failures` | integer | Failed named cross-column rules |
| `conditional_presence_failures` | integer | Failed named presence dependencies |
| `error_count` | integer | Error-severity issue count |
| `warning_count` | integer | Warning-severity issue count |
| `issues_by_code` | object | Stable issue-code counts in key order |

Informational issues such as `VALUE_MAPPED` appear in `issues_by_code` and
`issues` but do not increment `error_count` or `warning_count`.

## Mapping Coverage

`mapping_coverage` contains overall exact-match counts and a `columns` array.
Overall fields are:

- `observed_non_empty_cells`
- `mapped_cells`
- `unmapped_cells`
- `coverage_rate`

`coverage_rate` is rounded to six decimal places and is `null` when the
denominator is zero. Every column entry adds:

- `column`
- `unmatched_value_mode`
- `distinct_unmatched_values`
- `unmatched_value_frequencies`
- `unmatched_values_truncated`

In `raw` mode, frequency entries contain `value` and `count`. In `redacted`
mode, entries contain `rank` and `count`. In `disabled` mode, the frequency
list is empty and the distinct and truncation fields are `null`. Mapping
coverage is an exact-match measurement, not a data-quality score.

## Issues

Each object in `issues` contains:

| Field | Type | Meaning |
| --- | --- | --- |
| `severity` | string | `info`, `warning`, or `error` |
| `code` | string | Stable machine-readable issue code |
| `message` | string | Human-readable explanation |
| `row` | integer or null | One-based CSV row number including the header |
| `column` | string or null | Related column name |
| `value` | string or null | Related source or normalized evidence |
| `rule` | string, optional | Named cross-column or presence rule |

Issue order follows input processing order. Consumers should use `code` and
structured fields for automation rather than parsing `message`.

## Privacy Boundary

Reports may contain source values in issue evidence and, in raw mode, mapping
frequencies. Redacted frequency mode does not redact row-level issues. Disabled
frequency mode does not redact the clean CSV, source, schema, or issue list.
Review the complete artifact before sharing it.

## Determinism

For identical input bytes, schema bytes, package version, command arguments,
and supported Python behavior, serialized field order and numeric rounding are
deterministic. Changing path arguments changes the path fields even when file
contents are identical. Reference reports therefore use repository-relative
paths.
