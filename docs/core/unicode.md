# unicode.py - Unicode Width Utilities

Utilities for measuring and manipulating Unicode strings based on their terminal display width.

---

## Functions

### `char_width`

```python
@functools.lru_cache(maxsize=4096)
def char_width(ch: str) -> int
```

Return the display width of a single character: 0, 1, or 2.

- Returns `0` for control characters, zero-width characters, and combining marks
- Returns `2` for East Asian Wide and Fullwidth characters
- Returns `1` for all other characters

**Parameters:**
- `ch` (`str`): A single character

**Returns:** `int` - The display width (0, 1, or 2)

---

### `string_width`

```python
def string_width(s: str) -> int
```

Return the total display width of a string.

**Parameters:**
- `s` (`str`): The string to measure

**Returns:** `int` - Total display width in terminal columns

---

### `truncate_to_width`

```python
def truncate_to_width(
    s: str,
    max_width: int,
    ellipsis: str = "…",
) -> str
```

Truncate a string to fit within a maximum display width.

If the string is truncated, an ellipsis is appended.

**Parameters:**
- `s` (`str`): The string to truncate
- `max_width` (`int`): Maximum display width in columns
- `ellipsis` (`str`): Ellipsis character to append (default: "…")

**Returns:** `str` - The truncated string

---

### `pad_to_width`

```python
def pad_to_width(
    s: str,
    target_width: int,
    fill: str = " ",
    align: str = "left",
) -> str
```

Pad a string to exactly the specified display width.

**Parameters:**
- `s` (`str`): The string to pad
- `target_width` (`int`): Target display width
- `fill` (`str`): Fill character (default: space)
- `align` (`str`): Alignment - `"left"`, `"right"`, or `"center"`

**Returns:** `str` - The padded string

---

### `split_by_width`

```python
def split_by_width(s: str, width: int) -> list[str]
```

Split a string into lines that fit within the given display width.

Respects existing newlines and breaks at width boundaries.

**Parameters:**
- `s` (`str`): The string to split
- `width` (`int`): Maximum width per line

**Returns:** `list[str]` - List of lines