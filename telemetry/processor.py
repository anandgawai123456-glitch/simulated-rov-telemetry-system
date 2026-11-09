"""UI-independent telemetry processing pipeline."""
from __future__ import annotations
import time
from .parser import parse_record
from .validator import validate_record, DEFAULT_CONFIG
from .state import TelemetryState

class TelemetryProcessor:
    def __init__(self, config=None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.state = TelemetryState()

    def ingest(self, raw):
        try:
            record = parse_record(raw)
            result = validate_record(record, self.config)
        except Exception as exc:
            from .validator import ValidationResult
            result = ValidationResult(False, errors=[str(exc)])
        self.state.apply(result, time.monotonic())
        return result

    def check_freshness(self):
        return self.state.check_stale(time.monotonic(), self.config["freshness_timeout_s"])
