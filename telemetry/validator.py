"""Field validation and threshold evaluation for simulated ROV telemetry."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class ValidationResult:
    valid: bool
    values: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: str | None = None

DEFAULT_CONFIG = {
    "battery_warning_v": 21.0,
    "battery_critical_v": 19.0,
    "depth_min_m": 0.0,
    "depth_max_m": 100.0,
    "attitude_valid_deg": 180.0,
    "attitude_warning_deg": 45.0,
    "freshness_timeout_s": 3.0,
}

REQUIRED = ("timestamp", "vehicle_mode", "heartbeat_status", "battery_voltage_v", "depth_m", "roll_deg", "pitch_deg", "yaw_deg")

def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO 8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def validate_record(record: dict[str, Any], config: dict[str, float] | None = None) -> ValidationResult:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    errors: list[str] = []
    warnings: list[str] = []
    missing = [key for key in REQUIRED if key not in record]
    if missing:
        return ValidationResult(False, errors=[f"Missing required field(s): {', '.join(missing)}"])
    try:
        ts = _timestamp(record["timestamp"])
    except (ValueError, TypeError) as exc:
        return ValidationResult(False, errors=[f"Invalid timestamp: {exc}"])
    if not isinstance(record["vehicle_mode"], str) or not record["vehicle_mode"].strip():
        errors.append("vehicle_mode must be a non-empty string")
    hb = record["heartbeat_status"]
    if not isinstance(hb, bool):
        errors.append("heartbeat_status must be a boolean")
    numeric: dict[str, float] = {}
    for key in ("battery_voltage_v", "depth_m", "roll_deg", "pitch_deg", "yaw_deg"):
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{key} must be numeric")
            continue
        value = float(value)
        if not (-1e6 < value < 1e6):
            errors.append(f"{key} is outside the supported numeric bounds")
            continue
        numeric[key] = value
    if errors:
        return ValidationResult(False, errors=errors, timestamp=ts.isoformat())
    if numeric["battery_voltage_v"] <= 0:
        errors.append("battery_voltage_v must be greater than 0 V")
    if not cfg["depth_min_m"] <= numeric["depth_m"] <= cfg["depth_max_m"]:
        errors.append(f"depth_m outside valid range {cfg['depth_min_m']}..{cfg['depth_max_m']} m")
    for key in ("roll_deg", "pitch_deg", "yaw_deg"):
        if abs(numeric[key]) > cfg["attitude_valid_deg"]:
            errors.append(f"{key} outside valid range ±{cfg['attitude_valid_deg']}°")
        elif key in ("roll_deg", "pitch_deg") and abs(numeric[key]) > cfg["attitude_warning_deg"]:
          warnings.append(f"{key} exceeds warning threshold ({numeric[key]:.1f}°)")
    if numeric["battery_voltage_v"] < cfg["battery_critical_v"]:
        warnings.append(f"CRITICAL: battery voltage {numeric['battery_voltage_v']:.2f} V below {cfg['battery_critical_v']:.2f} V")
    elif numeric["battery_voltage_v"] < cfg["battery_warning_v"]:
        warnings.append(f"Battery voltage {numeric['battery_voltage_v']:.2f} V below warning threshold {cfg['battery_warning_v']:.2f} V")
    if hb is False:
        warnings.append("Heartbeat not reported by telemetry source")
    values = {"timestamp": ts.isoformat(), "vehicle_mode": record["vehicle_mode"].strip(), "heartbeat_status": hb, **numeric}
    return ValidationResult(not errors, values, errors, warnings, ts.isoformat())
