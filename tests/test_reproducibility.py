from __future__ import annotations

import sys
from pathlib import Path

import pytest

from examples.run_demo import (
    _verify_checksum_manifest,
    _write_checksum_manifest,
    main as run_demo,
)


ROOT = Path(__file__).resolve().parents[1]


def test_checksum_manifest_is_portable_and_verifiable(tmp_path: Path) -> None:
    (tmp_path / "b.json").write_text('{"value": 2}\n', encoding="utf-8")
    (tmp_path / "a.csv").write_text("value\n1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Not an artifact\n", encoding="utf-8")

    manifest = _write_checksum_manifest(tmp_path)

    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert [line.split("  ", maxsplit=1)[1] for line in lines] == [
        "a.csv",
        "b.json",
    ]
    assert _verify_checksum_manifest(tmp_path) == 2


def test_checksum_manifest_detects_changed_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "report.json"
    artifact.write_text('{"value": 1}\n', encoding="utf-8")
    _write_checksum_manifest(tmp_path)
    artifact.write_text('{"value": 2}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Checksum mismatch: report.json"):
        _verify_checksum_manifest(tmp_path)


def test_checksum_manifest_detects_artifact_set_changes(tmp_path: Path) -> None:
    original = tmp_path / "original.csv"
    original.write_text("value\n1\n", encoding="utf-8")
    _write_checksum_manifest(tmp_path)
    original.unlink()
    (tmp_path / "unexpected.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"missing: original.csv; unexpected: unexpected.json",
    ):
        _verify_checksum_manifest(tmp_path)


def test_checksum_manifest_rejects_malformed_entries(tmp_path: Path) -> None:
    (tmp_path / "report.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "checksums.sha256").write_text(
        "not-a-digest  report.json\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid SHA-256 on line 1"):
        _verify_checksum_manifest(tmp_path)


def test_verify_only_returns_nonzero_for_missing_manifest(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_demo.py", "--output-dir", str(tmp_path), "--verify-only"],
    )

    assert run_demo() == 1
    assert "Verification failed: Checksum manifest not found:" in (
        capsys.readouterr().err
    )


def test_committed_reference_checksums_are_valid() -> None:
    assert _verify_checksum_manifest(ROOT / "results") == 16
