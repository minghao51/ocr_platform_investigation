# Pytest Best Practices: Tagging & Folder Separation

> Researched April 2026 from pytest official docs, Google AI Search, and community sources.

---

## 1. Recommended Directory Layout (src layout)

The **"src" layout** is the official pytest recommendation. It ensures tests run against the installed package, avoiding import mismatches and `sys.path` pitfalls.

```
my_project/
├── pyproject.toml              # Central config (replaces pytest.ini)
├── src/
│   └── my_app/
│       ├── __init__.py
│       ├── core.py
│       └── api.py
└── tests/
    ├── conftest.py             # Global fixtures & hooks
    ├── unit/                   # Fast, isolated tests (no I/O, no network)
    │   ├── conftest.py         # Unit-specific fixtures
    │   ├── test_core.py
    │   └── test_utils.py
    ├── integration/            # Slow tests (DB, API, external services)
    │   ├── conftest.py         # Integration-specific fixtures (DB containers, etc.)
    │   ├── test_api.py
    │   └── test_database.py
    └── e2e/                    # End-to-end / smoke tests (optional)
        ├── conftest.py
        └── test_workflow.py
```

### Why src layout?

- Prevents accidental imports from the repo root instead of the installed package
- Works correctly with `pip install -e .`
- Avoids `sys.path` manipulation hacks
- Recommended by both pytest and the Python Packaging User Guide

### Alternative: Flat layout (not recommended for new projects)

```
my_project/
├── pyproject.toml
├── my_app/
│   └── ...
└── tests/
    └── ...
```

Works but susceptible to import confusion. If using this layout, set:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

---

## 2. Configuration (`pyproject.toml`)

**Avoid `pytest.ini`**. Centralize all settings in `pyproject.toml` — the modern standard since pytest 6+.

### Minimal config

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--strict-markers -ra --durations=10"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests requiring external services",
    "unit: marks fast unit tests",
    "e2e: marks end-to-end tests",
    "serial: marks tests that cannot run in parallel",
]
```

### Recommended strict config (pytest 9+)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "-ra",
    "--durations=10",
    "--import-mode=importlib",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
    "unit: marks fast unit tests",
    "e2e: marks end-to-end tests",
    "serial: marks tests that cannot run in parallel",
    "network: marks tests requiring network access",
]

# Or enable all strictness at once (pytest 9+):
# strict = true
```

### Key `addopts` flags

| Flag | Purpose |
|------|---------|
| `--strict-markers` | Error on unregistered markers (catches typos) |
| `-ra` | Show summary of all test outcomes |
| `--durations=10` | Show 10 slowest tests |
| `--import-mode=importlib` | Recommended import mode for new projects |
| `-v` | Verbose output |
| `--tb=short` | Shorter tracebacks |

---

## 3. Test Tagging / Markers

### Registering markers

Markers **must** be registered in `pyproject.toml` (or via `pytest_configure` hook). With `--strict-markers`, unregistered markers will error.

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
    "serial: marks tests that must run sequentially",
    "smoke: marks critical smoke tests",
]
```

Or programmatically in `conftest.py`:

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: integration tests")
```

### Using markers on tests

```python
import pytest

@pytest.mark.slow
def test_heavy_computation():
    ...

@pytest.mark.integration
@pytest.mark.slow
def test_database_migration():
    ...

@pytest.mark.serial
class TestFileOperations:
    def test_read(self):
        ...
    def test_write(self):
        ...
```

### Marking entire modules

```python
# test_all_slow_things.py
import pytest

pytestmark = pytest.mark.slow
# All tests in this file are marked slow

# Multiple markers:
# pytestmark = [pytest.mark.slow, pytest.mark.integration]
```

### Auto-marking based on directory (advanced)

Use the `pytest_collection_modifyitems` hook in `conftest.py` to auto-mark tests based on their file path:

```python
# tests/conftest.py
import pytest

def pytest_collection_modifyitems(items):
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
```

### Selecting / filtering tests with markers

