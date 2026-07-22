from __future__ import annotations

from pathlib import Path

from data_cleaning_toolkit.cleaning import clean_table
from data_cleaning_toolkit.csv_table import read_csv_table
from data_cleaning_toolkit.schema import load_schema, schema_from_mapping


ROOT = Path(__file__).resolve().parents[1]


def test_controlled_conditional_presence_rules_use_normalized_values() -> None:
    table = read_csv_table(ROOT / "examples" / "conditional_presence_demo.csv")
    schema = load_schema(ROOT / "examples" / "conditional_presence_schema.json")

    result = clean_table(table, schema)

    assert result.rows == [
        {
            "record_id": "1",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "reviewer": "Aiko",
            "reviewed_at": "2026-02-01",
        },
        {
            "record_id": "2",
            "start_date": "",
            "end_date": "",
            "reviewer": "",
            "reviewed_at": "",
        },
        {
            "record_id": "3",
            "start_date": "",
            "end_date": "",
            "reviewer": "",
            "reviewed_at": "",
        },
        {
            "record_id": "7",
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
            "reviewer": "Ken",
            "reviewed_at": "",
        },
    ]
    assert result.invalid_rows == 3
    assert result.dropped_invalid_rows == 3
    assert result.conditional_presence_failure_count == 4
    assert result.error_count == 4
    assert {issue.rule for issue in result.issues} == {
        "start_required_when_end_present",
        "reviewer_required_when_reviewed_at_present",
    }


def test_invalid_condition_value_still_counts_as_present(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("start_date,end_date\n,not-a-date\n", encoding="utf-8")
    schema = schema_from_mapping(
        {
            "invalid_rows": "keep",
            "columns": {
                "start_date": {"type": "date"},
                "end_date": {"type": "date"},
            },
            "conditional_presence_rules": [
                {
                    "name": "start_required_when_end_present",
                    "when_present": "end_date",
                    "require": "start_date",
                }
            ],
        }
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.error_count == 2
    assert result.conditional_presence_failure_count == 1
    assert {issue.code for issue in result.issues} == {
        "INVALID_DATE",
        "CONDITIONAL_REQUIRED_VALUE_MISSING",
    }
