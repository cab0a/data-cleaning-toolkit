"""Run a deterministic cleaning example through the supported public API."""

from __future__ import annotations

from pathlib import Path

from data_cleaning_toolkit import clean_table, load_schema, read_csv_table


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    table = read_csv_table(ROOT / "examples" / "privacy_modes_demo.csv")
    schema = load_schema(ROOT / "examples" / "privacy_modes_schema.json")
    result = clean_table(table, schema)

    print(f"Input rows: {result.input_rows}")
    print(f"Output rows: {len(result.rows)}")
    print(f"Errors: {result.error_count}")
    print("Mapping columns:")
    for coverage in result.mapping_coverage:
        print(
            f"  {coverage.column}: mode={coverage.unmatched_value_mode}, "
            f"mapped={coverage.mapped_cells}/"
            f"{coverage.observed_non_empty_cells}"
        )
    return 1 if result.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
