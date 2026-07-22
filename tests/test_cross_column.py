from __future__ import annotations

from pathlib import Path

import pytest

from data_cleaning_toolkit.cleaning import clean_table
from data_cleaning_toolkit.csv_table import read_csv_table
from data_cleaning_toolkit.schema import load_schema, schema_from_mapping


ROOT = Path(__file__).resolve().parents[1]


def test_controlled_cross_column_rules_use_normalized_values() -> None:
    table = read_csv_table(ROOT / "examples" / "cross_column_demo.csv")
    schema = load_schema(ROOT / "examples" / "cross_column_schema.json")

    result = clean_table(table, schema)

    assert result.rows == [
        {
            "record_id": "1",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "minimum_value": "10",
            "maximum_value": "20",
            "confirmation_code": "A1",
            "reported_code": "A1",
        },
        {
            "record_id": "2",
            "period_start": "2026-02-15",
            "period_end": "2026-02-15",
            "minimum_value": "-5",
            "maximum_value": "-5",
            "confirmation_code": "B2",
            "reported_code": "B2",
        },
        {
            "record_id": "7",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "minimum_value": "",
            "maximum_value": "",
            "confirmation_code": "G7",
            "reported_code": "G7",
        },
    ]
    assert result.invalid_rows == 4
    assert result.dropped_invalid_rows == 4
    assert result.cross_column_failure_count == 6
    assert result.error_count == 6
    assert {issue.rule for issue in result.issues} == {
        "period_order",
        "value_range_order",
        "code_match",
    }


def test_cross_column_rules_do_not_duplicate_column_errors(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text(
        "period_start,period_end\nnot-a-date,2026-01-31\n",
        encoding="utf-8",
    )
    schema = schema_from_mapping(
        {
            "invalid_rows": "keep",
            "columns": {
                "period_start": {"type": "date"},
                "period_end": {"type": "date"},
            },
            "cross_column_rules": [
                {
                    "name": "period_order",
                    "left": "period_start",
                    "operator": "less_than_or_equal",
                    "right": "period_end",
                }
            ],
        }
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.rows[0]["period_start"] == "not-a-date"
    assert result.error_count == 1
    assert result.cross_column_failure_count == 0
    assert result.issues[0].code == "INVALID_DATE"


@pytest.mark.parametrize(
    ("operator", "left", "right", "expected_failures"),
    [
        ("equal", "2", "2", 0),
        ("equal", "2", "3", 1),
        ("not_equal", "2", "3", 0),
        ("not_equal", "2", "2", 1),
        ("less_than", "2", "3", 0),
        ("less_than", "3", "2", 1),
        ("less_than_or_equal", "3", "3", 0),
        ("less_than_or_equal", "4", "3", 1),
        ("greater_than", "3", "2", 0),
        ("greater_than", "2", "3", 1),
        ("greater_than_or_equal", "3", "3", 0),
        ("greater_than_or_equal", "2", "3", 1),
    ],
)
def test_each_cross_column_operator(
    tmp_path: Path,
    operator: str,
    left: str,
    right: str,
    expected_failures: int,
) -> None:
    source = tmp_path / "input.csv"
    source.write_text(f"left,right\n{left},{right}\n", encoding="utf-8")
    schema = schema_from_mapping(
        {
            "invalid_rows": "keep",
            "columns": {
                "left": {"type": "integer"},
                "right": {"type": "integer"},
            },
            "cross_column_rules": [
                {
                    "name": "comparison",
                    "left": "left",
                    "operator": operator,
                    "right": "right",
                }
            ],
        }
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.cross_column_failure_count == expected_failures
