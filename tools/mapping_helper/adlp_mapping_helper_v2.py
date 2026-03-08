device_errors.csv registry/adlp_registry_v1.1.0.json mapping_suggestions.json
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


KeywordRule = Tuple[List[str], Tuple[str, str, Optional[str], str, str]]


class Registry:
    def __init__(self, registry_path: str | Path):
        self.registry_path = Path(registry_path)
        self.raw: Dict[str, Any] = {}
        self.domains: set[str] = set()
        self.systems_by_domain: Dict[str, set[str]] = {}
        self.fault_types: Dict[str, Dict[str, Any]] = {}
        self.severity_levels: Dict[str, Dict[str, Any]] = {}
        self.actions: set[str] = set()

    def load(self) -> "Registry":
        with self.registry_path.open("r", encoding="utf-8") as f:
            self.raw = json.load(f)

        self.domains = {
            d["name"] for d in self.raw.get("domains", [])
            if d.get("status") == "ACTIVE"
        }

        self.systems_by_domain = {}
        for s in self.raw.get("systems", []):
            if s.get("status") != "ACTIVE":
                continue
            self.systems_by_domain.setdefault(s["domain"], set()).add(s["name"])

        self.fault_types = {
            ft["name"]: ft for ft in self.raw.get("fault_types", [])
            if ft.get("status") == "ACTIVE"
        }

        self.severity_levels = {
            s["name"]: s for s in self.raw.get("severity_levels", [])
        }

        self.actions = set(self.raw.get("actions", []))
        return self

    def is_valid_domain(self, domain: str) -> bool:
        return domain in self.domains

    def is_valid_system(self, domain: str, system: str) -> bool:
        return system in self.systems_by_domain.get(domain, set())

    def is_valid_fault_type(self, fault_type: str) -> bool:
        return fault_type in self.fault_types

    def fault_type_allowed_for_domain(self, domain: str, fault_type: str) -> bool:
        entry = self.fault_types.get(fault_type)
        if not entry:
            return False
        return domain in entry.get("domains_applicable", [])

    def severity_allowed_for_fault_type(self, severity: str, fault_type: str) -> bool:
        entry = self.fault_types.get(fault_type)
        if not entry:
            return False
        return severity in entry.get("severity_guidance", [])

    def registry_version(self) -> str:
        return str(self.raw.get("registry_version", ""))

    def protocol_version(self) -> str:
        return str(self.raw.get("protocol_version", ""))


KEYWORD_RULES: List[KeywordRule] = [
    (["motor", "overheat"], ("PROPULSION", "MOTOR", None, "OVERHEAT", "S3")),
    (["motor", "stall"], ("PROPULSION", "MOTOR", None, "STALL", "S4")),
    (["battery", "low voltage"], ("POWER", "BATTERY", None, "UNDER_VOLT", "S3")),
    (["battery", "overheat"], ("POWER", "BATTERY", None, "OVERHEAT", "S4")),
    (["gps", "signal lost"], ("NAVIGATION", "GNSS", None, "SIGNAL_LOSS", "S2")),
    (["gnss", "signal lost"], ("NAVIGATION", "GNSS", None, "SIGNAL_LOSS", "S2")),
    (["camera", "failure"], ("SENSING", "CAMERA", None, "OUT_OF_RANGE", "S3")),
    (["camera", "signal lost"], ("SENSING", "CAMERA", None, "SIGNAL_LOSS", "S2")),
    (["pressure", "low"], ("PRESSURE", "LINE", None, "UNDER_PRESSURE", "S3")),
    (["pressure", "high"], ("PRESSURE", "LINE", None, "OVER_PRESSURE", "S3")),
    (["water", "level low"], ("FLUID", "TANK", None, "UNDER_LEVEL", "S2")),
    (["tank", "level low"], ("FLUID", "TANK", None, "UNDER_LEVEL", "S2")),
    (["tank", "level high"], ("FLUID", "TANK", None, "OVER_LEVEL", "S2")),
    (["pump", "blocked"], ("FLUID", "PUMP", None, "FLOW_BLOCKED", "S3")),
    (["fan", "failure"], ("THERMAL", "FAN", None, "COOLING_FAILURE", "S3")),
    (["lidar", "signal lost"], ("SENSING", "LIDAR", None, "SIGNAL_LOSS", "S2")),
    (["radar", "signal lost"], ("SENSING", "RADAR", None, "SIGNAL_LOSS", "S2")),
    (["imu", "calibration"], ("NAVIGATION", "IMU", None, "CALIBRATION_FAIL", "S2")),
    (["servo", "stall"], ("ACTUATION", "SERVO", None, "STALL", "S3")),
    (["link", "latency"], ("COMMUNICATION", "LINK", None, "LATENCY_EXCESS", "S2")),
]

SEVERITY_HINT_RE = re.compile(r"^S[1-5]$")


def detect_component(text: str) -> Optional[str]:
    rules = [
        ("right rear", "RIGHT_REAR"),
        ("rear right", "RIGHT_REAR"),
        ("left rear", "LEFT_REAR"),
        ("rear left", "LEFT_REAR"),
        ("right front", "RIGHT_FRONT"),
        ("front right", "RIGHT_FRONT"),
        ("left front", "LEFT_FRONT"),
        ("front left", "LEFT_FRONT"),
        ("primary", "PRIMARY"),
        ("secondary", "SECONDARY"),
    ]
    for phrase, component in rules:
        if phrase in text:
            return component
    return None


