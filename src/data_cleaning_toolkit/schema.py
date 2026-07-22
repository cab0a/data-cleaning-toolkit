"""Load and validate the declarative JSON cleaning schema."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


SUPPORTED_TYPES = {"string", "integer", "decimal", "boolean", "date"}
TOP_LEVEL_KEYS = {
    "version",
    "unknown_columns",
    "invalid_rows",
    "deduplicate_by",
    "cross_column_rules",
    "conditional_presence_rules",
    "columns",
}
COLUMN_KEYS = {
    "type",
    "required",
    "strip",
    "case",
    "null_values",
    "allowed_values",
    "pattern",
    "min",
    "max",
    "input_format",
    "output_format",
    "true_values",
    "false_values",
    "value_mapping",
}
CROSS_COLUMN_RULE_KEYS = {"name", "left", "operator", "right"}
CONDITIONAL_PRESENCE_RULE_KEYS = {"name", "when_present", "require"}
COMPARISON_OPERATORS = {
    "equal",
    "not_equal",
    "less_than",
    "less_than_or_equal",
    "greater_than",
    "greater_than_or_equal",
}
ORDERING_OPERATORS = COMPARISON_OPERATORS - {"equal", "not_equal"}


@dataclass(frozen=True, slots=True)
class ColumnRule:
    name: str
    data_type: str = "string"
    required: bool = False
    strip: bool = False
    case: str = "preserve"
    null_values: tuple[str, ...] = ("",)
    allowed_values: tuple[str, ...] = ()
    pattern: str | None = None
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    input_format: str = "%Y-%m-%d"
    output_format: str = "%Y-%m-%d"
    true_values: tuple[str, ...] = ("true", "1", "yes", "y")
    false_values: tuple[str, ...] = ("false", "0", "no", "n")
    value_mapping: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class CrossColumnRule:
    name: str
    left: str
    operator: str
    right: str


@dataclass(frozen=True, slots=True)
class ConditionalPresenceRule:
    name: str
    when_present: str
    require: str


@dataclass(frozen=True, slots=True)
class CleaningSchema:
    version: int
    columns: tuple[ColumnRule, ...]
    unknown_columns: str = "keep"
    invalid_rows: str = "drop"
    deduplicate_by: tuple[str, ...] = ()
    cross_column_rules: tuple[CrossColumnRule, ...] = ()
    conditional_presence_rules: tuple[ConditionalPresenceRule, ...] = ()

    @property
    def column_map(self) -> dict[str, ColumnRule]:
        return {rule.name: rule for rule in self.columns}


def _expect_bool(value: Any, location: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{location} must be true or false")
    return value


def _string_list(value: Any, location: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{location} must be a list of strings")
    return tuple(value)


def _string_mapping(value: Any, location: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in value.items()
    ):
        raise ValueError(f"{location} must be an object with string keys and values")
    if any(key == "" for key in value):
        raise ValueError(f"{location} cannot contain an empty source value")
    if any(item == "" for item in value.values()):
        raise ValueError(f"{location} cannot contain an empty target value")
    return tuple(value.items())


def _decimal(value: Any, location: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{location} must be a finite number")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{location} must be a finite number") from exc
    if not parsed.is_finite():
        raise ValueError(f"{location} must be a finite number")
    return parsed


def _column_rule(name: str, raw: Any) -> ColumnRule:
    if not name:
        raise ValueError("Column names in the schema cannot be empty")
    if not isinstance(raw, dict):
        raise ValueError(f"columns.{name} must be an object")

    unknown = sorted(set(raw) - COLUMN_KEYS)
    if unknown:
        raise ValueError(
            f"columns.{name} contains unknown keys: " + ", ".join(unknown)
        )

    data_type = raw.get("type", "string")
    if data_type not in SUPPORTED_TYPES:
        raise ValueError(
            f"columns.{name}.type must be one of: "
            + ", ".join(sorted(SUPPORTED_TYPES))
        )

    case = raw.get("case", "preserve")
    if case not in {"preserve", "lower", "upper"}:
        raise ValueError(
            f"columns.{name}.case must be preserve, lower, or upper"
        )
    if data_type != "string" and case != "preserve":
        raise ValueError(f"columns.{name}.case is only valid for string columns")

    pattern = raw.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            raise ValueError(f"columns.{name}.pattern must be a string")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"columns.{name}.pattern is invalid: {exc}") from exc

    minimum = _decimal(raw.get("min"), f"columns.{name}.min")
    maximum = _decimal(raw.get("max"), f"columns.{name}.max")
    if (minimum is not None or maximum is not None) and data_type not in {
        "integer",
        "decimal",
    }:
        raise ValueError(
            f"columns.{name}.min/max are only valid for integer or decimal columns"
        )
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError(f"columns.{name}.min cannot be greater than max")

    input_format = raw.get("input_format", "%Y-%m-%d")
    output_format = raw.get("output_format", "%Y-%m-%d")
    if not isinstance(input_format, str) or not isinstance(output_format, str):
        raise ValueError(
            f"columns.{name}.input_format and output_format must be strings"
        )

    true_values = _string_list(
        raw.get("true_values", ["true", "1", "yes", "y"]),
        f"columns.{name}.true_values",
    )
    false_values = _string_list(
        raw.get("false_values", ["false", "0", "no", "n"]),
        f"columns.{name}.false_values",
    )
    if data_type != "boolean" and (
        "true_values" in raw or "false_values" in raw
    ):
        raise ValueError(
            f"columns.{name}.true_values/false_values are only valid for boolean columns"
        )
    if {value.casefold() for value in true_values} & {
        value.casefold() for value in false_values
    }:
        raise ValueError(
            f"columns.{name}.true_values and false_values cannot overlap"
        )

    value_mapping = _string_mapping(
        raw.get("value_mapping", {}), f"columns.{name}.value_mapping"
    )
    if raw.get("strip", False) and any(
        source != source.strip() for source, _ in value_mapping
    ):
        raise ValueError(
            f"columns.{name}.value_mapping keys cannot contain surrounding "
            "whitespace when strip is true"
        )

    return ColumnRule(
        name=name,
        data_type=data_type,
        required=_expect_bool(
            raw.get("required", False), f"columns.{name}.required"
        ),
        strip=_expect_bool(raw.get("strip", False), f"columns.{name}.strip"),
        case=case,
        null_values=_string_list(
            raw.get("null_values", [""]), f"columns.{name}.null_values"
        ),
        allowed_values=_string_list(
            raw.get("allowed_values", []), f"columns.{name}.allowed_values"
        ),
        pattern=pattern,
        minimum=minimum,
        maximum=maximum,
        input_format=input_format,
        output_format=output_format,
        true_values=true_values,
        false_values=false_values,
        value_mapping=value_mapping,
    )


def _cross_column_rule(
    raw: Any,
    index: int,
    column_map: dict[str, ColumnRule],
) -> CrossColumnRule:
    location = f"cross_column_rules[{index}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{location} must be an object")

    unknown = sorted(set(raw) - CROSS_COLUMN_RULE_KEYS)
    if unknown:
        raise ValueError(
            f"{location} contains unknown keys: " + ", ".join(unknown)
        )

    values: dict[str, str] = {}
    for key in ("name", "left", "operator", "right"):
        value = raw.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{location}.{key} must be a non-empty string")
        values[key] = value

    operator = values["operator"]
    if operator not in COMPARISON_OPERATORS:
        raise ValueError(
            f"{location}.operator must be one of: "
            + ", ".join(sorted(COMPARISON_OPERATORS))
        )

    left = values["left"]
    right = values["right"]
    undefined = sorted({left, right} - set(column_map))
    if undefined:
        raise ValueError(
            f"{location} references undefined columns: " + ", ".join(undefined)
        )
    if left == right:
        raise ValueError(f"{location} must reference two different columns")

    left_type = column_map[left].data_type
    right_type = column_map[right].data_type
    if left_type != right_type:
        raise ValueError(f"{location} must compare columns with the same type")
    if operator in ORDERING_OPERATORS and left_type not in {
        "integer",
        "decimal",
        "date",
    }:
        raise ValueError(
            f"{location}.operator supports ordering only for integer, decimal, "
            "or date columns"
        )

    return CrossColumnRule(
        name=values["name"],
        left=left,
        operator=operator,
        right=right,
    )


def _conditional_presence_rule(
    raw: Any,
    index: int,
    column_map: dict[str, ColumnRule],
) -> ConditionalPresenceRule:
    location = f"conditional_presence_rules[{index}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{location} must be an object")

    unknown = sorted(set(raw) - CONDITIONAL_PRESENCE_RULE_KEYS)
    if unknown:
        raise ValueError(
            f"{location} contains unknown keys: " + ", ".join(unknown)
        )

    values: dict[str, str] = {}
    for key in ("name", "when_present", "require"):
        value = raw.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{location}.{key} must be a non-empty string")
        values[key] = value

    when_present = values["when_present"]
    required = values["require"]
    undefined = sorted({when_present, required} - set(column_map))
    if undefined:
        raise ValueError(
            f"{location} references undefined columns: " + ", ".join(undefined)
        )
    if when_present == required:
        raise ValueError(f"{location} must reference two different columns")
    if column_map[required].required:
        raise ValueError(
            f"{location}.require references an unconditionally required column"
        )

    return ConditionalPresenceRule(
        name=values["name"],
        when_present=when_present,
        require=required,
    )


def schema_from_mapping(raw: Any) -> CleaningSchema:
    if not isinstance(raw, dict):
        raise ValueError("Schema root must be a JSON object")
    unknown = sorted(set(raw) - TOP_LEVEL_KEYS)
    if unknown:
        raise ValueError("Schema contains unknown keys: " + ", ".join(unknown))

    version = raw.get("version", 1)
    if isinstance(version, bool) or version != 1:
        raise ValueError("Only schema version 1 is supported")

    columns_raw = raw.get("columns")
    if not isinstance(columns_raw, dict) or not columns_raw:
        raise ValueError("Schema columns must be a non-empty object")
    columns = tuple(_column_rule(name, rule) for name, rule in columns_raw.items())

    unknown_columns = raw.get("unknown_columns", "keep")
    if unknown_columns not in {"keep", "drop", "error"}:
        raise ValueError("unknown_columns must be keep, drop, or error")
    invalid_rows = raw.get("invalid_rows", "drop")
    if invalid_rows not in {"keep", "drop"}:
        raise ValueError("invalid_rows must be keep or drop")

    deduplicate_by = _string_list(
        raw.get("deduplicate_by", []), "deduplicate_by"
    )
    column_names = {rule.name for rule in columns}
    missing_keys = sorted(set(deduplicate_by) - column_names)
    if missing_keys:
        raise ValueError(
            "deduplicate_by references undefined columns: "
            + ", ".join(missing_keys)
        )
    if len(set(deduplicate_by)) != len(deduplicate_by):
        raise ValueError("deduplicate_by cannot contain duplicate column names")

    cross_column_rules_raw = raw.get("cross_column_rules", [])
    if not isinstance(cross_column_rules_raw, list):
        raise ValueError("cross_column_rules must be a list")
    column_map = {rule.name: rule for rule in columns}
    cross_column_rules = tuple(
        _cross_column_rule(rule, index, column_map)
        for index, rule in enumerate(cross_column_rules_raw)
    )
    cross_rule_names = [rule.name for rule in cross_column_rules]
    if len(set(cross_rule_names)) != len(cross_rule_names):
        raise ValueError("cross_column_rules cannot contain duplicate names")

    conditional_presence_rules_raw = raw.get("conditional_presence_rules", [])
    if not isinstance(conditional_presence_rules_raw, list):
        raise ValueError("conditional_presence_rules must be a list")
    conditional_presence_rules = tuple(
        _conditional_presence_rule(rule, index, column_map)
        for index, rule in enumerate(conditional_presence_rules_raw)
    )
    conditional_rule_names = [rule.name for rule in conditional_presence_rules]
    if len(set(conditional_rule_names)) != len(conditional_rule_names):
        raise ValueError(
            "conditional_presence_rules cannot contain duplicate names"
        )

    return CleaningSchema(
        version=version,
        columns=columns,
        unknown_columns=unknown_columns,
        invalid_rows=invalid_rows,
        deduplicate_by=deduplicate_by,
        cross_column_rules=cross_column_rules,
        conditional_presence_rules=conditional_presence_rules,
    )


def load_schema(path: str | Path) -> CleaningSchema:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        try:
            raw = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Schema is not valid JSON: {exc}") from exc
    return schema_from_mapping(raw)
