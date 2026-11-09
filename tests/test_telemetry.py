import json
from telemetry.processor import TelemetryProcessor
from telemetry.parser import parse_record, TelemetryParseError
from telemetry.validator import validate_record

BASE = {
    "timestamp": "2026-11-07T06:30:00Z", "vehicle_mode": "MANUAL", "heartbeat_status": True,
    "battery_voltage_v": 24.1, "depth_m": 12.5, "roll_deg": 1.0, "pitch_deg": -2.0, "yaw_deg": 90.0
}

def test_valid_record_is_accepted():
    result = validate_record(BASE)
    assert result.valid
    assert result.values["depth_m"] == 12.5

def test_yaw_heading_does_not_trigger_attitude_warning():
    record = dict(BASE, yaw_deg=-180.0)
    result = validate_record(record)

    assert result.valid
    assert not any("yaw_deg" in warning for warning in result.warnings)


def test_roll_exceeding_warning_threshold_generates_warning():
    record = dict(BASE, roll_deg=50.0)
    result = validate_record(record)

    assert result.valid
    assert any("roll_deg" in warning for warning in result.warnings)

def test_missing_field_is_rejected():
    record = dict(BASE); record.pop("depth_m")
    result = validate_record(record)
    assert not result.valid
    assert "depth_m" in result.errors[0]

def test_malformed_json_does_not_crash_processor():
    processor = TelemetryProcessor()
    result = processor.ingest("{not-json")
    assert not result.valid
    assert processor.state.quality == "INVALID"

def test_low_battery_generates_warning():
    record = dict(BASE, battery_voltage_v=18.5)
    result = validate_record(record)
    assert result.valid
    assert any("CRITICAL" in warning for warning in result.warnings)

def test_sensor_out_of_range_is_rejected():
    record = dict(BASE, roll_deg=190)
    result = validate_record(record)
    assert not result.valid
    assert any("roll_deg" in error for error in result.errors)

def test_bad_numeric_type_is_rejected():
    record = dict(BASE, pitch_deg="level")
    result = validate_record(record)
    assert not result.valid
    assert any("pitch_deg" in error for error in result.errors)


def test_stream_becomes_stale_and_recovers():
    from telemetry.state import TelemetryState
    from telemetry.validator import ValidationResult
    state = TelemetryState()
    state.apply(ValidationResult(True, values={"battery_voltage_v": 24.0}), received_monotonic=10.0)
    assert not state.check_stale(12.0, 3.0)
    assert state.quality == "VALID"
    assert state.check_stale(14.0, 3.0)
    assert state.quality == "STALE"
    state.apply(ValidationResult(True, values={"battery_voltage_v": 23.9}), received_monotonic=14.1)
    assert state.quality == "VALID"
