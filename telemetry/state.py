"""State store: preserves the last valid sample while explicitly tracking its age."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from .validator import ValidationResult

@dataclass
class TelemetryState:
    latest: dict = field(default_factory=dict)
    last_received_monotonic: float | None = None
    quality: str = "UNAVAILABLE"
    diagnostics: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def apply(self, result: ValidationResult, received_monotonic: float) -> None:
        if not result.valid:
            self.quality = "INVALID"
            self.diagnostics.extend(result.errors)
        else:
            self.latest = result.values
            self.last_received_monotonic = received_monotonic
            self.quality = "VALID"
            self.warnings = list(result.warnings)
            self.diagnostics.extend(result.warnings)
        self.diagnostics = self.diagnostics[-100:]

    def check_stale(self, now_monotonic: float, timeout_s: float) -> bool:
        if self.last_received_monotonic is None:
            if self.quality != "INVALID":
                self.quality = "UNAVAILABLE"
            return True
        stale = now_monotonic - self.last_received_monotonic > timeout_s
        if stale:
            self.quality = "STALE"
        elif self.quality == "STALE":
            self.quality = "VALID"
        return stale
