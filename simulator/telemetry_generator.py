from __future__ import annotations
import json
import math
from datetime import datetime, timezone


class TelemetryGenerator:
    """Generates plausible ROV telemetry with injectable simultaneous faults."""

    def __init__(self):
        self.index = 0
        self.fault = "none"
        self.faults = set()

    def next_record(self) -> str:
        i = self.index
        self.index += 1

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vehicle_mode": "MANUAL" if i % 20 < 10 else "STABILIZE",
            "heartbeat_status": True,
            "battery_voltage_v": round(24.2 - 0.015 * i, 2),
            "depth_m": round(8.0 + 1.5 * math.sin(i / 8), 2),
            "roll_deg": round(5.0 * math.sin(i / 4), 2),
            "pitch_deg": round(7.0 * math.cos(i / 6), 2),
            "yaw_deg": round((i * 3.0) % 360 - 180, 2),
        }

        active = set(self.faults)
        if self.fault != "none":
            active.add(self.fault)

        if "malformed" in active:
            return '{"timestamp": broken-json'

        if "missing" in active:
            record.pop("depth_m", None)

        if "low_battery" in active:
            record["battery_voltage_v"] = 18.4

        if "sensor_range" in active:
            record["roll_deg"] = 190.0

        if "heartbeat" in active:
            record["heartbeat_status"] = False

        return json.dumps(record)
