# Changelog

All notable changes to this project are documented in this file.

## [0.6.0] - 2026-07-22

### Added

- Per-column mapping coverage counts for observed, mapped, and unmapped cells
- Overall mapping coverage totals and rates in JSON cleaning reports
- Compact CLI percentages with explicit `n/a` handling for empty columns
- Controlled partial, complete, and zero-denominator evaluation artifacts

### Changed

- Mapping coverage is measured after configured null handling and trimming and
  includes all input rows, even when later validation drops a row
- Expanded the reproducible demo workflow and test suite for per-column and
  overall summaries

## [0.5.0] - 2026-07-22

### Added

- Named `conditional_presence_rules` with `when_present` and `require` columns
- `CONDITIONAL_REQUIRED_VALUE_MISSING` audit events with rule names and
  normalized trigger values
- Conditional-presence failure totals in CLI output and JSON cleaning reports
- Controlled date and review-metadata dependency evaluation artifacts

### Changed

- Conditional-presence validation now runs after per-column normalization and
  validation and before cross-column validation
- Expanded the reproducible demo workflow and test suite for normalized nulls,
  whitespace-only targets, invalid triggers, schema rejection, and CLI output

## [0.4.0] - 2026-07-22

### Added

- Named `cross_column_rules` for comparing two normalized columns
- Equality and inequality operators for columns with matching configured types
- Ordering operators for integer, decimal, and date columns
- `CROSS_COLUMN_RULE_FAILED` audit events with rule names and normalized values
- Cross-column failure totals in CLI output and JSON cleaning reports
- Controlled date-order, numeric-range, and code-match evaluation artifacts

### Changed

- Cross-column validation now runs after per-column normalization and
  validation and before invalid-row filtering
- Expanded the reproducible demo workflow and test suite for relationship
  validation, empty operands, and error de-duplication

## [0.3.0] - 2026-07-21

### Added

- Exact, case-sensitive `value_mapping` rules for reviewed canonicalization
- `VALUE_MAPPED` row-level audit events with informational severity
- Mapped-cell counts in CLI output and cleaning reports
- Controlled value-mapping sample with committed clean and audit artifacts
- Tests for mapping order, strict matching, schema validation, and reporting

### Changed

- Documented value mapping as a distinct step before type conversion and
  validation
- Expanded the reproducible demo workflow to verify mapping behavior and
  deliberate unknown-value rejection

## [0.2.0] - 2026-07-21

### Added

- Conservative `suggest-schema` command with reviewable JSON output
- Per-column parse coverage for boolean, integer, decimal, and date candidates
- Required-field and whitespace-normalization suggestions from observed values
- Leading-zero protection for identifier-like integer strings
- Configurable date format for suggestion analysis
- Controlled seven-column evaluation sample and committed reference evidence

### Changed

- Expanded the reproducible demonstration workflow and CI artifact check
- Clarified the distinction between syntactic suggestions and reviewed rules
- Standardized the README introduction in English

## [0.1.0] - 2026-07-21

### Added

- Schema-free CSV structural inspection with JSON output
- Versioned JSON schemas for deterministic normalization and validation
- String, integer, decimal, boolean, and date handling
- Required-value, allowed-value, regular-expression, and numeric-bound checks
- Configurable unknown-column and invalid-row policies
- Normalized-key deduplication with first accepted row retention
- Row-level audit reports with stable issue codes and SHA-256 provenance
- Atomic replacement for individual CSV and JSON output files
- Demonstration data, reproducible reference results, tests, and CI
