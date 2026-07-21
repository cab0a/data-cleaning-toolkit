from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from data_cleaning_toolkit.csv_table import CsvFormatError, read_csv_table
from data_cleaning_toolkit.inspection import inspect_table


def test_reader_records_malformed_rows_without_stopping(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("a,b\n1,2\n3\n4,5,6\n", encoding="utf-8")

    table = read_csv_table(source)

    assert [row.values for row in table.rows] == [
        {"a": "1", "b": "2"},
        {"a": "3", "b": ""},
        {"a": "4", "b": "5"},
    ]
    assert [issue.code for issue in table.issues] == [
        "ROW_WIDTH_MISMATCH",
        "ROW_WIDTH_MISMATCH",
    ]
    assert [issue.row for issue in table.issues] == [3, 4]


def test_reader_accepts_utf8_bom_and_rejects_duplicate_headers(
    tmp_path: Path,
) -> None:
    valid = tmp_path / "bom.csv"
    valid.write_text("\ufeffname,value\nalpha,1\n", encoding="utf-8")
    assert read_csv_table(valid).headers == ["name", "value"]

    duplicate = tmp_path / "duplicate.csv"
    duplicate.write_text("name,name\na,b\n", encoding="utf-8")
    with pytest.raises(CsvFormatError, match="duplicate column names"):
        read_csv_table(duplicate)


def test_inspection_counts_empty_cells_and_exact_duplicate_rows(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.csv"
    source.write_text(
        "name,value\nalpha,1\nalpha,1\n   ,2\nbeta,\n",
        encoding="utf-8",
    )

    report = inspect_table(read_csv_table(source))

    assert report["input_rows"] == 4
    assert report["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["column_count"] == 2
    assert report["duplicate_rows"] == 1
    assert report["malformed_rows"] == 0
    assert report["columns"] == [
        {
            "name": "name",
            "empty_cells": 1,
            "non_empty_cells": 3,
            "distinct_non_empty_values": 2,
        },
        {
            "name": "value",
            "empty_cells": 1,
            "non_empty_cells": 3,
            "distinct_non_empty_values": 2,
        },
    ]
