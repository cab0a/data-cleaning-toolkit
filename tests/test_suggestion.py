from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_cleaning_toolkit.csv_table import read_csv_table
from data_cleaning_toolkit.schema import schema_from_mapping
from data_cleaning_toolkit.suggestion import suggest_schema


ROOT = Path(__file__).resolve().parents[1]


def test_controlled_demo_matches_expected_types() -> None:
    report = suggest_schema(
        read_csv_table(ROOT / "examples" / "schema_suggestion_demo.csv")
    )
    expected = json.loads(
        (ROOT / "examples" / "schema_suggestion_expected.json").read_text(
            encoding="utf-8"
        )
    )
    observed = {
        name: rule["type"]
        for name, rule in report["suggested_schema"]["columns"].items()
    }

    assert observed == expected
    assert report["input_rows"] == 6
    assert report["malformed_rows"] == 0
    schema_from_mapping(report["suggested_schema"])


def test_suggestion_reports_coverage_and_optional_values(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text(
        "value,note\n1, alpha \n2,\nnot-a-number,beta\n",
        encoding="utf-8",
    )

    report = suggest_schema(read_csv_table(source))
    value, note = report["columns"]

    assert value["suggested_type"] == "string"
    assert value["parse_coverage"]["integer"] == pytest.approx(2 / 3, abs=1e-6)
    assert note["required"] is False
    assert note["whitespace_changes"] == 1
    assert report["suggested_schema"]["columns"]["note"]["strip"] is True


def test_leading_zero_identifiers_remain_strings(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("postal_code\n00123\n00124\n", encoding="utf-8")

    report = suggest_schema(read_csv_table(source))
    column = report["columns"][0]

    assert column["leading_zero_values"] == 2
    assert column["suggested_type"] == "string"
    assert column["parse_coverage"]["integer"] == 0.0
    assert column["parse_coverage"]["decimal"] == 0.0


def test_alternate_date_format_can_be_selected(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("event_date\n31/12/2025\n01/01/2026\n", encoding="utf-8")

    report = suggest_schema(
        read_csv_table(source),
        date_format="%d/%m/%Y",
    )

    assert report["columns"][0]["suggested_type"] == "date"
    assert report["suggested_schema"]["columns"]["event_date"] == {
        "type": "date",
        "required": True,
        "input_format": "%d/%m/%Y",
        "output_format": "%d/%m/%Y",
    }


def test_empty_table_does_not_suggest_required_columns(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("record_id,note\n", encoding="utf-8")

    report = suggest_schema(read_csv_table(source))

    assert report["suggested_schema"]["columns"] == {
        "record_id": {"type": "string", "required": False},
        "note": {"type": "string", "required": False},
    }
