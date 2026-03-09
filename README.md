









<p align="center">
Autonomous Defect Language Protocol
</p>

<p align="center">
A universal fault and event reporting protocol for autonomous machines.
</p>

---

# Overview

**ADLP (Autonomous Defect Language Protocol)** standardizes how machines report:

- faults  
- warnings  
- maintenance events  
- state transitions  
- recoveries  

The goal is to create a **common language for machine diagnostics** across:

- robotics  
- drones  
- autonomous vehicles  
- industrial automation  
- aerospace systems  
- IoT devices  

---

# Protocol Components

ADLP consists of four main components:

| Component | Description |
|---|---|
| Registry | Defines domains, systems, and fault types |
| Packet schema | Standard JSON event format |
| Validator | Reference implementation for validating packets |
| Mapping helper | Tool for mapping internal device errors to ADLP |

---

# Event Types

ADLP supports five event types:

```
FAULT
WARNING
MAINTENANCE
STATE_CHANGE
RECOVERY
```

These allow machines to report both **failures and health events**.

---

# Example ADLP Packet

```json
{
  "adlp_version": "1.0",
  "registry_version": "1.5.0",
  "canonical_code": "PROPULSION.MOTOR.OVERHEAT.S3",
  "event": {
    "event_type": "FAULT",
    "domain": "PROPULSION",
    "system": "MOTOR",
    "fault_type": "OVERHEAT",
    "severity": "S3"
  }
}
```

---

# Repository Structure

```
adlp-validator/
│
├─ adlp_validator/
│   ├─ cli.py
│   ├─ validator.py
│   ├─ registry_loader.py
│   └─ report.py
│
├─ registry/
│   └─ adlp_registry_v1.5.0.json
│
├─ examples/
│   ├─ valid/
│   │   └─ valid_packet_01.json
│   └─ invalid/
│       ├─ invalid_packet_01.json
│       └─ invalid_packet_02.json
│
├─ tools/
│   └─ mapping_helper/
│       └─ adlp_mapping_helper.py
│
└─ README.md
```

---

# Validator

The ADLP Reference Validator verifies that packets conform to:

- the packet schema  
- registry vocabulary  
- severity rules  
- protocol constraints  

---

# CLI Usage

Validate a single packet:

```bash
python -m adlp_validator.cli examples/valid/valid_packet_01.json \
  --registry registry/adlp_registry_v1.5.0.json
```

Validate multiple packets (directory mode):

```bash
python -m adlp_validator.cli examples/valid \
  --registry registry/adlp_registry_v1.5.0.json
```

Generate JSON validation reports:

```bash
python -m adlp_validator.cli examples/valid \
  --registry registry/adlp_registry_v1.5.0.json \
  --json-report
```

---

# Example CLI Output

```
ADLP BATCH VALIDATION

PASS  valid_packet_01.json

Summary:
Total: 1
Pass: 1
Fail: 0
```

The CLI validator supports:

- single packet validation  
- batch directory validation  
- JSON validation reports  

---

# Continuous Integration

The repository includes a CI pipeline that:

1. Validates example packets  
2. Confirms valid packets pass  
3. Confirms invalid packets fail  
4. Generates downloadable validation reports  

---

# Mapping Helper

Existing devices can adopt ADLP without firmware changes.

The **mapping helper** assists manufacturers in mapping internal error codes to ADLP canonical codes.

Example:

```
E1023 -> PROPULSION.MOTOR.OVERHEAT.S3
```

---

# Versioning

| Component | Version |
|---|---|
| Protocol | 1.0 |
| Registry | 1.5.0 |

Packets must declare both versions for compatibility.

---

# Goals of ADLP

ADLP aims to provide:

- cross-vendor fault interoperability  
- standardized diagnostics  
- improved telemetry analysis  
- easier fleet monitoring  
- compatibility across robotics ecosystems  

---

# License

Open protocol specification.

---

# Trademark

**ADLP™** is a trademark of the protocol author.

Registration with the Canadian Intellectual Property Office (CIPO) is pending.
