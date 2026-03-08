# ADLP Mapping Helper

This tool helps manufacturers map their internal device error codes to ADLP canonical codes.

It reads a CSV list of device errors and suggests ADLP mappings using the official ADLP registry.

The tool does NOT automatically certify mappings. Engineers should review suggestions before using them.

## Usage

Example:

python tools/mapping_helper/adlp_mapping_helper_v2.py \
device_errors.csv \
registry/adlp_registry_v1.1.0.json \
mapping_suggestions.json

## CSV format

Required fields:

internal_code,description

Optional fields:

notes,component,severity_hint

Example:

internal_code,description
E1023,Motor overheat on rear right rotor
E1208,Battery low voltage warning
E1450,GPS signal lost during flight

## Output

The tool generates a JSON file containing:

- suggested ADLP canonical code
- confidence score
- validation against the registry
- status flag

Status values:

REVIEW_REQUIRED  
NO_MATCH  
REGISTRY_CONFLICT

## Recommended workflow

1. Export internal device error list
2. Run the mapping helper
3. Review suggestions
4. Approve mappings
5. Validate ADLP packets with the ADLP validator