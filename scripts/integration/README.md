# Integration scripts

These scripts hit a **running** API server (default `http://localhost:8000`)
and exercise it end-to-end. They are **not** unit tests — `pytest` does not
collect them. Use the `tests/` directory for unit tests.

## Usage

Start the API first:

```bash
python main.py
```

Then run any script:

```bash
python scripts/integration/test_comprehensive.py
python scripts/integration/test_full_system.py
python scripts/integration/test_new_schema.py
```

Set `API_URL` to point at a different host, e.g.:

```bash
API_URL=http://localhost:8000/api python scripts/integration/test_comprehensive.py
```
