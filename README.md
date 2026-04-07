# cx-task-harness

An MCP server plugin for Claude Code that validates CX Task Specs and converts them to n8n workflows.

## What it does

1. **Validate** automation task specs against a strict schema
2. **Convert** specs to importable n8n workflow JSON
3. **Browse** industry-specific templates (ecommerce, travel, SaaS, medical)
4. **Guide** the setup of converted workflows

## Quick Start

### Install

```bash
# Add as MCP server to Claude Code
claude mcp add cx-task-harness \
  -- uv run --with fastmcp --with pydantic --with jsonschema \
  fastmcp run src/cx_task_harness/server.py
```

### Copy Claude Code files

Copy the `claude/` directory contents to your project:
- `claude/CLAUDE.md` → your project's `CLAUDE.md` (merge if exists)
- `claude/commands/` → your project's `.claude/commands/`

### Use

In Claude Code:

```
> /analyze path/to/support_logs.csv
> /design "Handle order cancellation for an ecommerce store"
> /guide
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `validate_task_spec` | Validate TaskSpec JSON structure |
| `convert_to_n8n` | Convert TaskSpec → n8n workflow |
| `validate_n8n` | Validate n8n workflow JSON |
| `list_templates` | Browse industry templates |

## Templates

8 templates in English and Korean:

- **ecommerce:** order cancel, exchange/return, delivery tracking, size/stock check
- **travel:** reservation change, reservation cancel
- **saas:** subscription management
- **medical:** appointment change

## Development

```bash
uv sync --dev
uv run python -m pytest -v
```

## License

MIT
