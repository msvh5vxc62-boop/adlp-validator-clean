# ADLP Packet Format

An ADLP packet describes a detected system fault.

## Required fields

## Event object

The `event` object contains the structured classification of the machine event.

Required fields inside `event`:

| Field | Description |
|---|---|
| event_type | Type of event (`FAULT`, `WARNING`, `MAINTENANCE`, `STATE_CHANGE`, `RECOVERY`) |
| domain | High-level subsystem category |
| system | Specific system within the domain |
| fault_type | Specific failure or condition |
| severity | Standardized severity level |
| component | Optional subcomponent identifier |
| confidence_percent | Optional confidence score |

## Example packet

```json
{
  "adlp_version": "1.0",
  "registry_version": "1.1.0",
  "canonical_code": "PROPULSION.MOTOR.OVERHEAT.S3",
  "event": {
    "event_type": "FAULT",
    "domain": "PROPULSION",
    "system": "MOTOR",
    "fault_type": "OVERHEAT",
    "severity": "S3"
  }
}