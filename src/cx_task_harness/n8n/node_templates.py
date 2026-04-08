"""Factory functions that produce n8n node JSON dicts."""

from __future__ import annotations

_DEFAULT_POS = [250, 300]


def _base_node(node_id: str, name: str, node_type: str, type_version: int | float = 1) -> dict:
    return {
        "parameters": {},
        "id": node_id,
        "name": name,
        "type": node_type,
        "typeVersion": type_version,
        "position": list(_DEFAULT_POS),
    }


def make_manual_trigger(node_id: str = "trigger") -> dict:
    return _base_node(node_id, "Manual Trigger", "n8n-nodes-base.manualTrigger")


def make_set_node(node_id: str, name: str, assignments: dict) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.set", type_version=3.3)
    node["parameters"] = {
        "assignments": {
            "assignments": [
                {"id": f"{node_id}_{k}", "name": k, "value": v, "type": "string"}
                for k, v in assignments.items()
            ]
        },
        "options": {},
    }
    return node


def make_code_node(node_id: str, name: str, code: str, language: str) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.code", type_version=2)
    if language == "python":
        node["parameters"] = {"language": "python", "pythonCode": code, "options": {}}
    else:
        node["parameters"] = {"jsCode": code, "options": {}}
    return node


def make_http_request_node(
    node_id: str,
    name: str,
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: dict | None = None,
) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.httpRequest", type_version=4.2)
    node["parameters"] = {
        "url": url,
        "method": method,
        "options": {},
    }
    if headers:
        node["parameters"]["options"]["headers"] = {
            "parameters": [{"name": k, "value": v} for k, v in headers.items()]
        }
    if body:
        node["parameters"]["sendBody"] = True
        node["parameters"]["bodyParameters"] = {
            "parameters": [{"name": k, "value": str(v)} for k, v in body.items()]
        }
    return node


def make_if_node(node_id: str, name: str, conditions: list[dict]) -> dict:
    node = _base_node(node_id, name, "n8n-nodes-base.if", type_version=2)
    n8n_conditions = []
    for cond in conditions:
        n8n_conditions.append({
            "id": f"{node_id}_{cond.get('variable', 'cond')}",
            "leftValue": f"={{{{ $json.{cond.get('variable', 'value')} }}}}",
            "rightValue": cond.get("value", ""),
            "operator": {
                "type": "string",
                "operation": _map_operator(cond.get("operator", "eq")),
            },
        })
    node["parameters"] = {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "typeValidation": "strict",
            },
            "conditions": n8n_conditions,
            "combinator": "and",
        },
        "options": {},
    }
    return node


def make_switch_node(node_id: str, name: str, conditions: list[dict]) -> dict:
    """Creates an n8n Switch node (V3.2) that supports N output branches."""
    node = _base_node(node_id, name, "n8n-nodes-base.switch", type_version=3.2)
    values = []
    for i, cond in enumerate(conditions):
        values.append({
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                },
                "conditions": [
                    {
                        "id": f"{node_id}_rule_{i}",
                        "leftValue": f"={{{{ $json.{cond.get('variable', 'value')} }}}}",
                        "rightValue": cond.get("value", ""),
                        "operator": {
                            "type": "string",
                            "operation": _map_operator(cond.get("operator", "eq")),
                        },
                    }
                ],
                "combinator": "and",
            },
            "outputKey": cond.get("value", f"output_{i}"),
        })
    node["parameters"] = {
        "mode": "rules",
        "rules": {"values": values},
        "options": {"fallbackOutput": "extra"},
    }
    return node


def make_ai_agent_node(node_id: str, name: str, system_message: str) -> dict:
    node = _base_node(node_id, name, "@n8n/n8n-nodes-langchain.agent", type_version=1.6)
    node["parameters"] = {
        "text": "={{ $json.chatInput }}",
        "options": {"systemMessage": system_message},
    }
    return node


def make_mock_response_node(node_id: str, name: str, mock_data: dict) -> dict:
    import json
    code = f"return [{json.dumps({'json': mock_data})}];"
    return make_code_node(node_id, f"[Mock] {name}", code, "javascript")


def _map_operator(op: str) -> str:
    mapping = {
        "eq": "equals",
        "neq": "notEquals",
        "contains": "contains",
        "gt": "gt",
        "lt": "lt",
        "in": "contains",
    }
    return mapping.get(op, "equals")
