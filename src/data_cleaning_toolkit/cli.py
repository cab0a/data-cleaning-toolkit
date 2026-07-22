"""Command-line interface for CSV inspection, suggestion, and cleaning."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .cleaning import clean_table
from .csv_table import read_csv_table, write_csv_rows
from .inspection import inspect_table
from .reporting import json_text, sha256_file, write_json_report
from .schema import load_schema
from .suggestion import suggest_schema


def _different_paths(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("Protected source and destination paths must be different")
    try:
        if source.exists() and destination.exists() and source.samefile(destination):
            raise ValueError(
                "Protected source and destination paths must be different"
            )
    except OSError:
        pass


def _default_report_path(output: Path) -> Path:
    if output.suffix:
        return output.with_suffix(".report.json")
    return output.with_name(output.name + ".report.json")


def _cmd_inspect(args: argparse.Namespace) -> int:
    source = Path(args.input)
    table = read_csv_table(source)
    report = inspect_table(table)
    if args.output:
        destination = Path(args.output)
        _different_paths(source, destination)
        write_json_report(destination, report)
        print(f"Rows: {report['input_rows']}")
        print(f"Columns: {report['column_count']}")
        print(f"Duplicate rows: {report['duplicate_rows']}")
        print(f"Malformed rows: {report['malformed_rows']}")
        print(f"Report: {destination}")
    else:
        print(json_text(report))
    return 1 if table.issues else 0


def _cmd_clean(args: argparse.Namespace) -> int:
    source = Path(args.input)
    schema_path = Path(args.schema)
    output = Path(args.output)
    report_path = Path(args.report) if args.report else _default_report_path(output)
    _different_paths(source, output)
    _different_paths(source, report_path)
    _different_paths(output, report_path)
    _different_paths(schema_path, output)
    _different_paths(schema_path, report_path)

    table = read_csv_table(source)
    schema = load_schema(schema_path)
    result = clean_table(table, schema)
    write_csv_rows(output, result.headers, result.rows)
    write_json_report(
        report_path,
        result.as_report(
            source=source.as_posix(),
            output=output.as_posix(),
            schema=schema_path.as_posix(),
            schema_version=schema.version,
            source_sha256=sha256_file(source),
            schema_sha256=sha256_file(schema_path),
            output_sha256=sha256_file(output),
        ),
    )

    print(f"Input rows: {result.input_rows}")
    print(f"Output rows: {len(result.rows)}")
    print(f"Invalid rows: {result.invalid_rows}")
    print(f"Duplicate rows removed: {result.duplicate_rows_removed}")
    print(f"Mapped cells: {result.mapped_cells}")
    print(f"Transformed cells: {result.transformed_cells}")
    print(f"Cross-column failures: {result.cross_column_failure_count}")
    print(f"Clean CSV: {output}")
    print(f"Audit report: {report_path}")
    return 1 if result.error_count else 0


def _cmd_suggest_schema(args: argparse.Namespace) -> int:
    source = Path(args.input)
    destination = Path(args.output)
    _different_paths(source, destination)
    table = read_csv_table(source)
    report = suggest_schema(table, date_format=args.date_format)
    write_json_report(destination, report)
    print(f"Rows: {report['input_rows']}")
    print(f"Columns: {report['column_count']}")
    print(f"Malformed rows: {report['malformed_rows']}")
    print(f"Suggestion: {destination}")
    return 1 if table.issues else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data-cleaning-toolkit",
        description=(
            "Inspect CSV structure, suggest rules, and apply deterministic cleaning."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    inspect_parser = commands.add_parser(
        "inspect",
        help="Report columns, empty cells, exact duplicate rows, and malformed rows",
    )
    inspect_parser.add_argument("input", help="UTF-8 CSV input")
    inspect_parser.add_argument("--output", help="JSON report path; stdout if omitted")
    inspect_parser.set_defaults(handler=_cmd_inspect)

    clean_parser = commands.add_parser(
        "clean",
        help="Normalize and validate a CSV using a versioned JSON schema",
    )
    clean_parser.add_argument("input", help="UTF-8 CSV input")
    clean_parser.add_argument("--schema", required=True, help="JSON schema path")
    clean_parser.add_argument("--output", required=True, help="Clean CSV output path")
    clean_parser.add_argument(
        "--report",
        help="Audit JSON path; defaults to OUTPUT with .report.json suffix",
    )
    clean_parser.set_defaults(handler=_cmd_clean)

    suggest_parser = commands.add_parser(
        "suggest-schema",
        help="Suggest conservative column rules and report inference evidence",
    )
    suggest_parser.add_argument("input", help="UTF-8 CSV input")
    suggest_parser.add_argument(
        "--output",
        required=True,
        help="JSON schema suggestion report path",
    )
    suggest_parser.add_argument(
        "--date-format",
        default="%Y-%m-%d",
        help="Date format considered during inference (default: %%Y-%%m-%%d)",
    )
    suggest_parser.set_defaults(handler=_cmd_suggest_schema)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (OSError, ValueError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
