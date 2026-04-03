# Synthitect Protocol

An open-source Model Context Protocol (MCP) server implementing the **Contract-First Agentic Workflow (CFAW)** methodology for AI-assisted software engineering.

## Overview

The Synthitect Protocol enforces contract-first development by providing a structured, phased workflow that maintains architectural integrity across AI-assisted coding sessions. It solves the session statelessness problem inherent in AI development by externalizing decisions into versioned specifications.

## Architecture (Mixture-of-Agents)

```
synthitect-protocol/
├── prompts/                    # Sub-Agent system prompts
│   ├── probe-phase.md         # Probe Sub-Agent prompt
│   ├── discovery-phase.md     # Discovery Synthesizer prompt
│   ├── spec-phase.md         # Spec Architect prompt
│   ├── tdd-red-phase.md       # SDET Sub-Agent prompt
│   ├── implement-phase.md     # Implementation Engineer prompt
│   └── audit-phase.md        # Principal Auditor prompt
├── src/synthitect_mcp/
│   ├── __init__.py
│   ├── server.py             # MCP server with 6 tools
│   └── file_manager.py       # File I/O utility
├── SKILL.md                   # Orchestrator instructions (MoA Manager)
├── pyproject.toml
└── README.md
```

## Installation

```bash
# From source
pip install -e .

# Or install dependencies directly
pip install mcp>=1.0.0
```

## Usage

### Starting the MCP Server

```bash
# Using the CLI entry point
synthitect-mcp

# Or directly with Python
python -m synthitect_mcp
```

### MCP Tools (6 tools for MoA architecture)

Each tool returns a **text briefing**. The Orchestrator MUST spawn a sub-agent and pass the briefing as instructions. The MCP server does NOT execute sub-agents.

| Tool | Description |
|------|-------------|
| `generate_probe_briefing(ticket_id, layer_name, directory, raw_idea)` | Generates Probe Sub-Agent briefing for parallel discovery |
| `generate_discovery_briefing(ticket_id, raw_idea, probe_reports)` | Generates Discovery Synthesizer briefing |
| `generate_spec_briefing(ticket_id, tier)` | Generates Spec Architect briefing |
| `generate_tdd_red_briefing(ticket_id, tier)` | Generates SDET Sub-Agent briefing |
| `generate_implementation_briefing(ticket_id, tier)` | Generates Implementation Engineer briefing |
| `generate_audit_briefing(ticket_id, tier)` | Generates Principal Auditor briefing |

### Integration with Claude Code

Add to your Claude Code MCP configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "synthitect": {
      "command": "synthitect-mcp",
      "cwd": "/path/to/your/project"
    }
  }
}
```

Or install as a user-level MCP server:

```bash
# Add to your Claude Code MCP settings (Settings > Developer > Edit Config)
{
  "mcpServers": {
    "synthitect": {
      "command": "python",
      "args": ["-m", "synthitect_mcp"],
      "cwd": "/path/to/synthitect-protocol"
    }
  }
}
```

### Integration with Claude CLI

```bash
# Start Claude CLI with the Synthitect Protocol MCP server
claude --mcp-config /path/to/mcp-config.json

# Or use environment variable
export MCP_SERVER_PATH=/path/to/synthitect-protocol
claude
```

### Integration with Other MCP Clients

The server communicates over stdio, making it compatible with any MCP client:

```bash
# Direct execution
cd /path/to/your/project && python -m synthitect_mcp

# With custom base directory
SYNTHIECT_BASE_DIR=/path/to/your/project python -m synthitect_mcp
```

---

## Usage Examples

### Example 1: Full CFAW Lifecycle with Claude Code

```
User: /synthitect Add offline-first sync for user preferences

Orchestrator: I'll execute the Synthitect Protocol for this feature.
             Let me start with Scatter-Gather Discovery.

Step 1: Spawn parallel Probe Sub-Agents

Orchestrator uses generate_probe_briefing for each layer:
- generate_probe_briefing(ticket_id="FEAT-001", layer_name="Domain Layer", directory="src/domain/")
- generate_probe_briefing(ticket_id="FEAT-001", layer_name="Data Layer", directory="src/data/")
- generate_probe_briefing(ticket_id="FEAT-001", layer_name="Presentation Layer", directory="src/ui/")

Step 2: Synthesize discovery

Orchestrator uses generate_discovery_briefing:
generate_discovery_briefing(
  ticket_id="FEAT-001",
  raw_idea="Add offline-first sync for user preferences",
  probe_reports="[concatenated probe outputs]"
)

Step 3: Check for clarifying questions

IF discovery.md contains High-Impact Clarifying Questions:
  → STOP and prompt Architect for answers
ELSE:
  → Proceed to Spec phase

Step 4: Generate specs

