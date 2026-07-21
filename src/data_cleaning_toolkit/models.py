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

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "row": self.row,
            "column": self.column,
            "value": self.value,
        }


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


@dataclass(slots=True)
class CleaningResult:
    headers: list[str]
    rows: list[dict[str, str]]
    input_rows: int
    invalid_rows: int
    dropped_invalid_rows: int
    duplicate_rows_removed: int
    transformed_cells: int
    issues: list[DataIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

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
            "transformed_cells": self.transformed_cells,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues_by_code": dict(sorted(counts.items())),
            "issues": [issue.as_dict() for issue in self.issues],
        }
