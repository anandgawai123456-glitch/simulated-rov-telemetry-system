import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from app_backend import DashboardBackend


app = QGuiApplication(sys.argv)
app.setApplicationName("Coratia ROV Telemetry Monitor")

engine = QQmlApplicationEngine()

# Keep a Python reference alive for the lifetime of the application.
backend = DashboardBackend()

# Register the backend BEFORE loading QML.
engine.rootContext().setContextProperty("dashboardBackend", backend)

qml_file = Path(__file__).parent / "dashboard" / "Main.qml"
engine.load(str(qml_file))

if not engine.rootObjects():
    raise SystemExit("Could not load dashboard QML")

sys.exit(app.exec())
