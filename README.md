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