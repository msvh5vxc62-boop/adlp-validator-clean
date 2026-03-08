# ADLP Protocol

Autonomous Defect Language Protocol (ADLP) is a standardized format for reporting faults in autonomous systems.

The protocol allows machines to communicate failures in a structured way across:

- drones
- robots
- autonomous vehicles
- industrial systems
- AI agents

## Goals

ADLP defines:

- canonical defect codes
- severity levels
- system domains
- required telemetry metrics
- recommended safe actions

This enables:

- interoperability between manufacturers
- standardized logging
- automated incident analysis
- machine-readable fault diagnostics

## Packet Structure

An ADLP packet contains:

- protocol version
- registry version
- canonical defect code
- event metadata
- freeze-frame telemetry
- recommended actions

Example:

```json
{
  "adlp_version": "1.0",
  "registry_version": "1.1.0",
  "canonical_code": "PROPULSION.MOTOR.OVERHEAT.S3"
}


Event Types

ADLP now supports the following event types:
	•	FAULT
	•	WARNING
	•	MAINTENANCE
	•	STATE_CHANGE
	•	RECOVERY

canonical_code describes what happened; 
event_type describes what kind of event it is.