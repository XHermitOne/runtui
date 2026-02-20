# widgets/calendar.py - Calendar Widget

Date picker calendar widget.

---

## Class: `Calendar`

A calendar widget for date selection.

### Constructor

```python
def __init__(
    self,
    year: int = 0,
    month: int = 0,
    day: int = 0,
    id: str | None = None,
    x: int = 0,
    y: int = 0,
    on_select: Callable[[int, int, int], None] | None = None,
) -> None
```

**Parameters:**
- `year` (`int`): Initial year (0 = current year)
- `month` (`int`): Initial month (0 = current month)
- `day` (`int`): Initial day (0 = current day)
- `on_select` (`Callable[[int, int, int], None]`): Callback when date is selected

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `year` | `int` | Selected year |
| `month` | `int` | Selected month (1-12) |
| `day` | `int` | Selected day |

### Key Bindings

| Key | Action |
|-----|--------|
| Arrow keys | Navigate days |
| Page Up/Down | Previous/next month |
| Enter | Select date |

### Mouse Support

- Click to select a day