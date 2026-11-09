from __future__ import annotations
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer
from telemetry.processor import TelemetryProcessor
from simulator.telemetry_generator import TelemetryGenerator

ROOT = Path(__file__).resolve().parent

class DashboardBackend(QObject):
    changed = Signal()
    def __init__(self):
        super().__init__()
        config_path = ROOT / "config" / "thresholds.json"
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else None
        self.processor = TelemetryProcessor(config)
        self.generator = TelemetryGenerator()
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._tick)
        self.watchdog = QTimer(self)
        self.watchdog.setInterval(250)
        self.watchdog.timeout.connect(self._check_stale)
        self._running = False
        self._diagnostics = []
        self._last_quality = "UNAVAILABLE"
        self._log_path = ROOT / "logs" / "events.log"
        self._log_path.parent.mkdir(exist_ok=True)

    def _log(self, message):
        stamp = datetime.now(timezone.utc).isoformat()
        line = f"{stamp} | {message}"
        self._diagnostics.insert(0, line)
        self._diagnostics = self._diagnostics[:12]
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _tick(self):
        if self.generator.fault == "stream_stop":
            self._check_stale()
            return
        raw = self.generator.next_record()
        result = self.processor.ingest(raw)
        if result.errors:
            for error in result.errors:
                self._log(f"INVALID RECORD: {error}")
        for warning in result.warnings:
            self._log(f"WARNING: {warning}")
        self._check_stale()
        self.changed.emit()

    def _check_stale(self):
        stale = self.processor.check_freshness()
        quality = self.processor.state.quality
        if quality != self._last_quality:
            if quality == "STALE": self._log("FAULT: telemetry stream stale; no recent valid samples")
            elif quality == "VALID" and self._last_quality in {"STALE", "INVALID"}: self._log("RECOVERY: valid telemetry stream resumed")
            self._last_quality = quality
        self.changed.emit()

    def _value(self, key, default="—"):
        value = self.processor.state.latest.get(key, default)
        return str(value)

    @Property(str, notify=changed)
    def connectionStatus(self):
        q = self.processor.state.quality
        return "CONNECTED" if q == "VALID" else ("STALE" if q == "STALE" else q)

    @Property(str, notify=changed)
    def quality(self): return self.processor.state.quality
    @Property(str, notify=changed)
    def mode(self): return self._value("vehicle_mode")
    @Property(str, notify=changed)
    def heartbeat(self): return "OK" if self.processor.state.latest.get("heartbeat_status") else "LOST"
    @Property(str, notify=changed)
    def battery(self): return self._format("battery_voltage_v", " V")
    @Property(str, notify=changed)
    def depth(self): return self._format("depth_m", " m")
    @Property(str, notify=changed)
    def roll(self): return self._format("roll_deg", "°")
    @Property(str, notify=changed)
    def pitch(self): return self._format("pitch_deg", "°")
    @Property(str, notify=changed)
    def yaw(self): return self._format("yaw_deg", "°")
    @Property(str, notify=changed)
    def warnings(self): return "\n".join(self.processor.state.warnings) or "No active warnings"
    @Property(str, notify=changed)
    def diagnostics(self): return "\n".join(self._diagnostics) or "No diagnostic events yet"
    @Property(str, notify=changed)
    def running(self): return "RUNNING" if self._running else "STOPPED"

    def _format(self, key, unit):
        val = self.processor.state.latest.get(key)
        return f"{val:.2f}{unit}" if isinstance(val, (int, float)) else "—"

    @Slot()
    def start(self):
        if not self._running:
            self.generator.fault = "none"
            self.generator.faults.clear()
            self._running = True
            self.watchdog.stop()
            self.timer.start()
            self._log("SIMULATOR STARTED")
            self.changed.emit()

    @Slot()
    def stop(self):
        self.timer.stop()
        self._running = False
        self.watchdog.start()
        self._log("SIMULATOR STOPPED by operator; freshness monitoring continues")
        self.changed.emit()

    @Slot(str)
    def injectFault(self, fault):
        allowed = {"none", "malformed", "missing", "low_battery", "sensor_range", "heartbeat", "stream_stop"}
        if fault not in allowed: return
        self.generator.faults.clear()
        self.generator.fault = fault
        self._log(f"FAULT INJECTION SELECTED: {fault}")
        if fault == "stream_stop": self._check_stale()
        self.changed.emit()

    @Slot()
    def injectMultipleFaults(self):
        self.generator.fault = "none"
        self.generator.faults = {"low_battery", "heartbeat"}
        self._log("MULTIPLE FAULTS INJECTED: low battery and heartbeat lost")
        self.changed.emit()

    @Slot()
    def clearFault(self):
        self.generator.fault = "none"
        self.generator.faults.clear()
        if not self._running:
            self.start()
        self._log("FAULT INJECTION CLEARED; normal stream will resume")
        self.changed.emit()
