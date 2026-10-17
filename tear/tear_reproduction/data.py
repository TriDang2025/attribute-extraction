"""Input and labeled-pool loading for the TEAR reproduction runner."""

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Read a JSONL file and report malformed lines with their source location."""
    records = []
    with Path(path).open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {error.msg}"
                ) from error
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
            records.append(value)
    return records


def validate_example(example: Dict[str, Any], source: str = "example") -> Dict[str, Any]:
    """Validate and normalize a text/table example."""
    text = example.get("text")
    table = example.get("table")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{source}: 'text' must be a non-empty string")
    if not isinstance(table, dict):
        raise ValueError(f"{source}: 'table' must be an object")

    headers = table.get("headers")
    rows = table.get("rows")
    if not isinstance(headers, list) or not headers:
        raise ValueError(f"{source}: table.headers must be a non-empty list")
    if any(not isinstance(header, str) or not header.strip() for header in headers):
        raise ValueError(f"{source}: each table header must be a non-empty string")
    headers = [header.strip() for header in headers]
    if len(set(headers)) != len(headers):
        raise ValueError(f"{source}: table headers must be unique")
    if not isinstance(rows, list):
        raise ValueError(f"{source}: table.rows must be a list")
    for row_number, row in enumerate(rows, start=1):
        if not isinstance(row, list) or len(row) != len(headers):
            raise ValueError(
                f"{source}: row {row_number} must be a list with {len(headers)} cells"
            )
        for cell in row:
            if cell is not None and not isinstance(cell, (str, list, int, float, bool)):
                raise ValueError(f"{source}: table cells must be scalar strings or span lists")
            if isinstance(cell, list) and any(not isinstance(span, str) for span in cell):
                raise ValueError(f"{source}: span-list cells may contain only strings")
    return {"text": text.strip(), "table": {"headers": headers, "rows": rows}}


def validate_headers(headers: Iterable[str], source: str = "schema") -> List[str]:
    """Return a clean header list or fail on malformed input."""
    if isinstance(headers, (str, bytes)):
        raise ValueError(f"{source} must be a list of header strings, not a string")
    result = list(headers)
    if not result or any(not isinstance(item, str) or not item.strip() for item in result):
        raise ValueError(f"{source} must contain at least one non-empty header string")
    return [item.strip() for item in result]


def _repair_json(text: str) -> str:
    """Undo the template artifacts small models copy from the prompt's JSON structure:
    '"1":{...},' and '...' placeholder lines, and trailing commas."""
    text = re.sub(r'"[^"\n]*"\s*:\s*\{\s*\.\.\.\s*\}\s*,?', "", text)
    text = re.sub(r"^\s*\.\.\.\s*,?\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    # Close brackets the model left open (scanning outside string literals only).
    start = text.find("{")
    if start < 0:
        return text
    stack, in_string, escape, end = [], False, False, len(text)
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            escape = ch == "\\" and not escape
            if ch == '"' and not escape:
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if stack:
                stack.pop()
            if not stack:
                return text
        end = i + 1
    return text[:end].rstrip().rstrip(",") + "".join(reversed(stack))


def parse_json_object(content: str, source: str) -> Dict[str, Any]:
    """Parse a JSON object, allowing a Markdown JSON fence or text around the object."""
    value = content.strip()
    fence = re.search(r"```(?:json)?\s*\n(.*?)```", value, flags=re.DOTALL)
    if fence:
        value = fence.group(1).strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        # Small local models often wrap the object in prose; use the first object found.
        start = value.find("{")
        parsed = None
        for candidate in (value, _repair_json(value)):
            start = candidate.find("{")
            if start < 0:
                continue
            try:
                parsed, _ = json.JSONDecoder().raw_decode(candidate, start)
                break
            except json.JSONDecodeError:
                continue
        if parsed is None:
            excerpt = value[:240].replace("\n", " ")
            raise ValueError(
                f"{source}: model returned invalid JSON near {excerpt!r}"
            ) from error
    if not isinstance(parsed, dict):
        raise ValueError(f"{source}: model response must be a JSON object")
    return parsed
