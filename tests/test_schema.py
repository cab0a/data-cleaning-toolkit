from __future__ import annotations

from decimal import Decimal

import pytest

from data_cleaning_toolkit.schema import schema_from_mapping


def test_schema_loads_ordered_column_rules() -> None:
    schema = schema_from_mapping(
        {
            "version": 1,
            "unknown_columns": "drop",
            "invalid_rows": "keep",
            "deduplicate_by": ["id"],
            "columns": {
                "id": {"type": "integer", "required": True, "min": 1},
                "active": {
                    "type": "boolean",
                    "true_values": ["yes"],
                    "false_values": ["no"],
                    "value_mapping": {"enabled": "yes"},
                },
            },
        }
    )

    assert [rule.name for rule in schema.columns] == ["id", "active"]
    assert schema.columns[0].minimum == Decimal("1")
    assert schema.invalid_rows == "keep"
    assert schema.deduplicate_by == ("id",)
    assert schema.columns[1].value_mapping == (("enabled", "yes"),)
    assert schema.columns[1].unmatched_value_mode == "raw"


def test_schema_loads_unmatched_value_privacy_modes() -> None:
    schema = schema_from_mapping(
        {
            "columns": {
                "public_code": {
                    "value_mapping": {"legacy": "canonical"},
                    "unmatched_value_mode": "redacted",
                },
                "restricted_code": {
                    "value_mapping": {"old": "new"},
                    "unmatched_value_mode": "disabled",
                },
            }
        }
    )

    assert schema.columns[0].unmatched_value_mode == "redacted"
    assert schema.columns[1].unmatched_value_mode == "disabled"


def test_schema_loads_cross_column_rules() -> None:
    schema = schema_from_mapping(
        {
            "columns": {
                "minimum": {"type": "decimal"},
                "maximum": {"type": "decimal"},
            },
            "cross_column_rules": [
                {
                    "name": "range_order",
                    "left": "minimum",
                    "operator": "less_than_or_equal",
                    "right": "maximum",
                }
            ],
        }
    )

    assert len(schema.cross_column_rules) == 1
    rule = schema.cross_column_rules[0]
    assert (rule.name, rule.left, rule.operator, rule.right) == (
        "range_order",
        "minimum",
        "less_than_or_equal",
        "maximum",
    )


def test_schema_loads_conditional_presence_rules() -> None:
    schema = schema_from_mapping(
        {
            "columns": {
                "start_date": {"type": "date"},
                "end_date": {"type": "date"},
            },
            "conditional_presence_rules": [
                {
                    "name": "start_required_when_end_present",
                    "when_present": "end_date",
                    "require": "start_date",
                }
            ],
        }
    )

    assert len(schema.conditional_presence_rules) == 1
    rule = schema.conditional_presence_rules[0]
    assert (rule.name, rule.when_present, rule.require) == (
        "start_required_when_end_present",
        "end_date",
        "start_date",
    )


