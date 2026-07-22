"""Deterministic tools for inspecting, profiling, and cleaning CSV data."""

from .cleaning import clean_table
from .csv_table import CsvFormatError, read_csv_table
from .inspection import inspect_table
from .models import (
    CleaningResult,
    CsvTable,
    DataIssue,
    MappingCoverage,
    TableRow,
)
from .schema import (
    CleaningSchema,
    ColumnRule,
    ConditionalPresenceRule,
    CrossColumnRule,
    load_schema,
    schema_from_mapping,
)
from .suggestion import suggest_schema

__all__ = [
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
]

__version__ = "0.9.0"
