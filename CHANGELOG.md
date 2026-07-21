# Changelog

All notable changes to this project are documented in this file.

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