```bash
# Run only fast tests (exclude slow)
pytest -m "not slow"

# Run only unit tests by directory
pytest tests/unit/

# Run only integration tests by marker
pytest -m integration

# Run smoke tests only (CI gate)
pytest -m smoke

# Combining markers
pytest -m "slow and integration"
pytest -m "slow or e2e"
pytest -m "not (slow or integration)"

# Using -k for substring matching on test names
pytest -k "test_user"
pytest -k "not test_admin"
```

### Parametrize with per-case markers

```python
@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("a", "A"),
        pytest.param("b", "B", marks=pytest.mark.slow),
        ("c", "C"),
    ],
)
def test_uppercase(input, expected):
    assert input.upper() == expected
```

---

## 4. `conftest.py` Organization

### Rules

1. **Root `tests/conftest.py`**: Shared fixtures, global hooks, marker registration
2. **Sub-directory `conftest.py`**: Scope-specific fixtures only
3. **Never bloat the root conftest** — keep it lean

### Example hierarchy

```python
# tests/conftest.py (root)
import pytest

@pytest.fixture
def app_config():
    """Shared test configuration."""
    return {"debug": True, "env": "test"}

def pytest_collection_modifyitems(items):
    """Auto-mark tests based on directory."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
```

```python
# tests/unit/conftest.py
import pytest

@pytest.fixture
def mock_db():
    """In-memory DB mock for unit tests."""
    return {"users": []}
```

```python
# tests/integration/conftest.py
import pytest

@pytest.fixture
def real_db():
    """Actual DB connection for integration tests."""
    # Setup
    db = connect_to_test_db()
    yield db
    # Teardown
    db.cleanup()
```

### `conftest.py` visibility rules

- A `conftest.py` is visible to all tests in its directory and **subdirectories**
- Fixtures defined in `tests/unit/conftest.py` are NOT visible to `tests/integration/`
- This provides natural scope isolation

---

## 5. Running the Suite — Common Patterns

```bash
# Fast feedback loop (unit only, no slow tests)
pytest tests/unit/ -m "not slow" --maxfail=3

# CI: run all with strict markers, fail fast
pytest --strict-markers --maxfail=2 -ra

# CI: parallel execution (requires pytest-xdist)
pytest -n auto -m "not serial"

# CI: integration tests only
pytest -m integration

# CI: smoke/critical path
pytest -m smoke

# Watch mode during development (requires pytest-watch)
ptw -- -m "not slow"

# Run specific test file
pytest tests/unit/test_core.py

# Run specific test by node ID
pytest tests/unit/test_core.py::test_function_name

# Run specific parametrized case
pytest "tests/unit/test_core.py::test_func[param1]"
```

---

## 6. Recommended Marker Taxonomy

| Marker | Purpose | Typical Use |
|--------|---------|-------------|
| `slow` | Tests taking >1s | DB queries, file I/O, computation |
| `integration` | Tests requiring external services | API calls, DB, queues |
| `unit` | Fast isolated tests | Pure logic, no side effects |
| `e2e` | Full workflow tests | User journeys, smoke tests |
| `serial` | Cannot run in parallel | Shared resources, file locks |
| `network` | Requires internet | External API calls |
| `smoke` | Critical path tests | CI gate, deployment checks |

### CI Pipeline example

```yaml
# .github/workflows/test.yml
jobs:
  unit:
    run: pytest -m "not slow" --maxfail=3 -n auto
  integration:
    run: pytest -m integration --maxfail=2
  smoke:
    run: pytest -m smoke
```

---

## 7. Import Mode

For new projects, use `importlib` import mode:

```toml
[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]
```

**Benefits over default `prepend` mode:**
- Does not modify `sys.path`
- Allows test modules with identical names in different directories
- Cleaner import semantics
- No need for `__init__.py` files in test directories

---

## Sources

- [pytest docs — Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [pytest docs — Working with Custom Markers](https://docs.pytest.org/en/stable/example/markers.html)
- [pytest docs — How to Mark Test Functions](https://docs.pytest.org/en/stable/how-to/mark.html)
- [pytest docs — Configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- [Python Packaging User Guide — src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Blog: Python Packaging Structure](https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure)
