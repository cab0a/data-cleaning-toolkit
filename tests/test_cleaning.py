from __future__ import annotations

from pathlib import Path

import pytest

from data_cleaning_toolkit.cleaning import SchemaMismatchError, clean_table
from data_cleaning_toolkit.csv_table import read_csv_table
from data_cleaning_toolkit.schema import load_schema, schema_from_mapping


ROOT = Path(__file__).resolve().parents[1]


def test_demo_cleaning_normalizes_valid_rows_and_preserves_audit_evidence() -> None:
    table = read_csv_table(ROOT / "examples" / "demo_dirty.csv")
    schema = load_schema(ROOT / "examples" / "customer_schema.json")

    result = clean_table(table, schema)

    assert result.headers == [
        "customer_id",
        "full_name",
        "email",
        "country",
        "signup_date",
        "lifetime_value",
    ]
    assert result.rows == [
        {
            "customer_id": "1",
            "full_name": "Aiko Tanaka",
            "email": "aiko@example.com",
            "country": "JP",
            "signup_date": "2026-01-15",
            "lifetime_value": "1200.5",
        },
        {
            "customer_id": "2",
            "full_name": "Ken Ito",
            "email": "ken@example.com",
            "country": "US",
            "signup_date": "2026-02-01",
            "lifetime_value": "98",
        },
        {
            "customer_id": "5",
            "full_name": "Mina Lee",
            "email": "mina@example.com",
            "country": "GB",
            "signup_date": "2026-03-10",
            "lifetime_value": "",
        },
    ]
    assert result.input_rows == 7
    assert result.invalid_rows == 3
    assert result.dropped_invalid_rows == 3
    assert result.duplicate_rows_removed == 1
    assert result.mapped_cells == 0
    assert result.transformed_cells > 0
    assert result.error_count == 6
    assert result.warning_count == 1
    assert {issue.code for issue in result.issues} == {
        "DUPLICATE_KEY",
        "MISSING_REQUIRED_VALUE",
        "PATTERN_MISMATCH",
        "VALUE_NOT_ALLOWED",
        "INVALID_DATE",
        "VALUE_BELOW_MINIMUM",
        "ROW_WIDTH_MISMATCH",
    }


def test_invalid_rows_can_be_kept_with_original_invalid_value(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("id,amount\n001,not-a-number\n", encoding="utf-8")
    schema = schema_from_mapping(
        {
            "invalid_rows": "keep",
            "columns": {
                "id": {"type": "integer"},
                "amount": {"type": "decimal"},
            },
        }
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.invalid_rows == 1
    assert result.dropped_invalid_rows == 0
    assert result.rows == [{"id": "1", "amount": "not-a-number"}]
    assert result.issues[0].code == "INVALID_DECIMAL"


def test_boolean_date_and_numeric_rules_are_canonicalized(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text(
        "active,observed,count,score\nYES,21/07/2026,+003,10.500\n",
        encoding="utf-8",
    )
    schema = schema_from_mapping(
        {
            "columns": {
                "active": {
                    "type": "boolean",
                    "true_values": ["yes"],
                    "false_values": ["no"],
                },
                "observed": {
                    "type": "date",
                    "input_format": "%d/%m/%Y",
                    "output_format": "%Y-%m-%d",
                },
                "count": {"type": "integer", "min": 1, "max": 5},
                "score": {"type": "decimal", "min": 0},
            }
        }
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.error_count == 0
    assert result.rows == [
        {
            "active": "true",
            "observed": "2026-07-21",
            "count": "3",
            "score": "10.5",
        }
    ]


def test_negative_decimal_zero_is_canonicalized(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("value\n-0.000\n", encoding="utf-8")
    schema = schema_from_mapping(
        {"columns": {"value": {"type": "decimal"}}}
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.rows == [{"value": "0"}]


def test_unknown_columns_can_be_kept_dropped_or_rejected(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("id,legacy\n1,x\n", encoding="utf-8")
    table = read_csv_table(source)

    keep = schema_from_mapping(
        {"unknown_columns": "keep", "columns": {"id": {"type": "integer"}}}
    )
    assert clean_table(table, keep).rows == [{"id": "1", "legacy": "x"}]

    drop = schema_from_mapping(
        {"unknown_columns": "drop", "columns": {"id": {"type": "integer"}}}
    )
    assert clean_table(table, drop).rows == [{"id": "1"}]

    reject = schema_from_mapping(
        {"unknown_columns": "error", "columns": {"id": {"type": "integer"}}}
    )
    with pytest.raises(SchemaMismatchError, match="not defined"):
        clean_table(table, reject)


def test_missing_required_column_is_a_schema_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("name\nAiko\n", encoding="utf-8")
    schema = schema_from_mapping(
        {
            "columns": {
                "id": {"type": "integer", "required": True},
                "name": {"type": "string"},
            }
        }
    )

    with pytest.raises(SchemaMismatchError, match="missing required columns"):
        clean_table(read_csv_table(source), schema)


def test_explicit_value_mapping_precedes_type_conversion_and_validation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.csv"
    source.write_text(
        "country,active\n JP ,enabled\nXX,unknown\n",
        encoding="utf-8",
    )
    schema = schema_from_mapping(
        {
            "invalid_rows": "drop",
            "columns": {
                "country": {
                    "type": "string",
                    "strip": True,
                    "value_mapping": {"JP": "Japan"},
                    "allowed_values": ["Japan"],
                },
                "active": {
                    "type": "boolean",
                    "value_mapping": {"enabled": "true"},
                },
            },
        }
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.rows == [{"country": "Japan", "active": "true"}]
    assert result.mapped_cells == 2
    assert result.error_count == 2
    assert sum(issue.code == "VALUE_MAPPED" for issue in result.issues) == 2
    assert {issue.code for issue in result.issues if issue.severity == "error"} == {
        "VALUE_NOT_ALLOWED",
        "INVALID_BOOLEAN",
    }


def test_value_mapping_is_exact_and_case_sensitive(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    source.write_text("country\njp\n", encoding="utf-8")
    schema = schema_from_mapping(
        {
            "invalid_rows": "keep",
            "columns": {
                "country": {
                    "value_mapping": {"JP": "Japan"},
                    "allowed_values": ["Japan"],
                }
            },
        }
    )

    result = clean_table(read_csv_table(source), schema)

    assert result.rows == [{"country": "jp"}]
    assert result.mapped_cells == 0
    assert result.issues[0].code == "VALUE_NOT_ALLOWED"
