# Reproducibility

The repository contains synthetic inputs, reviewed schemas, deterministic
outputs, controlled assertions, and SHA-256 checksums. These artifacts verify
implementation behavior; they are not benchmarks for arbitrary datasets.

## Environment

Python 3.10 or later is required. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pip check
```

## Regenerate Reference Results

```bash
python examples/run_demo.py
```

The script runs every controlled example, checks expected counts and privacy
properties, writes the reference CSV and JSON files, and updates
`results/checksums.sha256`.

Verify the committed bytes without regenerating them:

```bash
python examples/run_demo.py --verify-only
```

The verification fails on a changed artifact, missing artifact, unexpected CSV
or JSON artifact, malformed checksum, or duplicate manifest entry.

After regeneration, confirm that the repository references did not change:

```bash
git diff --exit-code -- results/
```

An intentional result change must be explained by the implementation,
documentation, tests, and changelog in the same review.

## Public API Sample

```bash
python examples/public_api_demo.py
```

This sample imports only names documented at the package root. It performs the
same controlled cleaning in memory and prints stable summary counts without
writing files.

## Distribution Verification

Build both distribution formats and install the wheel into a clean environment:

```bash
python -m pip install build
python -m build
python -m venv .work/wheel-venv
source .work/wheel-venv/bin/activate
python -m pip install dist/data_cleaning_toolkit-1.0.0-py3-none-any.whl
python -m pip check
data-cleaning-toolkit --version
python examples/public_api_demo.py
```

The expected version is `1.0.0`. The installed package must also contain the
`py.typed` marker. The `.work` directory is excluded from version control and
can be removed after the review.

## Automated Coverage

GitHub Actions runs the test workflow on Python 3.10 through 3.14 and performs
these steps:

1. Install the project and development tests.
2. Check the installed CLI and public Python API example.
3. Run the unit tests.
4. Regenerate every reference artifact.
5. Verify the SHA-256 manifest.
6. Require an empty diff under `results/`.

A separate Python 3.14 job builds the source and wheel distributions, installs
the wheel, checks its dependency state, executes the installed CLI and public
API example, and confirms that typed-package metadata is present.

The matrix checks supported interpreter behavior on Ubuntu. It does not claim
coverage for every operating system, filesystem, CSV dialect, locale, or data
volume.

## Interpretation

The examples use public, synthetic, non-sensitive inputs. Their expected
counts demonstrate deterministic rules and known failure cases. They do not
measure semantic correctness, real-world vocabulary coverage, model quality,
or production-scale performance.
