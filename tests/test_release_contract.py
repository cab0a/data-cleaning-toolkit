from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

import data_cleaning_toolkit
from data_cleaning_toolkit import (
    CleaningResult,
    clean_table,
    inspect_table,
    load_schema,
    read_csv_table,
    schema_from_mapping,
    suggest_schema,
)
from data_cleaning_toolkit.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_consistent(capsys) -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)

    assert match is not None
    assert match.group(1) == data_cleaning_toolkit.__version__ == "1.0.0"
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == "1.0.0\n"


def test_documented_public_functions_keep_stable_parameters() -> None:
    expected_parameters = {
        read_csv_table: ("path",),
        load_schema: ("path",),
        schema_from_mapping: ("raw",),
        clean_table: ("table", "schema"),
        inspect_table: ("table",),
        suggest_schema: ("table", "date_format"),
    }

    for function, expected in expected_parameters.items():
        assert tuple(inspect.signature(function).parameters) == expected
    assert (
        inspect.signature(suggest_schema).parameters["date_format"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )


def test_cleaning_report_retains_required_version_one_fields() -> None:
    result = CleaningResult(
        headers=["record_id"],
        rows=[{"record_id": "1"}],
        input_rows=1,
        invalid_rows=0,
        dropped_invalid_rows=0,
        duplicate_rows_removed=0,
        mapped_cells=0,
        transformed_cells=0,
    )
    report = result.as_report(
        source="input.csv",
        output="clean.csv",
        schema="schema.json",
        schema_version=1,
        source_sha256="a" * 64,
        schema_sha256="b" * 64,
        output_sha256="c" * 64,
    )
    required_fields = {
        "report_version",
        "source",
        "source_sha256",
        "schema",
        "schema_version",
        "schema_sha256",
        "output",
        "output_sha256",
        "input_rows",
        "output_rows",
        "invalid_rows",
        "dropped_invalid_rows",
        "duplicate_rows_removed",
        "mapped_cells",
        "mapping_coverage",
        "transformed_cells",
        "cross_column_failures",
        "conditional_presence_failures",
        "error_count",
        "warning_count",
        "issues_by_code",
        "issues",
    }

    assert report["report_version"] == 1
    assert required_fields <= report.keys()
    assert {
        "observed_non_empty_cells",
        "mapped_cells",
        "unmapped_cells",
        "coverage_rate",
        "columns",
    } <= report["mapping_coverage"].keys()
