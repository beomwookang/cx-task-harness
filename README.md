<p align="center">
  <h1 align="center">CX Task Harness</h1>
  <p align="center">
    <strong>Customer Support Automation Architect — A Claude Code Plugin</strong>
  </p>
  <p align="center">
    <a href="#installation">Install</a> &middot;
    <a href="#how-it-works">How It Works</a> &middot;
    <a href="#use-cases">Use Cases</a> &middot;
    <a href="#templates">Templates</a> &middot;
    <a href="docs/TASK_SPEC.md">Spec Reference</a>
  </p>
  <p align="center">
    <a href="README.md">English</a> | <a href="README.ko.md">한국어</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet" alt="Claude Code Plugin" />
  <img src="https://img.shields.io/badge/python-3.11+-yellow" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/n8n-1.x-orange" alt="n8n 1.x" />
</p>

---

> **Turn customer support conversations into working automation workflows.**
>
> CX Task Harness analyzes your support data, designs structured automation specs, and converts them into importable n8n workflows — all from Claude Code.

---

## The Problem

Customer support teams handle thousands of repetitive inquiries daily — order cancellations, delivery tracking, reservation changes. AI agents can automate these, but the bottleneck is **designing the automation**:

- Which inquiries _should_ be automated?
- What should the conversation flow look like?
- What APIs need to be called, and when?
- How should the agent branch based on conditions?

**CX Task Harness automates the design process itself.**

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   1. ANALYZE          2. DESIGN           3. CONVERT             │
│                                                                  │
│   Support Logs   ──>  CX Task Spec   ──>  n8n Workflow           │
│   (CSV/JSON)          (Structured)        (Importable)           │
│                                                                  │
│   "What can be        "How should it      "Make it               │
│    automated?"         work?"              runnable"              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
            4. VALIDATE              5. GUIDE
                  │                       │
            Structural checks       Setup report for
            before conversion       manual config items
```

| Phase | What Happens | Powered By |
|-------|-------------|------------|
| **Analyze** | Cluster support logs by intent, score automation potential | Claude Code (LLM) |
| **Design** | Generate structured CX Task Spec from scenario | Claude Code (LLM) |
| **Validate** | Check references, circular deps, branch targets | MCP Tool (deterministic) |
| **Convert** | Transform spec into importable n8n workflow JSON | MCP Tool (deterministic) |
| **Guide** | Generate setup instructions for manual config items | Claude Code (LLM) |

### Why Hybrid?

LLM-driven tasks (analysis, design) stay in Claude Code where prompts can be iterated instantly. Deterministic tasks (validation, conversion) run in the MCP server where Python guarantees correctness. Best of both worlds.

## Key Features

**Structured Task Specs** — Platform-agnostic JSON schema with 7 step types (agent, code, message, action, function, branch, browser), Pydantic-validated with discriminated unions

**Smart Validation** — Catches broken references, circular dependencies, unreachable steps, missing error handlers — before you waste time on conversion

**n8n Workflow Generation** — Produces importable n8n JSON with auto-positioned nodes, proper connections, and Switch nodes for multi-branch routing

**Mock Data Mode** — Inserts mock response nodes so you can test the entire flow without configuring external APIs

**Industry Templates** — 8 pre-built templates across 4 industries, in English and Korean

**Setup Guides** — Automatically identifies which nodes need manual configuration and generates step-by-step instructions

## Installation

### As Claude Code MCP Plugin

```bash
# Install via MCP
claude mcp add cx-task-harness \
  -- uv run --with fastmcp --with pydantic --with jsonschema \
  fastmcp run src/cx_task_harness/server.py
```

### Slash Commands (Optional)

Copy the slash commands to your project for guided workflows:

```bash
# From the cx-task-harness directory
cp claude/CLAUDE.md your-project/CLAUDE.md        # or merge with existing
cp -r claude/commands/ your-project/.claude/commands/
```

This gives you three commands in Claude Code:

| Command | Description |
|---------|-------------|
| `/analyze` | Analyze support logs and identify automation opportunities |
| `/design` | Design a CX Task Spec from a natural language scenario |
| `/guide` | Generate an n8n workflow setup guide |

### From Source

```bash
git clone https://github.com/your-username/cx-task-harness.git
cd cx-task-harness
uv sync --dev
uv run python -m pytest -v  # 88 tests
```

## Use Cases

### "I have support chat logs and want to know what to automate"

```
> /analyze support_logs.csv

Found 452 conversations with 3 automatable patterns:
  1. Order cancellation (127 conversations, score: 0.92)
  2. Delivery tracking (98 conversations, score: 0.88)
  3. Size exchange (67 conversations, score: 0.75)
Estimated automation rate: 64%
```

### "Design an order cancellation workflow"

```
> /design "Handle order cancellation for an ecommerce store.
>  Check if the order can be cancelled, process the refund,
>  and escalate to human if already shipped."

Generated TaskSpec with 9 steps:
  agent → function → branch → function → message → action
  Validated: 0 errors, 0 warnings
```

### "Convert it to n8n and tell me what to configure"

```
> Convert the order cancellation spec to n8n

Generated n8n workflow with 14 nodes
  Setup required for 2 nodes:
  - "Check Order Status" → API endpoint + auth
  - "Execute Cancellation" → API endpoint + auth

