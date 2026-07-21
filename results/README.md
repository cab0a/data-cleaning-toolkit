# Reference Results

These files are deterministic outputs generated from the intentionally dirty
CSV in `examples/demo_dirty.csv` and the versioned rules in
`examples/customer_schema.json`.

Regenerate them from the repository root with:

```bash
python examples/run_demo.py
```

The demo deliberately contains invalid and malformed rows. The underlying
`inspect` and `clean` commands therefore return exit code 1, while the wrapper
accepts that documented result and exits successfully after writing all three
artifacts.
