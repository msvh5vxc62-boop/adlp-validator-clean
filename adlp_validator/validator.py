from typing import Any, Dict, List

from adlp_validator.canonical import parse_canonical_code
from adlp_validator.registry_loader import RegistryLoader


def validate_packet(packet: Dict[str, Any], registry: RegistryLoader) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    # Version checks
    if packet.get("registry_version") != registry.get_registry_version():
        errors.append({
            "code": "REGISTRY_VERSION_MISMATCH",
            "path": "registry_version",
            "message": f"Packet registry_version {packet.get('registry_version')} does not match loaded registry {registry.get_registry_version()}"
        })

    if packet.get("adlp_version") != registry.get_protocol_version():
        errors.append({
            "code": "PROTOCOL_VERSION_MISMATCH",
            "path": "adlp_version",
            "message": f"Packet adlp_version {packet.get('adlp_version')} does not match registry protocol_version {registry.get_protocol_version()}"
        })

    event = packet.get("event", {})
    canonical_code = packet.get("canonical_code")

    # Canonical parsing
    try:
        parsed = parse_canonical_code(canonical_code)
    except Exception:
        return {
            "ok": False,
            "validation_id": None,
            "registry_version": registry.get_registry_version(),
            "protocol_version": registry.get_protocol_version(),
            "errors": errors + [{
                "code": "INVALID_CANONICAL_CODE",
                "path": "canonical_code",
                "message": "Canonical code format is invalid"
            }],
            "warnings": warnings
        }

    domain = parsed["domain"]
    system = parsed["system"]
    component = parsed["component"]
    fault_type = parsed["fault_type"]
    severity = parsed["severity"]

    # Registry checks
    if not registry.is_valid_domain(domain):
        errors.append({
            "code": "INVALID_DOMAIN",
            "path": "event.domain",
            "message": f"Domain '{domain}' is not defined in registry {registry.get_registry_version()}"
        })

    if not registry.is_valid_system(domain, system):
        allowed = sorted(list(registry.systems_by_domain.keys()))
        errors.append({
            "code": "INVALID_SYSTEM_FOR_DOMAIN",
            "path": "event.system",
            "message": f"System '{system}' is not valid under domain '{domain}'",
            "allowed_domains": allowed
        })

    if not registry.is_valid_fault_type(fault_type):
        errors.append({
            "code": "INVALID_FAULT_TYPE",
            "path": "event.fault_type",
            "message": f"Fault type '{fault_type}' is not defined in registry {registry.get_registry_version()}"
        })
    elif not registry.is_fault_type_allowed_for_domain(domain, fault_type):
        errors.append({
            "code": "FAULT_TYPE_NOT_ALLOWED_FOR_DOMAIN",
            "path": "event.fault_type",
            "message": f"Fault type '{fault_type}' is not allowed under domain '{domain}'"
        })

    if not registry.is_valid_severity(severity):
        errors.append({
            "code": "INVALID_SEVERITY",
            "path": "event.severity",
            "message": f"Severity '{severity}' is not valid"
        })
    else:
        allowed_severities = registry.severity_guidance_for_fault_type(fault_type)
        if allowed_severities and severity not in allowed_severities:
            errors.append({
                "code": "SEVERITY_NOT_ALLOWED_FOR_FAULT_TYPE",
                "path": "event.severity",
                "message": f"Severity '{severity}' is not allowed for fault type '{fault_type}'"
            })

    # Cross-field consistency
    if event.get("domain") != domain:
        errors.append({
            "code": "DOMAIN_MISMATCH",
            "path": "event.domain",
            "message": f"event.domain '{event.get('domain')}' does not match canonical domain '{domain}'"
        })

    if event.get("system") != system:
        errors.append({
            "code": "SYSTEM_MISMATCH",
            "path": "event.system",
            "message": f"event.system '{event.get('system')}' does not match canonical system '{system}'"
        })

    if event.get("fault_type") != fault_type:
        errors.append({
            "code": "FAULT_TYPE_MISMATCH",
            "path": "event.fault_type",
            "message": f"event.fault_type '{event.get('fault_type')}' does not match canonical fault_type '{fault_type}'"
        })

    if event.get("severity") != severity:
        errors.append({
            "code": "SEVERITY_MISMATCH",
            "path": "event.severity",
            "message": f"event.severity '{event.get('severity')}' does not match canonical severity '{severity}'"
        })

    if component is not None and event.get("component") != component:
        errors.append({
            "code": "COMPONENT_MISMATCH",
            "path": "event.component",
            "message": f"event.component '{event.get('component')}' does not match canonical component '{component}'"
        })

    # Numeric checks
    confidence = event.get("confidence_percent")
    if confidence is not None and not (0 <= confidence <= 100):
        errors.append({
            "code": "INVALID_CONFIDENCE_RANGE",
            "path": "event.confidence_percent",
            "message": "confidence_percent must be between 0 and 100"
        })

    # Action checks
    action = packet.get("action", {})
    recommended_action = action.get("recommended_action")

    if recommended_action and not registry.is_valid_action(recommended_action):
        errors.append({
            "code": "INVALID_ACTION",
            "path": "action.recommended_action",
            "message": f"Action '{recommended_action}' is not defined in the registry"
        })

    allowed_actions = registry.allowed_actions_for_severity(severity)
    if recommended_action and allowed_actions and recommended_action not in allowed_actions:
        errors.append({
            "code": "ACTION_NOT_ALLOWED_FOR_SEVERITY",
            "path": "action.recommended_action",
            "message": f"Action '{recommended_action}' is not allowed for severity '{severity}'"
        })

    if severity == "S4":
        if recommended_action not in {"RETURN_TO_BASE", "CONTROLLED_STOP"}:
            errors.append({
                "code": "INVALID_S4_ACTION",
                "path": "action.recommended_action",
                "message": "S4 requires RETURN_TO_BASE or CONTROLLED_STOP"
            })
        if action.get("safe_state_triggered") is not True:
            errors.append({
                "code": "S4_REQUIRES_SAFE_STATE",
                "path": "action.safe_state_triggered",
                "message": "S4 requires safe_state_triggered = true"
            })

    if severity == "S5":
        if recommended_action != "EMERGENCY_STOP":
            errors.append({
                "code": "INVALID_S5_ACTION",
                "path": "action.recommended_action",
                "message": "S5 requires EMERGENCY_STOP"
            })
        if action.get("safe_state_triggered") is not True:
            errors.append({
                "code": "S5_REQUIRES_SAFE_STATE",
                "path": "action.safe_state_triggered",
                "message": "S5 requires safe_state_triggered = true"
            })

    # Freeze-frame checks
    metrics = packet.get("metrics", {})
    freeze_frame = metrics.get("freeze_frame", {})

    if not isinstance(freeze_frame, dict) or len(freeze_frame) == 0:
        errors.append({
            "code": "EMPTY_FREEZE_FRAME",
            "path": "metrics.freeze_frame",
            "message": "freeze_frame must be a non-empty object"
        })

    required_metrics = registry.required_metrics_for_fault_type(fault_type)
    env = packet.get("context", {}).get("environmental_conditions", {})

    for metric in required_metrics:
        if metric not in freeze_frame and metric not in env:
            errors.append({
                "code": "MISSING_REQUIRED_METRIC",
                "path": "metrics.freeze_frame",
                "message": f"Required metric '{metric}' is missing for fault type '{fault_type}'"
            })

    return {
        "ok": len(errors) == 0,
        "validation_id": None,
        "registry_version": registry.get_registry_version(),
        "protocol_version": registry.get_protocol_version(),
        "errors": errors,
        "warnings": warnings
    }