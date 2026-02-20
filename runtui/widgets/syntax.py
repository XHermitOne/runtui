"""Simple regex-based syntax highlighting for the TextArea widget.

Produces a per-character Color list for each line of source code.
Supports: Python, Shell/Bash, HTML, JavaScript.

Usage:
    highlighter = SyntaxHighlighter.for_extension(".py")
    colors = highlighter.highlight_line(line_text, line_index)
    # colors is a list[Color | None], one per character. None means default fg.
"""

from __future__ import annotations

import re
from typing import Callable

from ..core.types import Color

# -- Palette (works on both light and dark themes) --------------------------

C_KEYWORD = Color.from_rgb(200, 100, 255)   # purple – keywords
C_BUILTIN = Color.from_rgb(80, 200, 255)    # cyan – builtins
C_STRING = Color.from_rgb(206, 145, 100)    # orange-brown – strings
C_COMMENT = Color.from_rgb(106, 153, 85)    # green – comments
C_NUMBER = Color.from_rgb(180, 206, 150)    # light green – numbers
C_DECORATOR = Color.from_rgb(255, 200, 50)  # gold – decorators / @
C_TAG = Color.from_rgb(80, 160, 255)        # blue – HTML tags
C_ATTR = Color.from_rgb(156, 220, 254)      # light blue – HTML attributes
C_FUNC = Color.from_rgb(220, 220, 170)      # pale yellow – function names
C_CONST = Color.from_rgb(100, 200, 180)     # teal – True/False/None/const
C_OPERATOR = Color.from_rgb(200, 200, 200)  # light grey – operators


class SyntaxHighlighter:
    """Base class for per-language highlighters."""

    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        """Return a list of Color|None, one per character in *line*."""
        return [None] * len(line)

    # -- Factory --------------------------------------------------------------

    _ext_map: dict[str, Callable[[], "SyntaxHighlighter"]] = {}

    @classmethod
    def register(cls, *extensions: str):
        """Decorator to register a highlighter for file extensions."""
        def decorator(factory):
            for ext in extensions:
                cls._ext_map[ext] = factory
            return factory
        return decorator

    @classmethod
    def for_extension(cls, ext: str) -> "SyntaxHighlighter | None":
        """Return a highlighter instance for the given extension, or None."""
        ext = ext.lower()
        factory = cls._ext_map.get(ext)
        return factory() if factory else None


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _apply_spans(colors: list[Color | None], spans: list[tuple[int, int, Color]]) -> None:
    """Paint *spans* [(start, end, color), ...] into *colors* list."""
    n = len(colors)
    for start, end, color in spans:
        for i in range(max(0, start), min(end, n)):
            colors[i] = color


# ---------------------------------------------------------------------------
#  Python
# ---------------------------------------------------------------------------

_PY_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
}

_PY_BUILTINS = {
    "print", "len", "range", "int", "str", "float", "list", "dict",
    "set", "tuple", "bool", "type", "isinstance", "hasattr", "getattr",
    "setattr", "open", "super", "property", "staticmethod", "classmethod",
    "enumerate", "zip", "map", "filter", "sorted", "reversed", "any",
    "all", "min", "max", "abs", "sum", "input", "format", "repr",
    "iter", "next", "vars", "dir", "id", "hex", "oct", "bin", "chr",
    "ord", "round", "callable", "hash",
}

_PY_CONSTS = {"True", "False", "None"}

