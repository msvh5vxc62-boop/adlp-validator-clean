# ADLP Mapping Helper


Registry-assisted helper tool that suggests ADLP mappings from existing device error descriptions.

## What v2 adds

- explicit rule matching for common high-confidence cases
- registry-assisted fallback matching when no rule matches
- ranked alternative suggestions
- validation against the active ADLP registry

## Usage

```bash
python adlp_mapping_helper_v3.py device_errors.csv registry/adlp_registry_v1.1.0.json mapping_suggestions.json
```

## Input CSV

Required columns:

```csv
internal_code,description
```

Optional columns:

```csv
notes,component,severity_hint
```

## Output

The output JSON contains:
- `primary_suggestion`
- `alternative_suggestions`
- `summary`
- registry and protocol version info