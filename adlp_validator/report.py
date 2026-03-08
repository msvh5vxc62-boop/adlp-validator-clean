import hashlib
import json
from typing import Any, Dict


def attach_validation_id(packet: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
    if not report.get("ok"):
        report["validation_id"] = None
        return report

    payload = {
        "packet": packet,
        "registry_version": report.get("registry_version"),
        "protocol_version": report.get("protocol_version")
    }

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["validation_id"] = hashlib.sha256(raw).hexdigest()[:12].upper()
    return report