_PY_LINE_RE = re.compile(
    r'(?P<comment>#.*$)'
    r'|(?P<string>"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
    r"|(?P<decorator>@\w+)"
    r"|(?P<number>\b\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)


@SyntaxHighlighter.register(".py")
class PythonHighlighter(SyntaxHighlighter):

    def __init__(self) -> None:
        self._in_triple: str | None = None  # track multi-line strings

    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        colors: list[Color | None] = [None] * len(line)
        spans: list[tuple[int, int, Color]] = []

        # Handle continuation of triple-quoted strings
        if self._in_triple:
            end_idx = line.find(self._in_triple)
            if end_idx >= 0:
                spans.append((0, end_idx + 3, C_STRING))
                rest_start = end_idx + 3
                self._in_triple = None
            else:
                _apply_spans(colors, [(0, len(line), C_STRING)])
                return colors
        else:
            rest_start = 0

        # Tokenize the rest of the line
        for m in _PY_LINE_RE.finditer(line, rest_start):
            s, e = m.start(), m.end()
            if m.group("comment"):
                spans.append((s, e, C_COMMENT))
            elif m.group("string"):
                txt = m.group("string")
                if txt.startswith('"""') or txt.startswith("'''"):
                    delim = txt[:3]
                    # Check if it closes on this line
                    close = txt.find(delim, 3)
                    if close >= 0:
                        spans.append((s, e, C_STRING))
                    else:
                        spans.append((s, e, C_STRING))
                        self._in_triple = delim
                else:
                    spans.append((s, e, C_STRING))
            elif m.group("decorator"):
                spans.append((s, e, C_DECORATOR))
            elif m.group("number"):
                spans.append((s, e, C_NUMBER))
            elif m.group("word"):
                word = m.group("word")
                if word in _PY_CONSTS:
                    spans.append((s, e, C_CONST))
                elif word in _PY_KEYWORDS:
                    spans.append((s, e, C_KEYWORD))
                elif word in _PY_BUILTINS:
                    spans.append((s, e, C_BUILTIN))
                # Detect function definitions: word followed by (
                elif e < len(line) and line[e:].lstrip().startswith("("):
                    # Check if preceded by "def "
                    before = line[:s].rstrip()
                    if before.endswith("def") or before.endswith("class"):
                        spans.append((s, e, C_FUNC))

        _apply_spans(colors, spans)
        return colors


# ---------------------------------------------------------------------------
#  Shell / Bash
# ---------------------------------------------------------------------------

_SH_KEYWORDS = {
    "if", "then", "else", "elif", "fi", "for", "while", "do", "done",
    "case", "esac", "in", "function", "select", "until", "return",
    "local", "export", "readonly", "declare", "typeset", "unset",
    "shift", "source", "eval", "exec", "exit", "trap",
}

_SH_BUILTINS = {
    "echo", "printf", "cd", "pwd", "ls", "cat", "grep", "sed", "awk",
    "find", "xargs", "test", "read", "set", "true", "false",
}

_SH_LINE_RE = re.compile(
    r'(?P<comment>#.*$)'
    r'|(?P<string>"(?:[^"\\]|\\.)*"|\'[^\']*\')'
    r"|(?P<variable>\$\{?\w+\}?)"
    r"|(?P<number>\b\d+\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)


@SyntaxHighlighter.register(".sh", ".bash", ".zsh")
class ShellHighlighter(SyntaxHighlighter):

    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        colors: list[Color | None] = [None] * len(line)
        spans: list[tuple[int, int, Color]] = []

        for m in _SH_LINE_RE.finditer(line):
            s, e = m.start(), m.end()
            if m.group("comment"):
                spans.append((s, e, C_COMMENT))
            elif m.group("string"):
                spans.append((s, e, C_STRING))
            elif m.group("variable"):
                spans.append((s, e, C_CONST))
            elif m.group("number"):
                spans.append((s, e, C_NUMBER))
            elif m.group("word"):
                word = m.group("word")
                if word in _SH_KEYWORDS:
                    spans.append((s, e, C_KEYWORD))
                elif word in _SH_BUILTINS:
                    spans.append((s, e, C_BUILTIN))

        _apply_spans(colors, spans)
        return colors


# ---------------------------------------------------------------------------
#  HTML
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(
    r'(?P<comment><!--[\s\S]*?-->)'
    r'|(?P<string>"[^"]*"|\'[^\']*\')'
    r"|(?P<tag></?\w+|/?>)"
    r"|(?P<attr>\b[a-zA-Z_][\w-]*(?=\s*=))"
)


@SyntaxHighlighter.register(".html", ".htm")
class HtmlHighlighter(SyntaxHighlighter):

    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        colors: list[Color | None] = [None] * len(line)
        spans: list[tuple[int, int, Color]] = []

        for m in _HTML_TAG_RE.finditer(line):
            s, e = m.start(), m.end()
            if m.group("comment"):
                spans.append((s, e, C_COMMENT))
            elif m.group("string"):
                spans.append((s, e, C_STRING))
            elif m.group("tag"):
                spans.append((s, e, C_TAG))
            elif m.group("attr"):
                spans.append((s, e, C_ATTR))

        _apply_spans(colors, spans)
        return colors


# ---------------------------------------------------------------------------
#  JavaScript
# ---------------------------------------------------------------------------

_JS_KEYWORDS = {
    "break", "case", "catch", "class", "const", "continue", "debugger",
    "default", "delete", "do", "else", "export", "extends", "finally",
    "for", "function", "if", "import", "in", "instanceof", "let", "new",
    "of", "return", "static", "super", "switch", "this", "throw", "try",
    "typeof", "var", "void", "while", "with", "yield", "async", "await",
    "from", "as",
}

_JS_CONSTS = {"true", "false", "null", "undefined", "NaN", "Infinity"}

_JS_BUILTINS = {
    "console", "Math", "JSON", "Array", "Object", "String", "Number",
    "Boolean", "Date", "RegExp", "Error", "Map", "Set", "Promise",
    "parseInt", "parseFloat", "isNaN", "isFinite", "setTimeout",
    "setInterval", "fetch", "require", "module", "exports",
}

_JS_LINE_RE = re.compile(
    r'(?P<comment>//.*$|/\*.*?\*/)'
    r'|(?P<string>"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|`(?:[^`\\]|\\.)*`)'
    r"|(?P<number>\b\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_$]\w*\b)"
)


@SyntaxHighlighter.register(".js", ".ts", ".jsx", ".tsx")
class JavaScriptHighlighter(SyntaxHighlighter):

    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        colors: list[Color | None] = [None] * len(line)
        spans: list[tuple[int, int, Color]] = []

        for m in _JS_LINE_RE.finditer(line):
            s, e = m.start(), m.end()
            if m.group("comment"):
                spans.append((s, e, C_COMMENT))
            elif m.group("string"):
                spans.append((s, e, C_STRING))
            elif m.group("number"):
                spans.append((s, e, C_NUMBER))
            elif m.group("word"):
                word = m.group("word")
                if word in _JS_CONSTS:
                    spans.append((s, e, C_CONST))
                elif word in _JS_KEYWORDS:
                    spans.append((s, e, C_KEYWORD))
                elif word in _JS_BUILTINS:
                    spans.append((s, e, C_BUILTIN))
                elif e < len(line) and line[e:].lstrip().startswith("("):
                    before = line[:s].rstrip()
                    if before.endswith("function") or before.endswith("."):
                        spans.append((s, e, C_FUNC))

        _apply_spans(colors, spans)
        return colors

# --- --- ---
# ---------------------------------------------------------------------------
#  C-Style Base (Helper for C/C++, Java, C#, Go, TS)
# ---------------------------------------------------------------------------

class BaseCStyleHighlighter(SyntaxHighlighter):
    """
    Base class for languages using C-style comments:
    - // Single line
    - /* Multi line */
    """
    def __init__(self) -> None:
        self._in_block_comment = False

    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        colors: list[Color | None] = [None] * len(line)
        spans: list[tuple[int, int, Color]] = []
        rest_start = 0

        # 1. Handle continuation of block comments
        if self._in_block_comment:
            end_idx = line.find("*/")
            if end_idx >= 0:
                spans.append((0, end_idx + 2, C_COMMENT))
                rest_start = end_idx + 2
                self._in_block_comment = False
            else:
                _apply_spans(colors, [(0, len(line), C_COMMENT)])
                return colors

        # 2. Tokenize the rest of the line
        # Note: Subclasses must define self.line_re and self.keywords/builtins
        for m in self.line_re.finditer(line, rest_start):
            s, e = m.start(), m.end()
            
            # Check for Block Comment start matching
            if m.groupdict().get("block_comment_start"):
                # We found a '/*', check if it closes on this line
                txt = m.group("block_comment_start") # usually just matches /*
                close_idx = line.find("*/", s + 2)
                if close_idx >= 0:
                    spans.append((s, close_idx + 2, C_COMMENT))
                    # Note: We rely on regex finditer to not overlap, 
                    # but regex engine skips 'e'. We might miss stuff if regex
                    # matched a huge chunk. But for simple '/*' match it's fine.
                else:
                    spans.append((s, len(line), C_COMMENT))
                    self._in_block_comment = True
                    # Stop processing this line as the rest is comment
                    break 

            elif m.group("comment"):
                spans.append((s, e, C_COMMENT))
            elif m.group("string"):
                spans.append((s, e, C_STRING))
            elif m.group("number"):
                spans.append((s, e, C_NUMBER))
            elif m.group("decorator"):
                spans.append((s, e, C_DECORATOR))
            elif m.group("word"):
                word = m.group("word")
                if word in self.keywords:
                    spans.append((s, e, C_KEYWORD))
                elif word in self.builtins:
                    spans.append((s, e, C_BUILTIN))
                elif word in self.consts:
                    spans.append((s, e, C_CONST))
                # Heuristic for functions: word followed by '('
                elif e < len(line) and line[e:].lstrip().startswith("("):
                     spans.append((s, e, C_FUNC))

        _apply_spans(colors, spans)
        return colors

    # Default empty sets, to be overridden
    line_re: re.Pattern
    keywords: set[str] = set()
    builtins: set[str] = set()
    consts: set[str] = set()


# ---------------------------------------------------------------------------
#  C / C++
# ---------------------------------------------------------------------------

_CPP_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
    "bool", "break", "case", "catch", "char", "char16_t", "char32_t",
    "class", "compl", "const", "constexpr", "const_cast", "continue",
    "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float",
    "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
    "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator",
    "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch", "template", "this",
    "thread_local", "throw", "true", "try", "typedef", "typeid",
    "typename", "union", "unsigned", "using", "virtual", "void", "volatile",
    "wchar_t", "while", "xor", "xor_eq"
}

_CPP_TYPES_BUILTINS = {
    "std", "vector", "string", "map", "set", "unique_ptr", "shared_ptr",
    "cout", "cin", "endl", "printf", "fprintf", "malloc", "free", "size_t",
}

# Matches Preprocessor (#include...), comments, strings, numbers, words
_CPP_LINE_RE = re.compile(
    r'(?P<comment>//.*$)'
    r'|(?P<block_comment_start>/\*)'
    r'|(?P<decorator>^\s*#\w+)'  # Preprocessor directives
    r'|(?P<string>"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
    r"|(?P<number>\b\d[\d_]*[uUlLfF]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)

@SyntaxHighlighter.register(".c", ".h", ".cpp", ".hpp", ".cc", ".cxx")
class CppHighlighter(BaseCStyleHighlighter):
    def __init__(self):
        super().__init__()
        self.line_re = _CPP_LINE_RE
        self.keywords = _CPP_KEYWORDS
        self.builtins = _CPP_TYPES_BUILTINS
        self.consts = {"true", "false", "nullptr", "NULL"}


# ---------------------------------------------------------------------------
#  Java
# ---------------------------------------------------------------------------

_JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "var", "record"
}

_JAVA_BUILTINS = {
    "String", "Object", "System", "Integer", "Boolean", "Math", "List",
    "Map", "Set", "ArrayList", "HashMap", "Exception", "Runnable", "Thread"
}

_JAVA_LINE_RE = re.compile(
    r'(?P<comment>//.*$)'
    r'|(?P<block_comment_start>/\*)'
    r'|(?P<string>"(?:[^"\\]|\\.)*")' # Java chars are single quote, handled as 'word' or need specific regex
    r"|(?P<decorator>@\w+)" 
    r"|(?P<number>\b\d[\d_]*[lLfFdD]?(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)

@SyntaxHighlighter.register(".java")
class JavaHighlighter(BaseCStyleHighlighter):
    def __init__(self):
        super().__init__()
        self.line_re = _JAVA_LINE_RE
        self.keywords = _JAVA_KEYWORDS
        self.builtins = _JAVA_BUILTINS
        self.consts = {"true", "false", "null"}


# ---------------------------------------------------------------------------
#  C#
# ---------------------------------------------------------------------------

_CS_KEYWORDS = {
    "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
    "char", "checked", "class", "const", "continue", "decimal", "default",
    "delegate", "do", "double", "else", "enum", "event", "explicit",
    "extern", "false", "finally", "fixed", "float", "for", "foreach",
    "goto", "if", "implicit", "in", "int", "interface", "internal", "is",
    "lock", "long", "namespace", "new", "null", "object", "operator",
    "out", "override", "params", "private", "protected", "public",
    "readonly", "ref", "return", "sbyte", "sealed", "short", "sizeof",
    "stackalloc", "static", "string", "struct", "switch", "this", "throw",
    "true", "try", "typeof", "uint", "ulong", "unchecked", "unsafe",
    "ushort", "using", "virtual", "void", "volatile", "while", "async",
    "await", "var", "get", "set", "value", "dynamic"
}

_CS_BUILTINS = {
    "Console", "List", "Dictionary", "Task", "Func", "Action", "IEnumerable",
    "Math", "String", "Int32", "Boolean", "DateTime"
}

_CS_LINE_RE = re.compile(
    r'(?P<comment>//.*$)'
    r'|(?P<block_comment_start>/\*)'
    r'|(?P<string>@"(?:[^"]|"")*"|"(?:[^"\\]|\\.)*")' # Supports verbatim strings @"..."
    r'|(?P<decorator>\[\w+\])' # Attributes [Test]
    r"|(?P<number>\b\d[\d_]*[uUlLmMfF]?(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)

@SyntaxHighlighter.register(".cs")
class CSharpHighlighter(BaseCStyleHighlighter):
    def __init__(self):
        super().__init__()
        self.line_re = _CS_LINE_RE
        self.keywords = _CS_KEYWORDS
        self.builtins = _CS_BUILTINS
        self.consts = {"true", "false", "null"}


# ---------------------------------------------------------------------------
#  Go
# ---------------------------------------------------------------------------

_GO_KEYWORDS = {
    "break", "case", "chan", "const", "continue", "default", "defer",
    "else", "fallthrough", "for", "func", "go", "goto", "if", "import",
    "interface", "map", "package", "range", "return", "select", "struct",
    "switch", "type", "var"
}

_GO_BUILTINS = {
    "append", "cap", "close", "complex", "copy", "delete", "imag", "len",
    "make", "new", "panic", "print", "println", "real", "recover",
    "bool", "string", "int", "int8", "int16", "int32", "int64",
    "uint", "uint8", "uint16", "uint32", "uint64", "uintptr",
    "byte", "rune", "float32", "float64", "complex64", "complex128", "error"
}

_GO_LINE_RE = re.compile(
    r'(?P<comment>//.*$)'
    r'|(?P<block_comment_start>/\*)'
    r'|(?P<string>"(?:[^"\\]|\\.)*"|`(?:[^`]|\\.)*`)'
    r"|(?P<number>\b\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)

@SyntaxHighlighter.register(".go")
class GoHighlighter(BaseCStyleHighlighter):
    def __init__(self):
        super().__init__()
        self.line_re = _GO_LINE_RE
        self.keywords = _GO_KEYWORDS
        self.builtins = _GO_BUILTINS
        self.consts = {"true", "false", "nil", "iota"}


# ---------------------------------------------------------------------------
#  TypeScript
#  (Note: Overrides .ts/.tsx from the JS highlighter to add types)
# ---------------------------------------------------------------------------

_TS_KEYWORDS = _JS_KEYWORDS | {
    "interface", "type", "enum", "implements", "declare", "namespace",
    "readonly", "abstract", "any", "void", "number", "string", "boolean",
    "never", "unknown", "keyof", "unique", "symbol"
}

_TS_LINE_RE = re.compile(
    r'(?P<comment>//.*$)'
    r'|(?P<block_comment_start>/\*)'
    r'|(?P<string>"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|`(?:[^`\\]|\\.)*`)'
    r"|(?P<decorator>@\w+)"
    r"|(?P<number>\b\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_$]\w*\b)"
)

@SyntaxHighlighter.register(".ts", ".tsx")
class TypeScriptHighlighter(BaseCStyleHighlighter):
    def __init__(self):
        super().__init__()
        self.line_re = _TS_LINE_RE
        self.keywords = _TS_KEYWORDS
        self.builtins = _JS_BUILTINS
        self.consts = _JS_CONSTS


# ---------------------------------------------------------------------------
#  R
# ---------------------------------------------------------------------------

_R_KEYWORDS = {
    "if", "else", "repeat", "while", "function", "for", "in", "next",
    "break", "library", "require", "source", "return"
}

_R_CONSTS = {"TRUE", "FALSE", "NULL", "NA", "NaN", "Inf"}

_R_LINE_RE = re.compile(
    r'(?P<comment>#.*$)'
    r'|(?P<string>"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
    r"|(?P<number>\b\d[\d_]*(?:\.\d[\d_]*)?L?\b)" # 10L is integer in R
    r"|(?P<word>\b[A-Za-z_.][\w.]*\b)" # R allows dots in identifiers
)

@SyntaxHighlighter.register(".r", ".R")
class RHighlighter(SyntaxHighlighter):
    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        colors: list[Color | None] = [None] * len(line)
        spans: list[tuple[int, int, Color]] = []

        for m in _R_LINE_RE.finditer(line):
            s, e = m.start(), m.end()
            if m.group("comment"):
                spans.append((s, e, C_COMMENT))
            elif m.group("string"):
                spans.append((s, e, C_STRING))
            elif m.group("number"):
                spans.append((s, e, C_NUMBER))
            elif m.group("word"):
                word = m.group("word")
                if word in _R_CONSTS:
                    spans.append((s, e, C_CONST))
                elif word in _R_KEYWORDS:
                    spans.append((s, e, C_KEYWORD))
                elif word in {"c", "list", "vector", "matrix", "data.frame", "factor"}:
                    spans.append((s, e, C_BUILTIN))
                # Function call detection
                elif e < len(line) and line[e:].lstrip().startswith("("):
                    spans.append((s, e, C_FUNC))
        
        _apply_spans(colors, spans)
        return colors


# ---------------------------------------------------------------------------
#  SQL
# ---------------------------------------------------------------------------

_SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
    "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "INDEX", "VIEW", "JOIN",
    "INNER", "OUTER", "LEFT", "RIGHT", "ON", "GROUP", "BY", "ORDER", "HAVING",
    "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT", "AS", "CASE", "WHEN",
    "THEN", "ELSE", "END", "AND", "OR", "NOT", "NULL", "IS", "IN", "EXISTS",
    "LIKE", "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "DEFAULT", "CONSTRAINT",
    "BEGIN", "COMMIT", "ROLLBACK", "TRANSACTION", "GRANT", "REVOKE"
}

_SQL_TYPES = {
    "INT", "INTEGER", "VARCHAR", "CHAR", "TEXT", "DATE", "DATETIME",
    "TIMESTAMP", "BOOLEAN", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "BLOB"
}

_SQL_LINE_RE = re.compile(
    r'(?P<comment>--.*$)'
    r'|(?P<string>\'(?:[^\']|\'\')*\')' # SQL strings are '...', '' escape
    r'|(?P<number>\b\d+\.?\d*\b)'
    r"|(?P<word>\b[A-Za-z_]\w*\b)"
)

@SyntaxHighlighter.register(".sql")
class SqlHighlighter(SyntaxHighlighter):
    def highlight_line(self, line: str, line_index: int) -> list[Color | None]:
        colors: list[Color | None] = [None] * len(line)
        spans: list[tuple[int, int, Color]] = []

        for m in _SQL_LINE_RE.finditer(line):
            s, e = m.start(), m.end()
            if m.group("comment"):
                spans.append((s, e, C_COMMENT))
            elif m.group("string"):
                spans.append((s, e, C_STRING))
            elif m.group("number"):
                spans.append((s, e, C_NUMBER))
            elif m.group("word"):
                # Case-insensitive check
                word = m.group("word").upper()
                if word in _SQL_KEYWORDS:
                    spans.append((s, e, C_KEYWORD))
                elif word in _SQL_TYPES:
                    spans.append((s, e, C_BUILTIN))
                elif word in {"TRUE", "FALSE", "NULL"}:
                     spans.append((s, e, C_CONST))
        
        _apply_spans(colors, spans)
        return colors 