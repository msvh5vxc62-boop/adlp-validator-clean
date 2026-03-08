<device_errors.csv> <registry.json> <mapping_suggestions.json>
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

KeywordRule = Tuple[List[str], Tuple[str, str, Optional[str], str, str]]

KEYWORD_RULES: List[KeywordRule] = [
    (["motor", "overheat"], ("PROPULSION", "MOTOR", None, "OVERHEAT", "S3")),
    (["motor", "stall"], ("PROPULSION", "MOTOR", None, "STALL", "S4")),
    (["battery", "low voltage"], ("POWER", "BATTERY", None, "UNDER_VOLT", "S3")),
    (["battery", "overheat"], ("POWER", "BATTERY", None, "OVERHEAT", "S4")),
    (["gps", "signal lost"], ("NAVIGATION", "GNSS", None, "SIGNAL_LOSS", "S2")),
    (["gnss", "signal lost"], ("NAVIGATION", "GNSS", None, "SIGNAL_LOSS", "S2")),
    (["camera", "failure"], ("SENSING", "CAMERA", None, "OUT_OF_RANGE", "S3")),
    (["pressure", "low"], ("PRESSURE", "LINE", None, "UNDER_PRESSURE", "S3")),
    (["pressure", "high"], ("PRESSURE", "LINE", None, "OVER_PRESSURE", "S3")),
    (["water", "level low"], ("FLUID", "TANK", None, "UNDER_LEVEL", "S2")),
    (["pump", "blocked"], ("FLUID", "PUMP", None, "FLOW_BLOCKED", "S3")),
    (["fan", "failure"], ("THERMAL", "FAN", None, "COOLING_FAILURE", "S3")),
    (["lidar", "signal lost"], ("SENSING", "LIDAR", None, "SIGNAL_LOSS", "S2")),
    (["imu", "calibration"], ("NAVIGATION", "IMU", None, "CALIBRATION_FAIL", "S2")),
    (["servo", "stall"], ("ACTUATION", "SERVO", None, "STALL", "S3")),
]

SEVERITY_HINT_RE = re.compile(r"^S[1-5]$")
TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalized_terms(text: str) -> set[str]:
    text = text.lower().replace("_", " ").replace("-", " ")
    terms = set(TOKEN_RE.findall(text))
    phrase = "_".join(TOKEN_RE.findall(text))
    if phrase:
        terms.add(phrase)
    return terms


class Registry:
    def __init__(self, registry_path: str | Path):
        self.registry_path = Path(registry_path)
        self.raw: Dict[str, Any] = {}
        self.domains: set[str] = set()
        self.systems_by_domain: Dict[str, set[str]] = {}
        self.fault_types: Dict[str, Dict[str, Any]] = {}
        self.severity_levels: Dict[str, Dict[str, Any]] = {}
        self.domain_terms: Dict[str, set[str]] = {}
        self.system_terms: Dict[tuple[str, str], set[str]] = {}
        self.fault_terms: Dict[str, set[str]] = {}

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

        self.domain_terms = {d: normalized_terms(d) for d in self.domains}
        self.system_terms = {
            (domain, system): normalized_terms(system)
            for domain, systems in self.systems_by_domain.items()
            for system in systems
        }
        self.fault_terms = {
            fault_type: normalized_terms(fault_type)
            for fault_type in self.fault_types
        }
        return self

    def fault_type_allowed_for_domain(self, domain: str, fault_type: str) -> bool:
        entry = self.fault_types.get(fault_type)
        return bool(entry and domain in entry.get("domains_applicable", []))

    def severity_allowed_for_fault_type(self, severity: str, fault_type: str) -> bool:
        entry = self.fault_types.get(fault_type)
        return bool(entry and severity in entry.get("severity_guidance", []))

    def registry_version(self) -> str:
        return str(self.raw.get("registry_version", ""))

    def protocol_version(self) -> str:
        return str(self.raw.get("protocol_version", ""))


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


def validate_suggestion(registry: Registry, domain: str, system: str, fault_type: str, severity: str) -> List[str]:
    issues: List[str] = []
    if domain not in registry.domains:
        issues.append(f"Invalid domain: {domain}")
    if system not in registry.systems_by_domain.get(domain, set()):
        issues.append(f"Invalid system '{system}' for domain '{domain}'")
    if fault_type not in registry.fault_types:
        issues.append(f"Invalid fault type: {fault_type}")
    elif not registry.fault_type_allowed_for_domain(domain, fault_type):
        issues.append(f"Fault type '{fault_type}' not allowed for domain '{domain}'")
    if severity not in registry.severity_levels:
        issues.append(f"Invalid severity: {severity}")
    elif fault_type in registry.fault_types and not registry.severity_allowed_for_fault_type(severity, fault_type):
        issues.append(f"Severity '{severity}' not allowed for fault type '{fault_type}'")
    return issues


def choose_severity(registry: Registry, fault_type: str, severity_hint: str, default: str = "S2") -> str:
    allowed = registry.fault_types.get(fault_type, {}).get("severity_guidance", [])
    if severity_hint and SEVERITY_HINT_RE.match(severity_hint) and severity_hint in allowed:
        return severity_hint
    if default in allowed:
        return default
    return allowed[0] if allowed else "S2"