> /guide

Setup Guide:
  Ready to run: 12 nodes (with mock data)
  Manual setup: 2 HTTP Request nodes
  [detailed step-by-step instructions...]
```

### "I need this in Korean"

```
> list_templates(industry="ecommerce", locale="ko")

Templates:
  - ecommerce/order_cancel — 주문 취소 및 환불
  - ecommerce/exchange_return — 교환 및 반품 처리
  - ecommerce/delivery_tracking — 배송 조회
  - ecommerce/size_stock_check — 사이즈 및 재고 확인
```

## MCP Tools

| Tool | Input | Output | Purpose |
|------|-------|--------|---------|
| `validate_task_spec` | TaskSpec JSON | `{valid, errors, warnings}` | Structural validation |
| `convert_to_n8n` | TaskSpec JSON | `{workflow, setup_required}` | n8n workflow generation |
| `validate_n8n` | n8n workflow JSON | `{valid, errors, n8n_version}` | n8n schema validation |
| `list_templates` | industry?, locale? | `{templates: [...]}` | Browse industry templates |

## Templates

8 production-ready templates in **English** and **Korean**:

| Industry | Template | Steps | Description |
|----------|----------|-------|-------------|
| **ecommerce** | `order_cancel` | 9 | Order cancellation & refund |
| **ecommerce** | `exchange_return` | 8 | Exchange & return processing |
| **ecommerce** | `delivery_tracking` | 7 | Delivery status inquiry |
| **ecommerce** | `size_stock_check` | 6 | Size & stock availability |
| **travel** | `reservation_change` | 8 | Reservation modification |
| **travel** | `reservation_cancel` | 8 | Reservation cancellation |
| **saas** | `subscription_manage` | 8 | Subscription change & cancellation |
| **medical** | `appointment_change` | 7 | Appointment rescheduling |

Each template includes: trigger conditions, agent instructions with exit conditions, API call steps with error handling, conditional branching, and automation potential scoring.

## CX Task Spec

The CX Task Spec is a **platform-agnostic JSON schema** for describing customer support automation tasks. It's designed to be convertible to any agent platform's native format.

### Step Types

| Type | Purpose | n8n Mapping |
|------|---------|-------------|
| `agent` | LLM-driven conversation with structured instructions | AI Agent (LangChain) |
| `code` | Programmatic logic (JavaScript/Python) | Code Node |
| `message` | Fixed message delivery | Set Node |
| `action` | Internal operations (assign team, set tags, close) | Set Node |
| `function` | External API call | HTTP Request Node |
| `branch` | Conditional routing with N conditions | Switch Node |
| `browser` | Web automation | HTTP Request (placeholder) |

See [TASK_SPEC.md](docs/TASK_SPEC.md) for the full schema reference.

## Architecture

```
cx-task-harness/
├── src/cx_task_harness/
│   ├── server.py              # FastMCP server entrypoint
│   ├── models/                # Pydantic v2 models (Discriminated Union)
│   │   ├── common.py          # Trigger, AgentInstruction, BranchCondition
│   │   ├── steps.py           # 7 step types + Step union
│   │   └── task_spec.py       # TaskSpec top-level model
│   ├── tools/                 # MCP tool implementations
│   │   ├── validator.py       # Reference checks, cycle detection
│   │   ├── converter.py       # TaskSpec → n8n orchestrator
│   │   ├── n8n_validator.py   # JSON Schema validation
│   │   └── templates.py       # Template listing & loading
│   ├── n8n/                   # n8n conversion internals
│   │   ├── mapper.py          # Step → node mapping
│   │   ├── layout.py          # Auto-placement algorithm
│   │   └── node_templates.py  # Node JSON factories
│   └── templates/             # 16 industry template files
│       ├── ecommerce/         # 4 templates × 2 locales
│       ├── travel/            # 2 templates × 2 locales
│       ├── saas/              # 1 template × 2 locales
│       └── medical/           # 1 template × 2 locales
│
├── claude/                    # Claude Code integration
│   ├── CLAUDE.md              # Workflow guide
│   └── commands/              # /analyze, /design, /guide
│
└── tests/                     # 88 tests (unit + integration + e2e)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| MCP Server | [FastMCP](https://github.com/jlowin/fastmcp) (Python) |
| Schema Validation | [Pydantic v2](https://docs.pydantic.dev/) (Discriminated Union) |
| n8n Validation | [jsonschema](https://python-jsonschema.readthedocs.io/) |
| Package Management | [uv](https://docs.astral.sh/uv/) |
| Testing | pytest + syrupy (snapshot tests) |

## Roadmap

- [ ] `cx-task-harness init` CLI for automated project setup
- [ ] Multi-version n8n schema support
- [ ] Community template contribution system
- [ ] Additional platform adapters (beyond n8n)
- [ ] Template marketplace

## Contributing

Contributions welcome! Templates for new industries are especially appreciated.

```bash
# Run tests
uv sync --dev
uv run python -m pytest -v

# Add a new template
# 1. Create src/cx_task_harness/templates/{industry}/{name}.en.json
# 2. Create the .ko.json version
# 3. Run tests — they auto-discover and validate all templates
```

## License

[MIT](LICENSE) — Use freely in personal and commercial projects.
