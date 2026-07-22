from __future__ import annotations

from pathlib import Path

import data_cleaning_toolkit
from data_cleaning_toolkit import (
    CleaningResult,
    CleaningSchema,
    CsvTable,
    clean_table,
    load_schema,
    read_csv_table,
    schema_from_mapping,
)
from examples.public_api_demo import main as public_api_demo


ROOT = Path(__file__).resolve().parents[1]


def test_supported_public_api_is_exported_from_package_root() -> None:
    expected = {
        "CleaningResult",
        "CleaningSchema",
        "ColumnRule",
        "ConditionalPresenceRule",
        "CrossColumnRule",
        "CsvFormatError",
        "CsvTable",
        "DataIssue",
        "MappingCoverage",
        "TableRow",
        "__version__",
        "clean_table",
        "inspect_table",
        "load_schema",
        "read_csv_table",
        "schema_from_mapping",
        "suggest_schema",
    }

    assert set(data_cleaning_toolkit.__all__) == expected
    assert all(hasattr(data_cleaning_toolkit, name) for name in expected)
    assert data_cleaning_toolkit.__version__ == "1.0.0"


def test_public_api_supports_file_and_in_memory_schemas() -> None:
    table = read_csv_table(ROOT / "examples" / "privacy_modes_demo.csv")
    loaded_schema = load_schema(ROOT / "examples" / "privacy_modes_schema.json")
    in_memory_schema = schema_from_mapping(
        {
            "columns": {
                "record_id": {"type": "integer", "required": True},
                "raw_category": {"type": "string"},
                "redacted_category": {"type": "string"},
                "disabled_category": {"type": "string"},
            }
        }
    )

    assert isinstance(table, CsvTable)
    assert isinstance(loaded_schema, CleaningSchema)
    assert isinstance(in_memory_schema, CleaningSchema)
    assert isinstance(clean_table(table, loaded_schema), CleaningResult)
    assert len(clean_table(table, in_memory_schema).rows) == 8


def test_public_api_demo_is_reproducible(capsys) -> None:
    assert public_api_demo() == 0
    assert capsys.readouterr().out == (
        "Input rows: 8\n"
        "Output rows: 8\n"
        "Errors: 0\n"
        "Mapping columns:\n"
        "  raw_category: mode=raw, mapped=1/8\n"
        "  redacted_category: mode=redacted, mapped=1/8\n"
        "  disabled_category: mode=disabled, mapped=1/8\n"
    )


def test_typed_package_marker_is_present() -> None:
    package_dir = Path(data_cleaning_toolkit.__file__).resolve().parent
    assert (package_dir / "py.typed").is_file()
