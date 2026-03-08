import argparse
import json
import sys
from pathlib import Path

from adlp_validator.registry_loader import RegistryLoader
from adlp_validator.validator import validate_packet
from adlp_validator.report import attach_validation_id


def validate_one_packet(packet_path: Path, registry: RegistryLoader) -> dict:
    with packet_path.open("r", encoding="utf-8") as f:
        packet = json.load(f)

    report = validate_packet(packet, registry)
    report = attach_validation_id(packet, report)
    return report


def print_single_report(report: dict) -> None:
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


def validate_directory(packet_dir: Path, registry: RegistryLoader) -> dict:
    json_files = sorted(packet_dir.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(f"No JSON files found in directory: {packet_dir}")

    results = []
    passed = 0
    failed = 0

    for packet_file in json_files:
        try:
            report = validate_one_packet(packet_file, registry)
            file_result = {
                "file": packet_file.name,
                "ok": report["ok"],
                "validation_id": report.get("validation_id"),
                "errors": report.get("errors", []),
                "warnings": report.get("warnings", []),
            }
            if report["ok"]:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            file_result = {
                "file": packet_file.name,
                "ok": False,
                "validation_id": None,
                "errors": [
                    {
                        "code": "FILE_PROCESSING_ERROR",
                        "path": str(packet_file),
                        "message": str(e),
                    }
                ],
                "warnings": [],
            }
            failed += 1

        results.append(file_result)

    summary = {
        "total": len(json_files),
        "passed": passed,
        "failed": failed,
    }

    return {
        "ok": failed == 0,
        "registry_version": registry.get_registry_version(),
        "protocol_version": registry.get_protocol_version(),
        "summary": summary,
        "results": results,
    }


def print_batch_report(batch_report: dict) -> None:
    print("ADLP BATCH VALIDATION")
    print(f"Registry version: {batch_report['registry_version']}")
    print(f"Protocol version: {batch_report['protocol_version']}")
    print()

    for result in batch_report["results"]:
        if result["ok"]:
            print(f"PASS  {result['file']}  {result.get('validation_id', '-')}")
        else:
            error_codes = ", ".join(
                err.get("code", "UNKNOWN") for err in result.get("errors", [])
            )
            print(f"FAIL  {result['file']}  [{error_codes}]")

    print()
    print("Summary:")
    print(f"Total: {batch_report['summary']['total']}")
    print(f"Pass: {batch_report['summary']['passed']}")
    print(f"Fail: {batch_report['summary']['failed']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="ADLP Reference Validator")
    parser.add_argument(
        "packet",
        help="Path to ADLP packet JSON file OR a directory containing JSON files",
    )
    parser.add_argument("--registry", required=True, help="Path to ADLP registry JSON file")
    parser.add_argument("--json-report", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    packet_path = Path(args.packet)
    registry_path = Path(args.registry)

    if not packet_path.exists():
        print(f"Packet path not found: {packet_path}", file=sys.stderr)
        return 2

    if not registry_path.exists():
        print(f"Registry file not found: {registry_path}", file=sys.stderr)
        return 2

    try:
        registry = RegistryLoader(registry_path).load()
    except Exception as e:
        print(f"Failed to load registry: {e}", file=sys.stderr)
        return 2

    # Single file mode
    if packet_path.is_file():
        try:
            report = validate_one_packet(packet_path, registry)
        except Exception as e:
            print(f"Failed to read packet JSON: {e}", file=sys.stderr)
            return 2

        if args.json_report:
            print(json.dumps(report, indent=2))
        else:
            print_single_report(report)

        return 0 if report["ok"] else 1

    # Directory mode
    if packet_path.is_dir():
        try:
            batch_report = validate_directory(packet_path, registry)
        except Exception as e:
            print(f"Failed to validate directory: {e}", file=sys.stderr)
            return 2

        if args.json_report:
            print(json.dumps(batch_report, indent=2))
        else:
            print_batch_report(batch_report)

        return 0 if batch_report["ok"] else 1

    print(f"Unsupported path type: {packet_path}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())