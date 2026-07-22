"""Schema-driven row normalization, validation, and deduplication."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import (
    UNMATCHED_VALUE_LIMIT,
    CleaningResult,
    CsvTable,
    DataIssue,
    MappingCoverage,
)
from .schema import (
    CleaningSchema,
    ColumnRule,
    ConditionalPresenceRule,
    CrossColumnRule,
)


COMPARISON_DESCRIPTIONS = {
    "equal": "equal",
    "not_equal": "differ from",
    "less_than": "be less than",
    "less_than_or_equal": "be less than or equal to",
    "greater_than": "be greater than",
    "greater_than_or_equal": "be greater than or equal to",
}


class SchemaMismatchError(ValueError):
    """The input columns cannot be reconciled with the cleaning schema."""


def _canonical_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def _issue(
    code: str,
    message: str,
    *,
    row: int,
    column: str,
    value: str,
) -> DataIssue:
    return DataIssue(
        severity="error",
        code=code,
        message=message,
        row=row,
        column=column,
        value=value,
    )


def _normalize_value(
    raw: str,
    rule: ColumnRule,
    *,
    row_number: int,
) -> tuple[str, list[DataIssue], bool, str | None]:
    value = raw.strip() if rule.strip else raw
    if value in rule.null_values:
        value = ""
    mapping_source = value if rule.value_mapping and value != "" else None
    if value == "":
        if rule.required:
            return value, [
                _issue(
                    "MISSING_REQUIRED_VALUE",
                    "Required value is empty",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            ], False, mapping_source
        return value, [], False, mapping_source

    issues: list[DataIssue] = []
    mapped = False
    for source, target in rule.value_mapping:
        if value == source:
            value = target
            mapped = True
            issues.append(
                DataIssue(
                    severity="info",
                    code="VALUE_MAPPED",
                    message=f"Mapped value to {target!r}",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            )
            break
    numeric_value: Decimal | None = None

    if rule.data_type == "string":
        if rule.case == "lower":
            value = value.lower()
        elif rule.case == "upper":
            value = value.upper()
    elif rule.data_type == "integer":
        if re.fullmatch(r"[+-]?\d+", value) is None:
            issues.append(
                _issue(
                    "INVALID_INTEGER",
                    "Value is not an integer",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            )
        else:
            try:
                value = str(int(value))
                numeric_value = Decimal(value)
            except ValueError:
                issues.append(
                    _issue(
                        "INVALID_INTEGER",
                        "Integer exceeds the supported conversion size",
                        row=row_number,
                        column=rule.name,
                        value=raw,
                    )
                )
    elif rule.data_type == "decimal":
        try:
            numeric_value = Decimal(value)
            if not numeric_value.is_finite():
                raise InvalidOperation
            value = _canonical_decimal(numeric_value)
        except InvalidOperation:
            numeric_value = None
            issues.append(
                _issue(
                    "INVALID_DECIMAL",
                    "Value is not a finite decimal number",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            )
    elif rule.data_type == "boolean":
        folded = value.casefold()
        if folded in {item.casefold() for item in rule.true_values}:
            value = "true"
        elif folded in {item.casefold() for item in rule.false_values}:
            value = "false"
        else:
            issues.append(
                _issue(
                    "INVALID_BOOLEAN",
                    "Value is not in the configured true or false values",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            )
    elif rule.data_type == "date":
        try:
            parsed = datetime.strptime(value, rule.input_format)
            value = parsed.strftime(rule.output_format)
        except ValueError:
            issues.append(
                _issue(
                    "INVALID_DATE",
                    f"Value does not match date format {rule.input_format}",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            )

    if (
        not any(issue.severity == "error" for issue in issues)
        and rule.allowed_values
        and value not in rule.allowed_values
    ):
        issues.append(
            _issue(
                "VALUE_NOT_ALLOWED",
                "Value is not in the configured allowed values",
                row=row_number,
                column=rule.name,
                value=raw,
            )
        )
    if (
        not any(issue.severity == "error" for issue in issues)
        and rule.pattern is not None
        and re.fullmatch(rule.pattern, value) is None
    ):
        issues.append(
            _issue(
                "PATTERN_MISMATCH",
                "Value does not match the configured regular expression",
                row=row_number,
                column=rule.name,
                value=raw,
            )
        )
    if numeric_value is not None:
        if rule.minimum is not None and numeric_value < rule.minimum:
            issues.append(
                _issue(
                    "VALUE_BELOW_MINIMUM",
                    f"Value is below minimum {rule.minimum}",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            )
        if rule.maximum is not None and numeric_value > rule.maximum:
            issues.append(
                _issue(
                    "VALUE_ABOVE_MAXIMUM",
                    f"Value is above maximum {rule.maximum}",
                    row=row_number,
                    column=rule.name,
                    value=raw,
                )
            )
    return value, issues, mapped, mapping_source


def _output_headers(table: CsvTable, schema: CleaningSchema) -> list[str]:
    schema_headers = [rule.name for rule in schema.columns]
    schema_names = set(schema_headers)
    input_names = set(table.headers)

    missing_required = [
        rule.name
        for rule in schema.columns
        if rule.required and rule.name not in input_names
    ]
    if missing_required:
        raise SchemaMismatchError(
            "Input is missing required columns: " + ", ".join(missing_required)
        )

    unknown = [header for header in table.headers if header not in schema_names]
    if unknown and schema.unknown_columns == "error":
        raise SchemaMismatchError(
            "Input contains columns not defined by the schema: " + ", ".join(unknown)
        )
    if schema.unknown_columns == "drop":
        return schema_headers
    return table.headers + [name for name in schema_headers if name not in input_names]


def _comparison_value(value: str, rule: ColumnRule) -> Any:
    if rule.data_type in {"integer", "decimal"}:
        return Decimal(value)
    if rule.data_type == "date":
        return datetime.strptime(value, rule.output_format)
    return value


def _comparison_holds(left: Any, operator: str, right: Any) -> bool:
    if operator == "equal":
        return left == right
    if operator == "not_equal":
        return left != right
    if operator == "less_than":
        return left < right
    if operator == "less_than_or_equal":
        return left <= right
    if operator == "greater_than":
        return left > right
    if operator == "greater_than_or_equal":
        return left >= right
    raise ValueError(f"Unsupported comparison operator: {operator}")


def _cross_column_issue(
    normalized: dict[str, str],
    rule: CrossColumnRule,
    column_rules: dict[str, ColumnRule],
    *,
    row_number: int,
) -> DataIssue | None:
    left_value = normalized[rule.left]
    right_value = normalized[rule.right]
    if left_value == "" or right_value == "":
        return None

    left = _comparison_value(left_value, column_rules[rule.left])
    right = _comparison_value(right_value, column_rules[rule.right])
    if _comparison_holds(left, rule.operator, right):
        return None

    return DataIssue(
        severity="error",
        code="CROSS_COLUMN_RULE_FAILED",
        message=(
            f"Cross-column rule requires {rule.left} to "
            f"{COMPARISON_DESCRIPTIONS[rule.operator]} {rule.right}"
        ),
        row=row_number,
        value=f"{rule.left}={left_value!r} | {rule.right}={right_value!r}",
        rule=rule.name,
    )


def _conditional_presence_issue(
    normalized: dict[str, str],
    rule: ConditionalPresenceRule,
    *,
    row_number: int,
) -> DataIssue | None:
    condition_value = normalized[rule.when_present]
    required_value = normalized[rule.require]
    if condition_value == "" or required_value != "":
        return None

    return DataIssue(
        severity="error",
        code="CONDITIONAL_REQUIRED_VALUE_MISSING",
        message=f"{rule.require} is required when {rule.when_present} is present",
        row=row_number,
        column=rule.require,
        value=f"{rule.when_present}={condition_value!r}",
        rule=rule.name,
    )


def clean_table(table: CsvTable, schema: CleaningSchema) -> CleaningResult:
    headers = _output_headers(table, schema)
    column_rules = schema.column_map
    structural_by_row: dict[int, list[DataIssue]] = defaultdict(list)
    for issue in table.issues:
        if issue.row is not None:
            structural_by_row[issue.row].append(issue)

    output_rows: list[dict[str, str]] = []
    issues: list[DataIssue] = []
    seen_keys: set[tuple[str, ...]] = set()
    invalid_rows = 0
    dropped_invalid_rows = 0
    duplicate_rows_removed = 0
    mapped_cells = 0
    transformed_cells = 0
    mapping_observed_by_column = {
        rule.name: 0 for rule in schema.columns if rule.value_mapping
    }
    mapping_mapped_by_column = dict.fromkeys(mapping_observed_by_column, 0)
    mapping_unmatched_by_column = {
        rule.name: Counter()
        for rule in schema.columns
        if rule.value_mapping and rule.unmatched_value_mode != "disabled"
    }

    for row in table.rows:
        normalized = dict(row.values)
        row_issues = list(structural_by_row[row.row_number])

        for rule in schema.columns:
            raw = row.values.get(rule.name, "")
            value, value_issues, mapped, mapping_source = _normalize_value(
                raw,
                rule,
                row_number=row.row_number,
            )
            normalized[rule.name] = value
            row_issues.extend(value_issues)
            if mapped:
                mapped_cells += 1
                mapping_mapped_by_column[rule.name] += 1
            if mapping_source is not None:
                mapping_observed_by_column[rule.name] += 1
                if not mapped:
                    unmatched_counts = mapping_unmatched_by_column.get(rule.name)
                    if unmatched_counts is not None:
                        unmatched_counts[mapping_source] += 1
            if value != raw:
                transformed_cells += 1

        for presence_rule in schema.conditional_presence_rules:
            presence_issue = _conditional_presence_issue(
                normalized,
                presence_rule,
                row_number=row.row_number,
            )
            if presence_issue is not None:
                row_issues.append(presence_issue)

        invalid_columns = {
            issue.column
            for issue in row_issues
            if issue.severity == "error" and issue.column is not None
        }
        for cross_rule in schema.cross_column_rules:
            if (
                cross_rule.left in invalid_columns
                or cross_rule.right in invalid_columns
            ):
                continue
            cross_issue = _cross_column_issue(
                normalized,
                cross_rule,
                column_rules,
                row_number=row.row_number,
            )
            if cross_issue is not None:
                row_issues.append(cross_issue)

        if schema.deduplicate_by:
            empty_keys = [
                name for name in schema.deduplicate_by if normalized[name] == ""
            ]
            if empty_keys:
                row_issues.append(
                    DataIssue(
                        severity="error",
                        code="EMPTY_DEDUPLICATION_KEY",
                        message=(
                            "Deduplication key contains empty values: "
                            + ", ".join(empty_keys)
                        ),
                        row=row.row_number,
                    )
                )

        has_errors = any(issue.severity == "error" for issue in row_issues)
        if has_errors:
            invalid_rows += 1
        issues.extend(row_issues)

        if has_errors and schema.invalid_rows == "drop":
            dropped_invalid_rows += 1
            continue

        if schema.deduplicate_by:
            key = tuple(normalized[name] for name in schema.deduplicate_by)
            if key in seen_keys:
                duplicate_rows_removed += 1
                issues.append(
                    DataIssue(
                        severity="warning",
                        code="DUPLICATE_KEY",
                        message=(
                            "Duplicate key removed; first row kept for "
                            + ", ".join(schema.deduplicate_by)
                        ),
                        row=row.row_number,
                        value=" | ".join(key),
                    )
                )
                continue
            seen_keys.add(key)

        output_rows.append({header: normalized.get(header, "") for header in headers})

    mapping_coverage: list[MappingCoverage] = []
    for rule in schema.columns:
        if not rule.value_mapping:
            continue
        unmatched_counts = mapping_unmatched_by_column.get(rule.name)
        if unmatched_counts is None:
            distinct_unmatched_values = None
            frequencies: tuple[tuple[str | None, int], ...] = ()
        else:
            sorted_frequencies = sorted(
                unmatched_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[:UNMATCHED_VALUE_LIMIT]
            distinct_unmatched_values = len(unmatched_counts)
            if rule.unmatched_value_mode == "redacted":
                frequencies = tuple((None, count) for _, count in sorted_frequencies)
            else:
                frequencies = tuple(sorted_frequencies)
        mapping_coverage.append(
            MappingCoverage(
                column=rule.name,
                observed_non_empty_cells=mapping_observed_by_column[rule.name],
                mapped_cells=mapping_mapped_by_column[rule.name],
                unmatched_value_mode=rule.unmatched_value_mode,
                distinct_unmatched_values=distinct_unmatched_values,
                unmatched_value_frequencies=frequencies,
            )
        )

    return CleaningResult(
        headers=headers,
        rows=output_rows,
        input_rows=len(table.rows),
        invalid_rows=invalid_rows,
        dropped_invalid_rows=dropped_invalid_rows,
        duplicate_rows_removed=duplicate_rows_removed,
        mapped_cells=mapped_cells,
        transformed_cells=transformed_cells,
        mapping_coverage=mapping_coverage,
        issues=issues,
    )
