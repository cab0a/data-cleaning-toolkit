from __future__ import annotations

from pathlib import Path

from data_cleaning_toolkit.cleaning import clean_table
from data_cleaning_toolkit.csv_table import read_csv_table
from data_cleaning_toolkit.schema import load_schema, schema_from_mapping


ROOT = Path(__file__).resolve().parents[1]


def test_controlled_mapping_coverage_uses_pre_mapping_normalized_values() -> None:
    table = read_csv_table(ROOT / "examples" / "mapping_coverage_demo.csv")
    schema = load_schema(ROOT / "examples" / "mapping_coverage_schema.json")

    result = clean_table(table, schema)

    assert len(result.rows) == 6
    assert result.invalid_rows == 1
    assert result.mapped_cells == 9
    assert [item.as_dict() for item in result.mapping_coverage] == [
        {
            "column": "country",
            "observed_non_empty_cells": 6,
            "mapped_cells": 3,
            "unmapped_cells": 3,
            "coverage_rate": 0.5,
            "distinct_unmatched_values": 3,
            "unmatched_value_frequencies": [
                {"value": "Japan", "count": 1},
                {"value": "United States", "count": 1},
                {"value": "ZZ", "count": 1},
            ],
            "unmatched_values_truncated": False,
        },
        {
            "column": "priority",
            "observed_non_empty_cells": 6,
            "mapped_cells": 6,
            "unmapped_cells": 0,
            "coverage_rate": 1.0,
            "distinct_unmatched_values": 0,
            "unmatched_value_frequencies": [],
            "unmatched_values_truncated": False,
        },
        {
            "column": "unused_code",
            "observed_non_empty_cells": 0,
            "mapped_cells": 0,
            "unmapped_cells": 0,
            "coverage_rate": None,
            "distinct_unmatched_values": 0,
            "unmatched_value_frequencies": [],
            "unmatched_values_truncated": False,
        },
    ]


def test_mapping_coverage_includes_rows_dropped_by_later_validation() -> None:
    table = read_csv_table(ROOT / "examples" / "mapping_coverage_demo.csv")
    schema = load_schema(ROOT / "examples" / "mapping_coverage_schema.json")

    result = clean_table(table, schema)

    country = result.mapping_coverage[0]
    assert country.observed_non_empty_cells == 6
    assert country.mapped_cells == 3
    assert country.unmapped_cells == 3


def test_controlled_unmatched_frequencies_are_sorted_by_count() -> None:
    table = read_csv_table(ROOT / "examples" / "unmatched_frequency_demo.csv")
    schema = load_schema(ROOT / "examples" / "unmatched_frequency_schema.json")

    result = clean_table(table, schema)
    coverage = result.mapping_coverage[0]

    assert len(result.rows) == 8
    assert result.invalid_rows == 4
    assert coverage.observed_non_empty_cells == 11
    assert coverage.mapped_cells == 2
    assert coverage.unmapped_cells == 9
    assert coverage.distinct_unmatched_values == 3
    assert coverage.unmatched_value_frequencies == (
        ("unknown", 4),
        ("alpha", 3),
        ("beta", 2),
    )
    assert coverage.unmatched_values_truncated is False


def test_unmatched_value_frequencies_are_limited_and_stably_sorted(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.csv"
    source.write_text(
        "code\n" + "\n".join(f"value-{index:02d}" for index in range(12)) + "\n",
        encoding="utf-8",
    )
    schema = schema_from_mapping(
        {
            "columns": {
                "code": {
                    "value_mapping": {"legacy": "canonical"},
                }
            }
        }
    )

    result = clean_table(read_csv_table(source), schema)
    coverage = result.mapping_coverage[0]

    assert coverage.distinct_unmatched_values == 12
    assert coverage.unmatched_value_frequencies == tuple(
        (f"value-{index:02d}", 1) for index in range(10)
    )
    assert coverage.unmatched_values_truncated is True
