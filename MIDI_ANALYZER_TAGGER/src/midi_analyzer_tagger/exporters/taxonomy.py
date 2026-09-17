import json
from pathlib import Path

from midi_analyzer_tagger.analysis.registry import ExtractorRegistry


def _inline_json(value) -> str:
    """Serialise a value as compact, single-line JSON."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


_MAX_COMPACT_LEN = 80


def _is_compact(value) -> bool:
    """Return True if a value should be rendered on a single line."""
    if isinstance(value, (list, tuple)):
        if not value:
            return True
        if not all(isinstance(item, (int, float, str, bool)) or item is None for item in value):
            return False
    elif isinstance(value, dict):
        if not value:
            return True
        if not all(
            isinstance(k, (int, str)) and (isinstance(v, (int, float, str, bool)) or v is None)
            for k, v in value.items()
        ):
            return False
    else:
        return False
    # Keep the line readable — don't inline if it would be too long
    return len(_inline_json(value)) <= _MAX_COMPACT_LEN


def _dump_value(value, indent: int, level: int, is_last: bool) -> list[str]:
    """Render one JSON value. Returns a list of lines already terminated."""
    pad = " " * (indent * level)
    comma = "" if is_last else ","

    if _is_compact(value):
        return [f"{pad}{_inline_json(value)}{comma}"]

    if isinstance(value, dict):
        if not value:
            return [f"{pad}{{}}{comma}"]
        lines = [f"{pad}{{"]
        items = list(value.items())
        for i, (k, v) in enumerate(items):
            sub = _dump_value(v, indent, level + 1, is_last=(i == len(items) - 1))
            key_line = f'{" " * (indent * (level + 1))}{_inline_json(str(k))}:'
            if sub:
                first = sub[0].lstrip()
                lines.append(f"{key_line} {first}")
                lines.extend(sub[1:])
            else:
                lines.append(f"{key_line} null{comma if i < len(items) - 1 else ''}")
        lines.append(f'{" " * (indent * level)}}}' + comma)
        return lines

    if isinstance(value, (list, tuple)):
        if not value:
            return [f"{pad}[]{comma}"]
        lines = [f"{pad}["]
        items = list(value)
        for i, item in enumerate(items):
            sub = _dump_value(item, indent, level + 1, is_last=(i == len(items) - 1))
            if sub:
                lines.extend(sub)
            else:
                lines.append(f'{" " * (indent * (level + 1))}null' + ("" if i == len(items) - 1 else ","))
        lines.append(f'{" " * (indent * level)}]' + comma)
        return lines

    return [f"{pad}{_inline_json(value)}{comma}"]


def _dump(obj, indent: int) -> str:
    lines = _dump_value(obj, indent, 0, is_last=True)
    return "\n".join(lines)


class TaxonomyExporter:
    """Export the concept taxonomy from a registry to JSON."""

    def __init__(self, registry: ExtractorRegistry):
        self.registry = registry

    def to_dict(self) -> dict:
        return self.registry.compile_taxonomy()

    def to_json(self, path: str | Path, indent: int = 2) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(_dump(self.to_dict(), indent) + "\n")
