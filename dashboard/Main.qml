import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 1120
    height: 760
    minimumWidth: 900
    minimumHeight: 650
    title: "Coratia Technologies | ROV Telemetry Monitor"
    color: "#101923"

    property color panel: "#1b2936"
    property color muted: "#9fb0bf"
    property color accent: "#45c4a0"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 2
                Label { text: "ROV TELEMETRY MONITOR"; color: "white"; font.pixelSize: 25; font.bold: true }
                Label { text: "CORATIA TECHNOLOGIES · SIMULATED VEHICLE"; color: muted; font.pixelSize: 11 }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                radius: 8; color: dashboardBackend.quality === "VALID" ? "#174b40" : (dashboardBackend.quality === "STALE" ? "#61451c" : "#512c36")
                implicitWidth: statusText.implicitWidth + 28; implicitHeight: 38
                Label { id: statusText; anchors.centerIn: parent; text: dashboardBackend.connectionStatus + " · " + dashboardBackend.quality; color: "white"; font.bold: true }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 3
            rowSpacing: 12; columnSpacing: 12
            Repeater {
                model: [
                    {name:"BATTERY VOLTAGE", value:dashboardBackend.battery},
                    {name:"DEPTH", value:dashboardBackend.depth},
                    {name:"VEHICLE MODE", value:dashboardBackend.mode},
                    {name:"ROLL", value:dashboardBackend.roll},
                    {name:"PITCH", value:dashboardBackend.pitch},
                    {name:"YAW", value:dashboardBackend.yaw}
                ]
                delegate: Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 105
                    radius: 10; color: panel; border.color: "#2b3c4c"
                    Column {
                        anchors.fill: parent; anchors.margins: 15; spacing: 8
                        Label { text: modelData.name; color: muted; font.pixelSize: 11; font.bold: true }
                        Label { text: modelData.value; color: "white"; font.pixelSize: 25; font.bold: true }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 76; radius: 10; color: panel
                RowLayout {
                    anchors.fill: parent; anchors.margins: 15
                    ColumnLayout {
                        Label { text: "HEARTBEAT"; color: muted; font.pixelSize: 11 }
                        Label { text: dashboardBackend.heartbeat; color: dashboardBackend.heartbeat === "OK" ? accent : "#ff7777"; font.bold: true; font.pixelSize: 18 }
                    }
                    Item { Layout.fillWidth: true }
                    ColumnLayout {
                        Label { text: "SIMULATOR"; color: muted; font.pixelSize: 11 }
                        Label { text: dashboardBackend.running; color: "white"; font.bold: true; font.pixelSize: 18 }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Button { text: "Start stream"; onClicked: dashboardBackend.start() }
            Button { text: "Stop stream"; onClicked: dashboardBackend.stop() }
            ComboBox {
                id: faultPicker
                model: ["No fault", "Malformed JSON", "Missing field", "Low battery", "Sensor out of range", "Heartbeat lost", "Stop telemetry"]
                onActivated: {
                    const faults = ["none", "malformed", "missing", "low_battery", "sensor_range", "heartbeat", "stream_stop"]
                    dashboardBackend.injectFault(faults[currentIndex])
                }
            }
            Button {
                text: "Inject 2 faults"
                onClicked: dashboardBackend.injectMultipleFaults()
            }
            Button {
                text: "Clear fault"
                onClicked: {
                    dashboardBackend.clearFault()
                    faultPicker.currentIndex = 0
                }
            }
            Item { Layout.fillWidth: true }
            Label { text: "Refresh: 2 Hz"; color: muted }
        }

        GridLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            columns: 2; columnSpacing: 12; rowSpacing: 12
            Rectangle {
                Layout.fillWidth: true; Layout.fillHeight: true; radius: 10; color: panel; border.color: "#2b3c4c"
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 15
                    Label { text: "ACTIVE FAULTS"; color: "#ffca70"; font.bold: true; font.pixelSize: 13 }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Label { width: parent.width; text: dashboardBackend.warnings; color: "#ffe1ae"; wrapMode: Text.WordWrap }
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true; Layout.fillHeight: true; radius: 10; color: panel; border.color: "#2b3c4c"
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 15
                    Label { text: "RECENT DIAGNOSTICS"; color: accent; font.bold: true; font.pixelSize: 13 }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        Label { width: parent.width; text: dashboardBackend.diagnostics; color: "#d1dce5"; wrapMode: Text.WordWrap; font.pixelSize: 11 }
                    }
                }
            }
        }
        Label { text: "SIMULATION ONLY · Values are illustrative and are not suitable for vehicle operation."; color: muted; font.pixelSize: 10; Layout.alignment: Qt.AlignHCenter }
    }
}
