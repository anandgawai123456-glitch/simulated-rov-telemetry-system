# Read-only ArduPilot SITL / MAVLink integration proposal

The simulator is deliberately isolated behind the telemetry-processing interface. A future adapter can receive MAVLink packets (for example through pymavlink) and map them into the same normalized JSON/dictionary schema. The adapter must be read-only: it should not send arm, mode, movement, or actuator commands.

| Normalized field | MAVLink source | Mapping / assumptions |
|---|---|---|
| heartbeat_status, vehicle_mode | `HEARTBEAT` | Heartbeat reception establishes source liveness. Decode `base_mode` and `custom_mode` using the ArduSub firmware mode mapping. A missing heartbeat over the configured timeout is stale/disconnected. |
| roll_deg, pitch_deg, yaw_deg | `ATTITUDE` | `roll`, `pitch`, `yaw` are radians; convert with `math.degrees`. `ATTITUDE` is normally streamed by the autopilot. |
| battery_voltage_v | `SYS_STATUS` or `BATTERY_STATUS` | `SYS_STATUS.voltage_battery` is millivolts; `BATTERY_STATUS.voltages[]` entries are millivolts. Handle unknown sentinel values and multi-battery selection explicitly. |
| depth_m | `SCALED_PRESSURE2` (or configured pressure sensor message) | `depth` is not universally provided as a standard MAVLink vehicle-depth field. For ArduSub, confirm the firmware/sensor setup and message stream. Convert pressure to depth using a documented reference pressure and water density, or consume a firmware-specific depth estimate if one is available and verified. |
| timestamp | packet time / receive time | Prefer source boot-time where available; otherwise timestamp packet receipt in UTC and document that it is receive time, not sensor acquisition time. |

## Integration safeguards

- Use a configured UDP endpoint connected to ArduPilot SITL only; no physical controller endpoint is supported by this assessment build.
- Subscribe only to telemetry messages. Do not call command, parameter-write, arming, or mission-upload APIs.
- Validate packet age, message availability, units, sentinel values, and vehicle system/component IDs before updating the common state model.
- Confirm the actual ArduSub firmware version, pressure/depth sensor configuration, message rates, and mode mapping before treating depth or mode as authoritative.
- Keep the current simulator adapter as the default source so automated tests and demonstrations remain deterministic and hardware-free.
