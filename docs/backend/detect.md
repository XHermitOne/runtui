# backend/detect.md - Platform Detection

Auto-detect platform and create appropriate backend.

---

## Functions

### `create_backend`

```python
def create_backend() -> Backend
```

Create the appropriate backend for the current platform.

**Returns:** `Backend` - A platform-appropriate backend instance

### Platform Detection Logic

| Platform | Backend |
|----------|---------|
| Linux | `UnixBackend` |
| Darwin (macOS) | `UnixBackend` |
| FreeBSD | `UnixBackend` |
| Windows | `WindowsBackend` |
| Other | `UnixBackend` (fallback) |