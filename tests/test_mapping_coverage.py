from __future__ import annotations

from pathlib import Path

from data_cleaning_toolkit.cleaning import clean_table
from data_cleaning_toolkit.csv_table import read_csv_table
from data_cleaning_toolkit.schema import load_schema


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
        },
        {
            "column": "priority",
            "observed_non_empty_cells": 6,
            "mapped_cells": 6,
            "unmapped_cells": 0,
            "coverage_rate": 1.0,
        },
        {
            "column": "unused_code",
            "observed_non_empty_cells": 0,
            "mapped_cells": 0,
            "unmapped_cells": 0,
            "coverage_rate": None,
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
