"""Shared data models for CSV inspection and cleaning."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DataIssue:
    severity: str
    code: str
    message: str
    row: int | None = None
    column: str | None = None
    value: str | None = None
    rule: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "row": self.row,
            "column": self.column,
            "value": self.value,
        }
        if self.rule is not None:
            data["rule"] = self.rule
        return data


@dataclass(frozen=True, slots=True)
class TableRow:
    row_number: int
    values: dict[str, str]


@dataclass(slots=True)
class CsvTable:
    source: Path
    headers: list[str]
    rows: list[TableRow]
    issues: list[DataIssue] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class MappingCoverage:
    column: str
    observed_non_empty_cells: int
    mapped_cells: int

    @property
    def unmapped_cells(self) -> int:
        return self.observed_non_empty_cells - self.mapped_cells

    @property
    def coverage_rate(self) -> float | None:
        if self.observed_non_empty_cells == 0:
            return None
        return round(self.mapped_cells / self.observed_non_empty_cells, 6)

    def as_dict(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "observed_non_empty_cells": self.observed_non_empty_cells,
            "mapped_cells": self.mapped_cells,
            "unmapped_cells": self.unmapped_cells,
            "coverage_rate": self.coverage_rate,
        }


@dataclass(slots=True)
class CleaningResult:
    headers: list[str]
    rows: list[dict[str, str]]
    input_rows: int
    invalid_rows: int
    dropped_invalid_rows: int
    duplicate_rows_removed: int
    mapped_cells: int
    transformed_cells: int
    mapping_coverage: list[MappingCoverage] = field(default_factory=list)
    issues: list[DataIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    @property
    def cross_column_failure_count(self) -> int:
        return sum(
            issue.code == "CROSS_COLUMN_RULE_FAILED" for issue in self.issues
        )

    @property
    def conditional_presence_failure_count(self) -> int:
        return sum(
            issue.code == "CONDITIONAL_REQUIRED_VALUE_MISSING"
            for issue in self.issues
        )

    def as_report(
        self,
        *,
        source: str,
        output: str,
        schema: str,
        schema_version: int,
        source_sha256: str,
        schema_sha256: str,
        output_sha256: str,
    ) -> dict[str, Any]:
        counts = Counter(issue.code for issue in self.issues)
        coverage_observed = sum(
            item.observed_non_empty_cells for item in self.mapping_coverage
        )
        coverage_mapped = sum(item.mapped_cells for item in self.mapping_coverage)
        coverage_rate = (
            round(coverage_mapped / coverage_observed, 6)
            if coverage_observed
            else None
        )
        return {
            "report_version": 1,
            "source": source,
            "source_sha256": source_sha256,
            "schema": schema,
            "schema_version": schema_version,
            "schema_sha256": schema_sha256,
            "output": output,
            "output_sha256": output_sha256,
            "input_rows": self.input_rows,
            "output_rows": len(self.rows),
            "invalid_rows": self.invalid_rows,
            "dropped_invalid_rows": self.dropped_invalid_rows,
            "duplicate_rows_removed": self.duplicate_rows_removed,
            "mapped_cells": self.mapped_cells,
            "mapping_coverage": {
                "observed_non_empty_cells": coverage_observed,
                "mapped_cells": coverage_mapped,
                "unmapped_cells": coverage_observed - coverage_mapped,
                "coverage_rate": coverage_rate,
                "columns": [item.as_dict() for item in self.mapping_coverage],
            },
            "transformed_cells": self.transformed_cells,
            "cross_column_failures": self.cross_column_failure_count,
            "conditional_presence_failures": (
                self.conditional_presence_failure_count
            ),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues_by_code": dict(sorted(counts.items())),
            "issues": [issue.as_dict() for issue in self.issues],
        }