def normalize_component(value: str | None) -> Optional[str]:
    if not value:
        return None
    value = value.strip().upper().replace(" ", "_").replace("-", "_")
    return value or None


def build_canonical(domain: str, system: str, component: Optional[str], fault_type: str, severity: str) -> str:
    parts = [domain, system]
    if component:
        parts.append(component)
    parts.extend([fault_type, severity])
    return ".".join(parts)


def validate_suggestion(
    registry: Registry,
    domain: str,
    system: str,
    fault_type: str,
    severity: str,
) -> List[str]:
    issues: List[str] = []

    if not registry.is_valid_domain(domain):
        issues.append(f"Invalid domain: {domain}")
    if not registry.is_valid_system(domain, system):
        issues.append(f"Invalid system '{system}' for domain '{domain}'")
    if not registry.is_valid_fault_type(fault_type):
        issues.append(f"Invalid fault type: {fault_type}")
    elif not registry.fault_type_allowed_for_domain(domain, fault_type):
        issues.append(f"Fault type '{fault_type}' not allowed for domain '{domain}'")
    if severity not in registry.severity_levels:
        issues.append(f"Invalid severity: {severity}")
    elif registry.is_valid_fault_type(fault_type) and not registry.severity_allowed_for_fault_type(severity, fault_type):
        issues.append(f"Severity '{severity}' not allowed for fault type '{fault_type}'")

    return issues


def suggest_mapping(
    registry: Registry,
    internal_code: str,
    description: str,
    notes: str = "",
    component_hint: str = "",
    severity_hint: str = "",
) -> Dict[str, Any]:
    text = f"{description} {notes}".lower().strip()
    component = normalize_component(component_hint) or detect_component(text)
    chosen: Optional[Tuple[str, str, Optional[str], str, str]] = None
    reason = "No keyword rule matched the description"
    confidence = 0.0

    for keywords, mapping in KEYWORD_RULES:
        if all(k in text for k in keywords):
            chosen = mapping
            reason = f"Matched keywords: {', '.join(keywords)}"
            confidence = 0.75
            break

    if chosen is None:
        return {
            "internal_code": internal_code,
            "description": description,
            "notes": notes,
            "domain": None,
            "system": None,
            "component": component,
            "fault_type": None,
            "severity": None,
            "suggested_adlp": None,
            "confidence": confidence,
            "status": "NO_MATCH",
            "reason": reason,
            "registry_validation": [],
        }

    domain, system, _, fault_type, default_severity = chosen

    severity = default_severity
    if severity_hint:
        severity_hint = severity_hint.strip().upper()
        if SEVERITY_HINT_RE.match(severity_hint):
            severity = severity_hint
            confidence = min(confidence + 0.07, 0.95)

    if component:
        confidence = min(confidence + 0.07, 0.95)

    issues = validate_suggestion(registry, domain, system, fault_type, severity)
    status = "REVIEW_REQUIRED" if not issues else "REGISTRY_CONFLICT"

    return {
        "internal_code": internal_code,
        "description": description,
        "notes": notes,
        "domain": domain,
        "system": system,
        "component": component,
        "fault_type": fault_type,
        "severity": severity,
        "suggested_adlp": build_canonical(domain, system, component, fault_type, severity),
        "confidence": round(confidence, 2),
        "status": status,
        "reason": reason,
        "registry_validation": issues,
    }


def run_mapper(input_csv: str, registry_json: str, output_json: str) -> None:
    input_path = Path(input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    registry = Registry(registry_json).load()

    results: List[Dict[str, Any]] = []
    summary = {
        "total_rows": 0,
        "review_required": 0,
        "no_match": 0,
        "registry_conflict": 0,
        "registry_version": registry.registry_version(),
        "protocol_version": registry.protocol_version(),
    }

    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"internal_code", "description"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        for row in reader:
            item = suggest_mapping(
                registry=registry,
                internal_code=(row.get("internal_code") or "").strip(),
                description=(row.get("description") or "").strip(),
                notes=(row.get("notes") or "").strip(),
                component_hint=(row.get("component") or "").strip(),
                severity_hint=(row.get("severity_hint") or "").strip(),
            )
            results.append(item)
            summary["total_rows"] += 1
            if item["status"] == "REVIEW_REQUIRED":
                summary["review_required"] += 1
            elif item["status"] == "NO_MATCH":
                summary["no_match"] += 1
            elif item["status"] == "REGISTRY_CONFLICT":
                summary["registry_conflict"] += 1

    payload = {
        "tool": "ADLP Mapping Helper v2",
        "registry_version": registry.registry_version(),
        "protocol_version": registry.protocol_version(),
        "summary": summary,
        "results": results,
    }

    output_path = Path(output_json)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {summary['total_rows']} mapping suggestions to {output_path}")
    print(
        f"review_required={summary['review_required']} "
        f"no_match={summary['no_match']} "
        f"registry_conflict={summary['registry_conflict']}"
    )


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: python adlp_mapping_helper_v2.py <device_errors.csv> <registry.json> <mapping_suggestions.json>",
            file=sys.stderr,
        )
        return 2

    try:
        run_mapper(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())