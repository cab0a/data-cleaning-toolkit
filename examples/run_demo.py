"""Regenerate the committed demonstration reports and cleaned CSV."""

from __future__ import annotations

import argparse
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
    if inspect_status != 1:
        raise SystemExit(
            f"Expected inspect status 1 for the malformed demo row, got {inspect_status}"
        )
    if clean_status != 1:
        raise SystemExit(
            f"Expected clean status 1 for the intentionally invalid rows, got {clean_status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
