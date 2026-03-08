# ADLP Reference Validator

Reference validator for the Autonomous Defect Language Protocol (ADLP).

## What it does

This tool validates ADLP defect packets against:

- the ADLP registry
- canonical code rules
- severity and action rules
- required metric presence

## Example

```bash
python -m adlp_validator.cli examples/valid_packet_01.json --registry registry/adlp_registry_v1.1.0.json
