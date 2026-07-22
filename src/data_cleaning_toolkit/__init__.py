"""Deterministic tools for inspecting, profiling, and cleaning CSV data."""

from .cleaning import clean_table
from .inspection import inspect_table
from .schema import load_schema
from .suggestion import suggest_schema

__all__ = ["clean_table", "inspect_table", "load_schema", "suggest_schema"]

__version__ = "0.6.0"
