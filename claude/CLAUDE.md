# CX Task Harness — Workflow Guide

## MCP Tools Available

- `validate_task_spec` — Validate a TaskSpec JSON (run after generating)
- `convert_to_n8n` — Convert TaskSpec to n8n workflow JSON
- `validate_n8n` — Validate n8n workflow JSON against schema
- `list_templates` — Browse industry task templates

## Pipeline Rules

1. Always **validate** a TaskSpec before converting to n8n
2. Always **validate** the n8n output after conversion
3. Use `list_templates` to check for existing templates before designing from scratch
4. When using `/design`, auto-fix and re-validate if validation fails

## TaskSpec Authoring Guidelines

- All step IDs must be unique and use snake_case (e.g., `check_order_status`)
- AgentStep must have at least one `exit_conditions` entry
- FunctionStep and CodeStep should have `on_failure` set
- Memory variables: only declare what is actually used in steps
- Avoid circular step references

## Supported Industries

ecommerce, travel, saas, medical — run `list_templates` for full catalog
