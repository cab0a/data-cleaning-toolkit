"""Strict, deterministic CSV input and output helpers."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Iterable

from .models import CsvTable, DataIssue, TableRow


class CsvFormatError(ValueError):
    """The CSV cannot be represented as a table with unique headers."""


def read_csv_table(path: str | Path) -> CsvTable:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise CsvFormatError("CSV is empty and has no header row") from exc

        if not headers:
            raise CsvFormatError("CSV header row is empty")
        if any(header == "" for header in headers):
            raise CsvFormatError("CSV contains an empty column name")

        duplicates = sorted(
            {header for header in headers if headers.count(header) > 1}
        )
        if duplicates:
            raise CsvFormatError(
                "CSV contains duplicate column names: " + ", ".join(duplicates)
            )

        rows: list[TableRow] = []
        issues: list[DataIssue] = []
        width = len(headers)
        for row_number, raw_values in enumerate(reader, start=2):
            if len(raw_values) != width:
                issues.append(
                    DataIssue(
                        severity="error",
                        code="ROW_WIDTH_MISMATCH",
                        message=(
                            f"Expected {width} fields but found {len(raw_values)}"
                        ),
                        row=row_number,
                    )
                )
            values = (raw_values + [""] * width)[:width]
            rows.append(
                TableRow(
                    row_number=row_number,
                    values=dict(zip(headers, values, strict=True)),
                )
            )

    return CsvTable(source=source, headers=headers, rows=rows, issues=issues)


def write_csv_rows(
    path: str | Path,
    headers: list[str],
    rows: Iterable[dict[str, str]],
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(
                handle,
                fieldnames=headers,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, destination)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise
    return destination
