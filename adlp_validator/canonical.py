import re
from typing import Optional, Dict

CANONICAL_RE = re.compile(
    r"^(?P<domain>[A-Z0-9_]+)\.(?P<system>[A-Z0-9_]+)(?:\.(?P<component>[A-Z0-9_]+))?\.(?P<fault_type>[A-Z0-9_]+)\.(?P<severity>S[1-5])$"
)

def parse_canonical_code(code: str) -> Dict[str, Optional[str]]:
    match = CANONICAL_RE.match(code)
    if not match:
        raise ValueError("Invalid canonical code format")
    return {
        "domain": match.group("domain"),
        "system": match.group("system"),
        "component": match.group("component"),
        "fault_type": match.group("fault_type"),
        "severity": match.group("severity"),
    }