"""Parse JSON telemetry records into dictionaries without raising on bad input."""
from __future__ import annotations
import json
from typing import Any

class TelemetryParseError(ValueError):
    pass

def parse_record(raw: str | bytes | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TelemetryParseError(f"Input is not valid UTF-8: {exc}") from exc
    if not isinstance(raw, str):
        raise TelemetryParseError("Telemetry record must be JSON text, bytes, or a dictionary")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TelemetryParseError(f"Malformed JSON at line {exc.lineno}, column {exc.colno}") from exc
    if not isinstance(value, dict):
        raise TelemetryParseError("Telemetry JSON root must be an object")
    return value
