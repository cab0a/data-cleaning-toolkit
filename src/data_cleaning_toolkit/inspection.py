"""Schema-free structural inspection for CSV files."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .models import CsvTable
from .reporting import sha256_file


def inspect_table(table: CsvTable) -> dict[str, Any]:
    row_signatures = [
        tuple(row.values[header] for header in table.headers)
        for row in table.rows
    ]
    signature_counts = Counter(row_signatures)
    duplicate_rows = sum(count - 1 for count in signature_counts.values())

    columns: list[dict[str, Any]] = []
    for header in table.headers:
        values = [row.values[header] for row in table.rows]
        empty_cells = sum(value.strip() == "" for value in values)
        distinct_non_empty = {value for value in values if value.strip() != ""}
        columns.append(
            {
                "name": header,
                "empty_cells": empty_cells,
                "non_empty_cells": len(values) - empty_cells,
                "distinct_non_empty_values": len(distinct_non_empty),
            }
        )

    return {
        "report_version": 1,
        "source": table.source.as_posix(),
        "source_sha256": sha256_file(table.source),
        "input_rows": len(table.rows),
        "column_count": len(table.headers),
        "duplicate_rows": duplicate_rows,
        "malformed_rows": sum(
            issue.code == "ROW_WIDTH_MISMATCH" for issue in table.issues
        ),
        "columns": columns,
        "issues": [issue.as_dict() for issue in table.issues],
    }
