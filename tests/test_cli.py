from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

from data_cleaning_toolkit.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_inspect_writes_report_and_signals_malformed_rows(
    tmp_path: Path,
    capsys,
) -> None:
    report = tmp_path / "inspection.json"

    status = main(
        [
            "inspect",
            str(ROOT / "examples" / "demo_dirty.csv"),
            "--output",
            str(report),
        ]
    )

    assert status == 1
    assert json.loads(report.read_text(encoding="utf-8"))["malformed_rows"] == 1
    assert "Malformed rows: 1" in capsys.readouterr().out


def test_clean_writes_csv_and_audit_report_with_documented_exit_code(
    tmp_path: Path,
    capsys,
) -> None:
    output = tmp_path / "clean.csv"
    report = tmp_path / "audit.json"

    status = main(
        [
            "clean",
            str(ROOT / "examples" / "demo_dirty.csv"),
            "--schema",
            str(ROOT / "examples" / "customer_schema.json"),
            "--output",
            str(output),
            "--report",
            str(report),
        ]
    )

    assert status == 1
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    audit = json.loads(report.read_text(encoding="utf-8"))
    assert audit["input_rows"] == 7
    assert audit["output_rows"] == 3
    assert audit["invalid_rows"] == 3
    assert audit["duplicate_rows_removed"] == 1
    assert audit["mapped_cells"] == 0
    assert audit["cross_column_failures"] == 0
    assert audit["conditional_presence_failures"] == 0
    assert audit["schema_version"] == 1
    assert audit["source_sha256"] == hashlib.sha256(
        (ROOT / "examples" / "demo_dirty.csv").read_bytes()
    ).hexdigest()
    assert audit["schema_sha256"] == hashlib.sha256(
        (ROOT / "examples" / "customer_schema.json").read_bytes()
    ).hexdigest()
    assert audit["output_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert "Audit report:" in capsys.readouterr().out


def test_clean_reports_explicit_value_mappings(capsys, tmp_path: Path) -> None:
    output = tmp_path / "clean.csv"
    report = tmp_path / "audit.json"

    status = main(
        [
            "clean",
            str(ROOT / "examples" / "value_mapping_demo.csv"),
            "--schema",
            str(ROOT / "examples" / "value_mapping_schema.json"),
            "--output",
            str(output),
            "--report",
            str(report),
        ]
    )

    assert status == 1
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    audit = json.loads(report.read_text(encoding="utf-8"))
    assert audit["mapped_cells"] == 13
    assert audit["issues_by_code"]["VALUE_MAPPED"] == 13
    assert audit["error_count"] == 3
    assert "Mapped cells: 13" in capsys.readouterr().out


def test_clean_reports_cross_column_failures(capsys, tmp_path: Path) -> None:
    output = tmp_path / "clean.csv"
    report = tmp_path / "audit.json"

    status = main(
        [
            "clean",
            str(ROOT / "examples" / "cross_column_demo.csv"),
            "--schema",
            str(ROOT / "examples" / "cross_column_schema.json"),
            "--output",
            str(output),
            "--report",
            str(report),
        ]
    )

    assert status == 1
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    audit = json.loads(report.read_text(encoding="utf-8"))
    assert audit["cross_column_failures"] == 6
    assert audit["issues_by_code"]["CROSS_COLUMN_RULE_FAILED"] == 6
    assert {issue["rule"] for issue in audit["issues"]} == {
        "period_order",
        "value_range_order",
        "code_match",
    }
    assert "Cross-column failures: 6" in capsys.readouterr().out


def test_clean_reports_conditional_presence_failures(capsys, tmp_path: Path) -> None:
    output = tmp_path / "clean.csv"
    report = tmp_path / "audit.json"

    status = main(
        [
            "clean",
            str(ROOT / "examples" / "conditional_presence_demo.csv"),
            "--schema",
            str(ROOT / "examples" / "conditional_presence_schema.json"),
            "--output",
            str(output),
            "--report",
            str(report),
        ]
    )

    assert status == 1
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    audit = json.loads(report.read_text(encoding="utf-8"))
    assert audit["conditional_presence_failures"] == 4
    assert audit["issues_by_code"]["CONDITIONAL_REQUIRED_VALUE_MISSING"] == 4
    assert {issue["rule"] for issue in audit["issues"]} == {
        "start_required_when_end_present",
        "reviewer_required_when_reviewed_at_present",
    }
    assert "Conditional presence failures: 4" in capsys.readouterr().out


def test_clean_uses_default_report_name(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    schema = tmp_path / "schema.json"
    output = tmp_path / "clean.csv"
    source.write_text("id\n1\n", encoding="utf-8")
    schema.write_text(
        json.dumps({"columns": {"id": {"type": "integer"}}}),
        encoding="utf-8",
    )

    status = main(
        [
            "clean",
            str(source),
            "--schema",
            str(schema),
            "--output",
            str(output),
        ]
    )

    assert status == 0
    assert output.exists()
    assert (tmp_path / "clean.report.json").exists()


def test_suggest_schema_writes_evidence_report(
    tmp_path: Path,
    capsys,
) -> None:
    output = tmp_path / "suggestion.json"

    status = main(
        [
            "suggest-schema",
            str(ROOT / "examples" / "schema_suggestion_demo.csv"),
            "--output",
            str(output),
        ]
    )

    assert status == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["suggested_schema"]["columns"]["record_id"]["type"] == "integer"
    assert report["suggested_schema"]["columns"]["postal_code"]["type"] == "string"
    assert "Suggestion:" in capsys.readouterr().out


def test_cli_rejects_overwriting_the_input(tmp_path: Path, capsys) -> None:
    source = tmp_path / "input.csv"
    schema = tmp_path / "schema.json"
    source.write_text("id\n1\n", encoding="utf-8")
    schema.write_text(
        json.dumps({"columns": {"id": {"type": "integer"}}}),
        encoding="utf-8",
    )

    status = main(
        [
            "clean",
            str(source),
            "--schema",
            str(schema),
            "--output",
            str(source),
        ]
    )

    assert status == 2
    assert "must be different" in capsys.readouterr().err


def test_cli_rejects_overwriting_the_schema(tmp_path: Path, capsys) -> None:
    source = tmp_path / "input.csv"
    schema = tmp_path / "schema.json"
    source.write_text("id\n1\n", encoding="utf-8")
    schema_text = json.dumps({"columns": {"id": {"type": "integer"}}})
    schema.write_text(schema_text, encoding="utf-8")

    status = main(
        [
            "clean",
            str(source),
            "--schema",
            str(schema),
            "--output",
            str(schema),
        ]
    )

    assert status == 2
    assert schema.read_text(encoding="utf-8") == schema_text
    assert "must be different" in capsys.readouterr().err


def test_cli_rejects_hard_link_alias_of_the_input(tmp_path: Path, capsys) -> None:
    source = tmp_path / "input.csv"
    alias = tmp_path / "alias.csv"
    schema = tmp_path / "schema.json"
    source_text = "id\n1\n"
    source.write_text(source_text, encoding="utf-8")
    os.link(source, alias)
    schema.write_text(
        json.dumps({"columns": {"id": {"type": "integer"}}}),
        encoding="utf-8",
    )

    status = main(
        [
            "clean",
            str(source),
            "--schema",
            str(schema),
            "--output",
            str(alias),
        ]
    )

    assert status == 2
    assert source.read_text(encoding="utf-8") == source_text
    assert "must be different" in capsys.readouterr().err
