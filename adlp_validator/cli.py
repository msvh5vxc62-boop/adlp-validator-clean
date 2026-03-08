import argparse
import json
import sys
from pathlib import Path

from adlp_validator.registry_loader import RegistryLoader
from adlp_validator.validator import validate_packet
from adlp_validator.report import attach_validation_id


def main() -> int:
    parser = argparse.ArgumentParser(description="ADLP Reference Validator")
    parser.add_argument("packet", help="Path to ADLP packet JSON file")
    parser.add_argument("--registry", required=True, help="Path to ADLP registry JSON file")
    parser.add_argument("--json-report", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    packet_path = Path(args.packet)
    registry_path = Path(args.registry)

    if not packet_path.exists():
        print(f"Packet file not found: {packet_path}", file=sys.stderr)
        return 2

    if not registry_path.exists():
        print(f"Registry file not found: {registry_path}", file=sys.stderr)
        return 2

    try:
        with packet_path.open("r", encoding="utf-8") as f:
            packet = json.load(f)
    except Exception as e:
        print(f"Failed to read packet JSON: {e}", file=sys.stderr)
        return 2

    try:
        registry = RegistryLoader(registry_path).load()
    except Exception as e:
        print(f"Failed to load registry: {e}", file=sys.stderr)
        return 2

    report = validate_packet(packet, registry)
    report = attach_validation_id(packet, report)

    if args.json_report:
        print(json.dumps(report, indent=2))
    else:
        if report["ok"]:
            print("ADLP VALIDATION: PASS")
            print(f"Validation ID: {report['validation_id']}")
            print(f"Registry version: {report['registry_version']}")
            print(f"Protocol version: {report['protocol_version']}")
        else:
            print("ADLP VALIDATION: FAIL")
            print(f"Registry version: {report['registry_version']}")
            print(f"Protocol version: {report['protocol_version']}")
            for err in report["errors"]:
                code = err.get("code", "UNKNOWN")
                path = err.get("path", "-")
                msg = err.get("message", "")
                print(f"[{code}] {path}: {msg}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())