Orchestrator uses generate_spec_briefing:
generate_spec_briefing(ticket_id="FEAT-001", tier="Tier 2")
→ Returns briefing for Orchestrator to give to Spec Architect Sub-Agent

HUMAN GATE: Present spec.md + test_spec.md to Architect for approval

Step 5: TDD Red

Orchestrator uses generate_tdd_red_briefing:
generate_tdd_red_briefing(ticket_id="FEAT-001", tier="Tier 2")
→ Returns briefing for Orchestrator to give to SDET Sub-Agent

HUMAN GATE: Architect verifies all tests are RED

Step 6: Implementation

Orchestrator uses generate_implementation_briefing:
generate_implementation_briefing(ticket_id="FEAT-001", tier="Tier 2")
→ Returns briefing for Orchestrator to give to Implementation Engineer Sub-Agent

Step 7: Audit

Orchestrator uses generate_audit_briefing:
generate_audit_briefing(ticket_id="FEAT-001", tier="Tier 2")
→ Returns briefing for Orchestrator to give to Principal Auditor Sub-Agent

HUMAN GATE: Architect reviews audit verdict and approves merge
```

### Example 2: Single-Phase Invocation

```javascript
// In Claude Code, you can invoke individual phases:

// Re-run just the discovery for a new idea
generate_probe_briefing("FEAT-002", "Domain Layer", "src/domain/", "Add payment processing")

// Generate specs after discovery is complete
generate_spec_briefing("FEAT-002", "Tier 2")

// Skip to TDD if spec already exists
generate_tdd_red_briefing("FEAT-002", "Tier 2")
```

### Example 3: Checking Phase Status

```bash
# Discovery artifacts are stored in plans/{ticket_id}/
ls plans/FEAT-001/
# discovery.md  spec.md  test_spec.md

# View the discovery document
cat plans/FEAT-001/discovery.md

# Check if a phase is complete
test -f plans/FEAT-001/spec.md && echo "Spec complete" || echo "Spec not ready"
```

### Example 4: Using with Custom Constitution

```bash
# Set a custom Constitution file
export CONSTITUTION_PATH=/path/to/project/CONSTITUTION.md

# The Orchestrator will inject this Constitution into sub-agent briefings
python -m synthitect_mcp
```

## CFAW Lifecycle

```
/synthitect [idea]
    │
    ▼
┌──────────────────────────────────────────────┐
│  Phase 1: Discovery                          │
│  generate_discovery_briefing(ticket_id, idea)│
│  Output: plans/{id}/discovery.md             │
└──────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────┐
│  Phase 2: Spec + Test Spec                   │
│  generate_spec_briefing(ticket_id)           │
│  Output: plans/{id}/spec.md                  │
│          plans/{id}/test_spec.md             │
└──────────────────────────────────────────────┘
    │  HUMAN GATE: Architect approval          │
    ▼
┌──────────────────────────────────────────────┐
│  Phase 3: TDD Red                            │
│  generate_tdd_red_briefing(ticket_id)        │
│  Output: Briefing for SDET Sub-Agent         │
└──────────────────────────────────────────────┘
    │  HUMAN GATE: Red state verified          │
    ▼
┌──────────────────────────────────────────────┐
│  Phase 4: Implementation                     │
│  generate_implementation_briefing(ticket_id) │
│  Output: Briefing for Implementation Engineer│
└──────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────┐
│  Phase 5: Audit                              │
│  generate_audit_briefing(ticket_id)          │
│  Output: Briefing for Principal Auditor      │
└──────────────────────────────────────────────┘
    │  HUMAN GATE: Merge approval              │
    ▼
   MERGE
```

## Key Features

### Contract-First Development
- All decisions externalized to versioned specs
- No code written without approved specification
- Constitution as architectural law

### Self-Review Loops
- Actor-Critic Reflection in Spec and TDD phases
- Tautology detection for tests
- Hallucination detection for dependencies

### Human Gates
- Architect approval required after Spec phase
- Red state verification before Implementation
- Merge approval after Audit

### Drift Detection
- File manifest tracking
- Hard flags for manifest/build changes
- Visibility mutation detection

## The CFAW Contract

1. Intelligence lives in specs, not chat history
2. Constitution is law. Violations are rejected.
3. No code without approved spec. No spec without Constitution audit.
4. Spec phase produces implementation plan AND test spec. Tests are red before implementation.
5. Implementation derives from spec. Tests are verifiers, not blueprints.
6. Drift is flagged proportionally. Minor is noted; Significant is reverted or amended.
7. Behavioral scenarios define done. Coverage numbers are a floor.
8. Ask of every test: What is the most broken implementation that still passes?

## Documentation

- [CFAW Specification](CFAW.md) - Full methodology specification
- [SKILL.md](SKILL.md) - Orchestrator instructions for AI agents

## License

0BSD
