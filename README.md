
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/8359b2c0-fe27-4f97-bffb-b1ef89ea1696" />






# ADLP Reference Validator

Reference validator for the Autonomous Defect Language Protocol (ADLP).

## What it does

This tool validates ADLP defect packets against:

- the ADLP registry
- canonical code rules
- severity and action rules
- required metric presence

ADLP Validator CI ✔ PASS

Event Types

ADLP supports the following event types:
	•	FAULT
	•	WARNING
	•	MAINTENANCE
	•	STATE_CHANGE
	•	RECOVERY
canonical_code describes what happened; 
event_type describes what kind of event it is.

## Example

```bash
python -m adlp_validator.cli examples/valid_packet_01.json --registry registry/adlp_registry_v1.1.0.json

## Quick Start

Clone the repository:

git clone https://github.com/<your-user>/adlp-validator-clean
cd adlp-validator-clean

Validate an example ADLP packet:

python -m adlp_validator.cli examples/valid_packet_01.json \
--registry registry/adlp_registry_v1.1.0.json

Generate ADLP mappings from existing device error codes:

python tools/mapping_helper/adlp_mapping_helper_v2.py \
tools/mapping_helper/device_errors_sample.csv \
registry/adlp_registry_v1.1.0.json \
mapping_output.json