@pytest.mark.parametrize(
    ("mapping", "message"),
    [
        (
            {"columns": {"id": {"type": "integer", "requird": True}}},
            "unknown keys",
        ),
        (
            {
                "columns": {"id": {"type": "integer"}},
                "deduplicate_by": ["missing"],
            },
            "undefined columns",
        ),
        (
            {"columns": {"name": {"type": "string", "min": 1}}},
            "only valid for integer or decimal",
        ),
        (
            {"columns": {"name": {"pattern": "["}}},
            "pattern is invalid",
        ),
        (
            {"version": 2, "columns": {"id": {}}},
            "version 1",
        ),
        (
            {"columns": {"country": {"value_mapping": ["JP", "Japan"]}}},
            "object with string keys and values",
        ),
        (
            {"columns": {"country": {"value_mapping": {"JP": 1}}}},
            "object with string keys and values",
        ),
        (
            {"columns": {"country": {"value_mapping": {"": "Japan"}}}},
            "empty source value",
        ),
        (
            {"columns": {"country": {"value_mapping": {"JP": ""}}}},
            "empty target value",
        ),
        (
            {
                "columns": {
                    "country": {
                        "strip": True,
                        "value_mapping": {" JP ": "Japan"},
                    }
                }
            },
            "surrounding whitespace",
        ),
        (
            {
                "columns": {
                    "country": {
                        "value_mapping": {"JP": "Japan"},
                        "unmatched_value_mode": "hashed",
                    }
                }
            },
            "must be raw, redacted, or disabled",
        ),
        (
            {
                "columns": {
                    "country": {"unmatched_value_mode": "redacted"}
                }
            },
            "only valid when value_mapping is configured",
        ),
    ],
)
def test_schema_rejects_ambiguous_or_misspelled_rules(
    mapping: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        schema_from_mapping(mapping)


@pytest.mark.parametrize(
    ("rules", "message"),
    [
        ({}, "must be a list"),
        ([{}], "name must be a non-empty string"),
        (
            [
                {
                    "name": "order",
                    "left": "minimum",
                    "operator": "less_than_or_equal",
                    "right": "maximum",
                    "unexpected": True,
                }
            ],
            "unknown keys",
        ),
        (
            [
                {
                    "name": "order",
                    "left": "missing",
                    "operator": "equal",
                    "right": "maximum",
                }
            ],
            "undefined columns",
        ),
        (
            [
                {
                    "name": "self_compare",
                    "left": "minimum",
                    "operator": "equal",
                    "right": "minimum",
                }
            ],
            "two different columns",
        ),
        (
            [
                {
                    "name": "mixed_types",
                    "left": "minimum",
                    "operator": "equal",
                    "right": "label",
                }
            ],
            "same type",
        ),
        (
            [
                {
                    "name": "text_order",
                    "left": "label",
                    "operator": "less_than",
                    "right": "other_label",
                }
            ],
            "ordering only",
        ),
        (
            [
                {
                    "name": "bad_operator",
                    "left": "minimum",
                    "operator": "approximately_equal",
                    "right": "maximum",
                }
            ],
            "operator must be one of",
        ),
        (
            [
                {
                    "name": "duplicate",
                    "left": "minimum",
                    "operator": "equal",
                    "right": "maximum",
                },
                {
                    "name": "duplicate",
                    "left": "minimum",
                    "operator": "not_equal",
                    "right": "maximum",
                },
            ],
            "duplicate names",
        ),
    ],
)
def test_schema_rejects_invalid_cross_column_rules(
    rules: object,
    message: str,
) -> None:
    mapping = {
        "columns": {
            "minimum": {"type": "decimal"},
            "maximum": {"type": "decimal"},
            "label": {"type": "string"},
            "other_label": {"type": "string"},
        },
        "cross_column_rules": rules,
    }

    with pytest.raises(ValueError, match=message):
        schema_from_mapping(mapping)


@pytest.mark.parametrize(
    ("rules", "message"),
    [
        ({}, "must be a list"),
        ([{}], "name must be a non-empty string"),
        (
            [
                {
                    "name": "presence",
                    "when_present": "end_date",
                    "require": "start_date",
                    "unexpected": True,
                }
            ],
            "unknown keys",
        ),
        (
            [
                {
                    "name": "presence",
                    "when_present": "missing",
                    "require": "start_date",
                }
            ],
            "undefined columns",
        ),
        (
            [
                {
                    "name": "self_reference",
                    "when_present": "start_date",
                    "require": "start_date",
                }
            ],
            "two different columns",
        ),
        (
            [
                {
                    "name": "redundant",
                    "when_present": "end_date",
                    "require": "always_required",
                }
            ],
            "unconditionally required",
        ),
        (
            [
                {
                    "name": "duplicate",
                    "when_present": "end_date",
                    "require": "start_date",
                },
                {
                    "name": "duplicate",
                    "when_present": "start_date",
                    "require": "end_date",
                },
            ],
            "duplicate names",
        ),
    ],
)
def test_schema_rejects_invalid_conditional_presence_rules(
    rules: object,
    message: str,
) -> None:
    mapping = {
        "columns": {
            "start_date": {"type": "date"},
            "end_date": {"type": "date"},
            "always_required": {"type": "string", "required": True},
        },
        "conditional_presence_rules": rules,
    }

    with pytest.raises(ValueError, match=message):
        schema_from_mapping(mapping)