def score_overlap(text_terms: set[str], candidate_terms: set[str]) -> float:
    return float(len(text_terms & candidate_terms))


def registry_assisted_candidates(registry: Registry, description: str, notes: str, component: Optional[str], severity_hint: str, top_n: int = 3) -> List[Dict[str, Any]]:
    text_terms = normalized_terms(f"{description} {notes}")
    candidates: List[Dict[str, Any]] = []

    for domain in sorted(registry.domains):
        domain_score = score_overlap(text_terms, registry.domain_terms.get(domain, set()))
        for system in sorted(registry.systems_by_domain.get(domain, set())):
            system_score = score_overlap(text_terms, registry.system_terms.get((domain, system), set()))
            for fault_type in sorted(registry.fault_types.keys()):
                if not registry.fault_type_allowed_for_domain(domain, fault_type):
                    continue
                fault_score = score_overlap(text_terms, registry.fault_terms.get(fault_type, set()))
                total = domain_score * 1.0 + system_score * 1.6 + fault_score * 2.0
                if total <= 0:
                    continue
                severity = choose_severity(registry, fault_type, severity_hint.strip().upper())
                issues = validate_suggestion(registry, domain, system, fault_type, severity)
                status = "REVIEW_REQUIRED" if not issues else "REGISTRY_CONFLICT"
                candidates.append({
                    "domain": domain,
                    "system": system,
                    "component": component,
                    "fault_type": fault_type,
                    "severity": severity,
                    "suggested_adlp": build_canonical(domain, system, component, fault_type, severity),
                    "confidence": round(min(0.35 + total * 0.08 + (0.05 if component else 0), 0.79), 2),
                    "status": status,
                    "reason": f"Registry-assisted match score={total:.2f}",
                    "registry_validation": issues,
                    "_score": total,
                })

    candidates.sort(key=lambda x: (-x["_score"], -x["confidence"], x["suggested_adlp"]))
    out: List[Dict[str, Any]] = []
    seen = set()
    for item in candidates:
        if item["suggested_adlp"] in seen:
            continue
        seen.add(item["suggested_adlp"])
        item = dict(item)
        item.pop("_score", None)
        out.append(item)
        if len(out) >= top_n:
            break
    return out


def suggest_mapping(registry: Registry, internal_code: str, description: str, notes: str = "", component_hint: str = "", severity_hint: str = "") -> Dict[str, Any]:
    text = f"{description} {notes}".lower().strip()
    component = normalize_component(component_hint) or detect_component(text)

    for keywords, mapping in KEYWORD_RULES:
        if all(k in text for k in keywords):
            domain, system, _, fault_type, default_severity = mapping
            severity = choose_severity(registry, fault_type, severity_hint.strip().upper(), default_severity)
            issues = validate_suggestion(registry, domain, system, fault_type, severity)
            primary = {
                "domain": domain,
                "system": system,
                "component": component,
                "fault_type": fault_type,
                "severity": severity,
                "suggested_adlp": build_canonical(domain, system, component, fault_type, severity),
                "confidence": round(min((0.82 if component else 0.75) + (0.05 if severity_hint else 0), 0.92), 2),
                "status": "REVIEW_REQUIRED" if not issues else "REGISTRY_CONFLICT",
                "reason": f"Matched explicit rule: {', '.join(keywords)}",
                "registry_validation": issues,
            }
            alternatives = [c for c in registry_assisted_candidates(registry, description, notes, component, severity_hint, 2) if c["suggested_adlp"] != primary["suggested_adlp"]]
            return {
                "internal_code": internal_code,
                "description": description,
                "notes": notes,
                "primary_suggestion": primary,
                "alternative_suggestions": alternatives,
            }

    candidates = registry_assisted_candidates(registry, description, notes, component, severity_hint, 3)
    if not candidates:
        return {
            "internal_code": internal_code,
            "description": description,
            "notes": notes,
            "primary_suggestion": {
                "domain": None,
                "system": None,
                "component": component,
                "fault_type": None,
                "severity": None,
                "suggested_adlp": None,
                "confidence": 0.0,
                "status": "NO_MATCH",
                "reason": "No explicit rule or registry-assisted candidate matched",
                "registry_validation": [],
            },
            "alternative_suggestions": [],
        }

    return {
        "internal_code": internal_code,
        "description": description,
        "notes": notes,
        "primary_suggestion": candidates[0],
        "alternative_suggestions": candidates[1:],
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
            status = item["primary_suggestion"]["status"]
            if status == "REVIEW_REQUIRED":
                summary["review_required"] += 1
            elif status == "NO_MATCH":
                summary["no_match"] += 1
            elif status == "REGISTRY_CONFLICT":
                summary["registry_conflict"] += 1

    payload = {
        "tool": "ADLP Mapping Helper v3",
        "registry_version": registry.registry_version(),
        "protocol_version": registry.protocol_version(),
        "summary": summary,
        "results": results,
    }

    with Path(output_json).open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {summary['total_rows']} mapping suggestions to {output_json}")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python adlp_mapping_helper_v3.py <device_errors.csv> <registry.json> <mapping_suggestions.json>", file=sys.stderr)
        return 2
    try:
        run_mapper(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
