"""Regenerate the committed demonstration reports and cleaned CSV."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from data_cleaning_toolkit.cli import main as toolkit_main


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    os.chdir(ROOT)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source = Path("examples/demo_dirty.csv")
    schema = Path("examples/customer_schema.json")
    inspection = args.output_dir / "demo_inspection.json"
    cleaned = args.output_dir / "demo_clean.csv"
    audit = args.output_dir / "demo_cleaning_report.json"
    suggestion_source = Path("examples/schema_suggestion_demo.csv")
    expected_types = Path("examples/schema_suggestion_expected.json")
    suggestion = args.output_dir / "demo_schema_suggestion.json"

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
