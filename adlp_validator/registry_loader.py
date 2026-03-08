import json
from pathlib import Path
from typing import Any, Dict, Set

class RegistryLoader:
    def __init__(self, registry_path: str | Path):
        self.registry_path = Path(registry_path)
        self.raw: Dict[str, Any] = {}
        self.domains: Set[str] = set()
        self.systems_by_domain: Dict[str, Set[str]] = {}
        self.fault_types: Dict[str, Dict[str, Any]] = {}
        self.severity_levels: Dict[str, Dict[str, Any]] = {}
        self.actions: Set[str] = set()

    def load(self) -> "RegistryLoader":
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
            domain = s["domain"]
            name = s["name"]
            self.systems_by_domain.setdefault(domain, set()).add(name)

        self.fault_types = {
            f["name"]: f for f in self.raw.get("fault_types", [])
            if f.get("status") == "ACTIVE"
        }

        self.severity_levels = {
            s["name"]: s for s in self.raw.get("severity_levels", [])
        }

        self.actions = set(self.raw.get("actions", []))
        return self

    def get_registry_version(self) -> str:
        return self.raw.get("registry_version", "")

    def get_protocol_version(self) -> str:
        return self.raw.get("protocol_version", "")

    def is_valid_domain(self, domain: str) -> bool:
        return domain in self.domains

    def is_valid_system(self, domain: str, system: str) -> bool:
        return system in self.systems_by_domain.get(domain, set())

    def is_valid_fault_type(self, fault_type: str) -> bool:
        return fault_type in self.fault_types

    def is_fault_type_allowed_for_domain(self, domain: str, fault_type: str) -> bool:
        ft = self.fault_types.get(fault_type)
        if not ft:
            return False
        return domain in ft.get("domains_applicable", [])

    def is_valid_severity(self, severity: str) -> bool:
        return severity in self.severity_levels

    def is_valid_action(self, action: str) -> bool:
        return action in self.actions

    def allowed_actions_for_severity(self, severity: str) -> set[str]:
        level = self.severity_levels.get(severity, {})
        return set(level.get("allowed_actions", []))

    def required_metrics_for_fault_type(self, fault_type: str) -> list[str]:
        ft = self.fault_types.get(fault_type, {})
        return list(ft.get("required_metrics", []))

    def severity_guidance_for_fault_type(self, fault_type: str) -> list[str]:
        ft = self.fault_types.get(fault_type, {})
        return list(ft.get("severity_guidance", []))