# rad/runner.py - RAD Runner

Run RAD-designed applications.

---

## Functions

### `run_schema`

```python
def run_schema(schema: WidgetSchema) -> None
```

Run an application from a schema.

**Parameters:**
- `schema` (`WidgetSchema`): The application schema

### `run_file`

```python
def run_file(path: str) -> None
```

Run an application from a JSON file.

**Parameters:**
- `path` (`str`): Path to the JSON file

### `run_json`

```python
def run_json(json_str: str) -> None
```

Run an application from a JSON string.

**Parameters:**
- `json_str` (`str`): JSON string

### Usage

From command line:

```bash
python -m runtui.rad my_app.json
```

From Python:

```python
from runtui.rad import run_file
run_file("my_app.json")
```