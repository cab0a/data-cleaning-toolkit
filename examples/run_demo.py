"""Regenerate the committed demonstration reports and cleaned CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from data_cleaning_toolkit.cli import main as toolkit_main


ROOT = Path(__file__).resolve().parents[1]
CHECKSUM_MANIFEST = "checksums.sha256"
RESULT_SUFFIXES = {".csv", ".json"}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _result_artifacts(output_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.suffix in RESULT_SUFFIXES
    )


def _write_checksum_manifest(output_dir: Path) -> Path:
    manifest = output_dir / CHECKSUM_MANIFEST
    lines = [
        f"{_sha256_file(path)}  {path.name}\n"
        for path in _result_artifacts(output_dir)
    ]
    manifest.write_text("".join(lines), encoding="utf-8", newline="\n")
    return manifest


def _verify_checksum_manifest(output_dir: Path) -> int:
    manifest = output_dir / CHECKSUM_MANIFEST
    if not manifest.is_file():
        raise ValueError(f"Checksum manifest not found: {manifest}")

    expected: dict[str, str] = {}
    for line_number, line in enumerate(
        manifest.read_text(encoding="utf-8").splitlines(), start=1
    ):
        parts = line.split("  ", maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Invalid checksum line {line_number}")
        digest, name = parts
        valid_digest = len(digest) == 64 and all(
            character in "0123456789abcdef" for character in digest
        )
        if not valid_digest:
            raise ValueError(f"Invalid SHA-256 on line {line_number}")
        if (
            not name
            or "/" in name
            or "\\" in name
            or Path(name).name != name
        ):
            raise ValueError(f"Invalid artifact name on line {line_number}")
        if name in expected:
            raise ValueError(f"Duplicate artifact in manifest: {name}")
        expected[name] = digest

    actual = {path.name: path for path in _result_artifacts(output_dir)}
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ValueError("Artifact set mismatch (" + "; ".join(details) + ")")

    mismatched = [
        name
        for name, digest in expected.items()
        if _sha256_file(actual[name]) != digest
    ]
    if mismatched:
        raise ValueError("Checksum mismatch: " + ", ".join(mismatched))
    return len(expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.verify_only:
        try:
            verified = _verify_checksum_manifest(args.output_dir)
        except ValueError as exc:
            print(f"Verification failed: {exc}", file=sys.stderr)
            return 1
        print(f"Verified: {verified} reference artifacts")
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source = Path("examples/demo_dirty.csv")
    schema = Path("examples/customer_schema.json")
    inspection = args.output_dir / "demo_inspection.json"
    cleaned = args.output_dir / "demo_clean.csv"
    audit = args.output_dir / "demo_cleaning_report.json"
    suggestion_source = Path("examples/schema_suggestion_demo.csv")
    expected_types = Path("examples/schema_suggestion_expected.json")
    suggestion = args.output_dir / "demo_schema_suggestion.json"
    mapping_source = Path("examples/value_mapping_demo.csv")
    mapping_schema = Path("examples/value_mapping_schema.json")
    mapping_cleaned = args.output_dir / "value_mapping_clean.csv"
    mapping_audit = args.output_dir / "value_mapping_report.json"
    cross_source = Path("examples/cross_column_demo.csv")
    cross_schema = Path("examples/cross_column_schema.json")
    cross_cleaned = args.output_dir / "cross_column_clean.csv"
    cross_audit = args.output_dir / "cross_column_report.json"
    presence_source = Path("examples/conditional_presence_demo.csv")
    presence_schema = Path("examples/conditional_presence_schema.json")
    presence_cleaned = args.output_dir / "conditional_presence_clean.csv"
    presence_audit = args.output_dir / "conditional_presence_report.json"
    coverage_source = Path("examples/mapping_coverage_demo.csv")
    coverage_schema = Path("examples/mapping_coverage_schema.json")
    coverage_cleaned = args.output_dir / "mapping_coverage_clean.csv"
    coverage_audit = args.output_dir / "mapping_coverage_report.json"
    frequency_source = Path("examples/unmatched_frequency_demo.csv")
    frequency_schema = Path("examples/unmatched_frequency_schema.json")
    frequency_cleaned = args.output_dir / "unmatched_frequency_clean.csv"
    frequency_audit = args.output_dir / "unmatched_frequency_report.json"
    privacy_source = Path("examples/privacy_modes_demo.csv")
    privacy_schema = Path("examples/privacy_modes_schema.json")
    privacy_cleaned = args.output_dir / "privacy_modes_clean.csv"
    privacy_audit = args.output_dir / "privacy_modes_report.json"

    inspect_status = toolkit_main(
        ["inspect", str(source), "--output", str(inspection)]
    )
    clean_status = toolkit_main(
        [
            "clean",
            str(source),
            "--schema",
            str(schema),
            "--output",
            str(cleaned),
            "--report",
            str(audit),
        ]
    )
    suggestion_status = toolkit_main(
        [
            "suggest-schema",
            str(suggestion_source),
            "--output",
            str(suggestion),
        ]
    )
    mapping_status = toolkit_main(
        [
            "clean",
            str(mapping_source),
            "--schema",
            str(mapping_schema),
            "--output",
            str(mapping_cleaned),
            "--report",
            str(mapping_audit),
        ]
    )
    cross_status = toolkit_main(
        [
            "clean",
            str(cross_source),
            "--schema",
            str(cross_schema),
            "--output",
            str(cross_cleaned),
            "--report",
            str(cross_audit),
        ]
    )
    presence_status = toolkit_main(
        [
            "clean",
            str(presence_source),
            "--schema",
            str(presence_schema),
            "--output",
            str(presence_cleaned),
            "--report",
            str(presence_audit),
        ]
    )
    coverage_status = toolkit_main(
        [
            "clean",
            str(coverage_source),
            "--schema",
            str(coverage_schema),
            "--output",
            str(coverage_cleaned),
            "--report",
            str(coverage_audit),
        ]
    )
    frequency_status = toolkit_main(
        [
            "clean",
            str(frequency_source),
            "--schema",
            str(frequency_schema),
            "--output",
            str(frequency_cleaned),
            "--report",
            str(frequency_audit),
        ]
    )
    privacy_status = toolkit_main(
        [
            "clean",
            str(privacy_source),
            "--schema",
            str(privacy_schema),
            "--output",
            str(privacy_cleaned),
            "--report",
            str(privacy_audit),
        ]
    )
    if inspect_status != 1:
        raise SystemExit(
            f"Expected inspect status 1 for the malformed demo row, got {inspect_status}"
        )
    if clean_status != 1:
        raise SystemExit(
            f"Expected clean status 1 for the intentionally invalid rows, got {clean_status}"
        )
    if suggestion_status != 0:
        raise SystemExit(
            "Expected suggest-schema status 0 for the controlled demo, "
            f"got {suggestion_status}"
        )
    if mapping_status != 1:
        raise SystemExit(
            "Expected clean status 1 for the controlled unmapped row, "
            f"got {mapping_status}"
        )
    if cross_status != 1:
        raise SystemExit(
            "Expected clean status 1 for the controlled cross-column failures, "
            f"got {cross_status}"
        )
    if presence_status != 1:
        raise SystemExit(
            "Expected clean status 1 for the controlled conditional presence "
            f"failures, got {presence_status}"
        )
    if coverage_status != 1:
        raise SystemExit(
            "Expected clean status 1 for the controlled unmapped value, "
            f"got {coverage_status}"
        )
    if frequency_status != 1:
        raise SystemExit(
            "Expected clean status 1 for the controlled unmatched values, "
            f"got {frequency_status}"
        )
    if privacy_status != 0:
        raise SystemExit(
            "Expected clean status 0 for the privacy-mode demo, "
            f"got {privacy_status}"
        )

    report = json.loads(suggestion.read_text(encoding="utf-8"))
    expected = json.loads(expected_types.read_text(encoding="utf-8"))
    observed = {
        name: rule["type"]
        for name, rule in report["suggested_schema"]["columns"].items()
    }
    if observed != expected:
        raise SystemExit(
            f"Schema suggestion mismatch: expected {expected}, got {observed}"
        )

    mapping_report = json.loads(mapping_audit.read_text(encoding="utf-8"))
    expected_mapping_summary = {
        "input_rows": 7,
        "output_rows": 6,
        "mapped_cells": 13,
        "error_count": 3,
        "mapped_issue_count": 13,
    }
    observed_mapping_summary = {
        "input_rows": mapping_report["input_rows"],
        "output_rows": mapping_report["output_rows"],
        "mapped_cells": mapping_report["mapped_cells"],
        "error_count": mapping_report["error_count"],
        "mapped_issue_count": mapping_report["issues_by_code"].get(
            "VALUE_MAPPED", 0
        ),
    }
    if observed_mapping_summary != expected_mapping_summary:
        raise SystemExit(
            "Value-mapping evaluation mismatch: expected "
            f"{expected_mapping_summary}, got {observed_mapping_summary}"
        )

    cross_report = json.loads(cross_audit.read_text(encoding="utf-8"))
    expected_cross_summary = {
        "input_rows": 7,
        "output_rows": 3,
        "invalid_rows": 4,
        "cross_column_failures": 6,
        "error_count": 6,
    }
    observed_cross_summary = {
        key: cross_report[key] for key in expected_cross_summary
    }
    if observed_cross_summary != expected_cross_summary:
        raise SystemExit(
            "Cross-column evaluation mismatch: expected "
            f"{expected_cross_summary}, got {observed_cross_summary}"
        )

    presence_report = json.loads(presence_audit.read_text(encoding="utf-8"))
    expected_presence_summary = {
        "input_rows": 7,
        "output_rows": 4,
        "invalid_rows": 3,
        "conditional_presence_failures": 4,
        "error_count": 4,
    }
    observed_presence_summary = {
        key: presence_report[key] for key in expected_presence_summary
    }
    if observed_presence_summary != expected_presence_summary:
        raise SystemExit(
            "Conditional presence evaluation mismatch: expected "
            f"{expected_presence_summary}, got {observed_presence_summary}"
        )

    coverage_report = json.loads(coverage_audit.read_text(encoding="utf-8"))
    expected_coverage_summary = {
        "input_rows": 7,
        "output_rows": 6,
        "invalid_rows": 1,
        "mapped_cells": 9,
        "error_count": 1,
    }
    observed_coverage_summary = {
        key: coverage_report[key] for key in expected_coverage_summary
    }
    if observed_coverage_summary != expected_coverage_summary:
        raise SystemExit(
            "Mapping coverage evaluation mismatch: expected "
            f"{expected_coverage_summary}, got {observed_coverage_summary}"
        )
    expected_coverage = {
        "observed_non_empty_cells": 12,
        "mapped_cells": 9,
        "unmapped_cells": 3,
        "coverage_rate": 0.75,
    }
    observed_coverage = {
        key: coverage_report["mapping_coverage"][key]
        for key in expected_coverage
    }
    if observed_coverage != expected_coverage:
        raise SystemExit(
            "Mapping coverage totals mismatch: expected "
            f"{expected_coverage}, got {observed_coverage}"
        )

    frequency_report = json.loads(frequency_audit.read_text(encoding="utf-8"))
    expected_frequency_summary = {
        "input_rows": 12,
        "output_rows": 8,
        "invalid_rows": 4,
        "mapped_cells": 2,
        "error_count": 4,
    }
    observed_frequency_summary = {
        key: frequency_report[key] for key in expected_frequency_summary
    }
    if observed_frequency_summary != expected_frequency_summary:
        raise SystemExit(
            "Unmatched-frequency evaluation mismatch: expected "
            f"{expected_frequency_summary}, got {observed_frequency_summary}"
        )
    expected_frequencies = [
        {"value": "unknown", "count": 4},
        {"value": "alpha", "count": 3},
        {"value": "beta", "count": 2},
    ]
    coverage_column = frequency_report["mapping_coverage"]["columns"][0]
    if coverage_column["unmatched_value_frequencies"] != expected_frequencies:
        raise SystemExit(
            "Unmatched-frequency order mismatch: expected "
            f"{expected_frequencies}, got "
            f"{coverage_column['unmatched_value_frequencies']}"
        )

    privacy_audit_text = privacy_audit.read_text(encoding="utf-8")
    privacy_report = json.loads(privacy_audit_text)
    expected_privacy_summary = {
        "input_rows": 8,
        "output_rows": 8,
        "invalid_rows": 0,
        "mapped_cells": 3,
        "error_count": 0,
    }
    observed_privacy_summary = {
        key: privacy_report[key] for key in expected_privacy_summary
    }
    if observed_privacy_summary != expected_privacy_summary:
        raise SystemExit(
            "Privacy-mode evaluation mismatch: expected "
            f"{expected_privacy_summary}, got {observed_privacy_summary}"
        )
    privacy_columns = {
        item["column"]: item
        for item in privacy_report["mapping_coverage"]["columns"]
    }
    expected_redacted_frequencies = [
        {"rank": 1, "count": 4},
        {"rank": 2, "count": 2},
        {"rank": 3, "count": 1},
    ]
    if (
        privacy_columns["redacted_category"]["unmatched_value_frequencies"]
        != expected_redacted_frequencies
    ):
        raise SystemExit("Redacted frequency counts do not match the reference")
    disabled_column = privacy_columns["disabled_category"]
    if (
        disabled_column["distinct_unmatched_values"] is not None
        or disabled_column["unmatched_value_frequencies"]
        or disabled_column["unmatched_values_truncated"] is not None
    ):
        raise SystemExit("Disabled frequency mode retained unmatched-value details")
    hidden_values = (
        "sensitive-one",
        "sensitive-two",
        "restricted-one",
        "restricted-two",
        "restricted-three",
    )
    if any(value in privacy_audit_text for value in hidden_values):
        raise SystemExit("Privacy-mode report exposed a protected sample value")
    manifest = _write_checksum_manifest(args.output_dir)
    print(f"Checksums: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
