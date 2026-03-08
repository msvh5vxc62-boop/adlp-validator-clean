# ADLP Packet Format

An ADLP packet describes a detected system fault.

## Required fields

| Field | Description |
|-----|-----|
| adlp_version | Protocol version |
| registry_version | Registry version |
| canonical_code | Structured fault identifier |
| event | Fault metadata |
| metrics | Freeze frame telemetry |
| action | Recommended mitigation |

## Example packet

```json
{
  "adlp_version": "1.0",
  "registry_version": "1.1.0",
  "canonical_code": "PROPULSION.MOTOR.OVERHEAT.S3",
  "event": {
    "domain": "PROPULSION",
    "system": "MOTOR",
    "fault_type": "OVERHEAT",
    "severity": "S3"
  }
}