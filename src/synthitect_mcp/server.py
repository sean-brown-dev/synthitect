"""Synthitect Protocol MCP Server.

A Model Context Protocol server implementing the Contract-First Agentic Workflow (CFAW).

Each tool has two responsibilities:
1. Manages phase artifacts (writes discovery.md, spec stubs, phase state tracking, etc.)
2. Returns a text briefing for the Orchestrator to give to a sub-agent

IMPORTANT: The MCP server does NOT execute sub-agents. It only generates their
system prompts (briefings) and manages the spec files. The Orchestrator is
responsible for spawning sub-agents and passing the briefings as instructions.

The MoA architecture delegates work to specialized sub-agents:
- Probe Sub-Agent: Read-only codebase indexer for a specific layer/directory
- Discovery Synthesizer Sub-Agent: Synthesizes probe reports into discovery.md
- Spec Architect Sub-Agent: Produces spec.md and test_spec.md
- SDET Sub-Agent: Writes failing tests against skeleton stubs
- Implementation Engineer Sub-Agent: Writes production code to pass tests
- Principal Auditor Sub-Agent: Performs adversarial code review
"""

import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .file_manager import FileManager


# Server instance
server = Server("synthitect-protocol")


def get_file_manager() -> FileManager:
    """Get FileManager instance with configurable base directory.

    Returns:
        FileManager instance.
    """
    base_dir = os.environ.get("SYNTHIECT_BASE_DIR")
    return FileManager(base_dir)


# ============================================================================
# MCP Tool Definitions
# ============================================================================

TOOLS = [
    Tool(
        name="generate_probe_briefing",
        description="""Generates a Sub-Agent Briefing for a Probe Sub-Agent.

This tool does NOT execute the sub-agent. It does two things:
1. Creates the plans/{ticket_id}/ directory
2. Returns a text briefing — the Orchestrator MUST spawn a Probe Sub-Agent
   and pass this briefing as the sub-agent's instructions.

A Probe Sub-Agent indexes a specific directory/layer of the codebase during
the Scatter-Gather Discovery phase. Multiple probes run in parallel.

INPUTS:
- ticket_id: Unique identifier for this feature/ticket
- layer_name: Name for this probe's target area (e.g., 'Domain Layer', 'Data Layer')
- directory: The specific directory path to index
- raw_idea: The original user description for context

OUTPUT:
Returns a text briefing. The Orchestrator spawns the Probe Sub-Agent with it.
All probe reports are concatenated and passed to generate_discovery_briefing.""",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "Ticket identifier"
                },
                "layer_name": {
                    "type": "string",
                    "description": "Human-readable name for this probe's target area (e.g., 'Domain Layer', 'Data Layer')"
                },
                "directory": {
                    "type": "string",
                    "description": "The directory path this probe should index"
                },
                "raw_idea": {
                    "type": "string",
                    "description": "The original user description for context"
                }
            },
            "required": ["ticket_id", "layer_name", "directory", "raw_idea"]
        }
    ),
    Tool(
        name="generate_discovery_briefing",
        description="""Generates a Sub-Agent Briefing for the Discovery Synthesizer Sub-Agent.

This tool does NOT execute the sub-agent. It does three things:
1. Creates plans/{ticket_id}/ directory
2. Writes plans/{ticket_id}/discovery.md with raw probe reports synthesized
3. Returns a text briefing — the Orchestrator MUST spawn a Discovery Synthesizer
   Sub-Agent and pass this briefing as the sub-agent's instructions.

INPUTS:
- ticket_id: Unique identifier for this feature/ticket (e.g., 'TASK-123')
- raw_idea: The user's raw description of the feature to build
- probe_reports: Concatenated output from N parallel Probe Sub-Agents

OUTPUT:
Returns a text briefing. The Orchestrator spawns the Discovery Synthesizer
Sub-Agent with it. The sub-agent refines discovery.md by analyzing overlaps,
gaps, and conflicts.

CONDITIONAL HUMAN GATE: After discovery.md is generated, the Orchestrator must check
for High-Impact Clarifying Questions. If any exist, it MUST halt and prompt the Architect
for answers before proceeding to the Spec phase.""",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "Unique identifier for the feature/ticket (e.g., 'TASK-123', 'FEAT-offline-sync')"
                },
                "raw_idea": {
                    "type": "string",
                    "description": "The user's raw description of the feature or change to implement"
                },
                "probe_reports": {
                    "type": "string",
                    "description": "Concatenated probe reports from N parallel Probe Sub-Agents. Each report contains: existing data models, dependencies & API contracts, utility/shared classes, and impact observations from a specific layer."
                }
            },
            "required": ["ticket_id", "raw_idea", "probe_reports"]
        }
    ),
    Tool(
        name="generate_spec_briefing",
        description="""Generates a Sub-Agent Briefing for the Spec Architect Sub-Agent.

This tool does NOT execute the sub-agent. It does three things:
1. Verifies discovery.md exists for the ticket
2. Writes stub plans/{ticket_id}/spec.md and test_spec.md files
3. Returns a text briefing — the Orchestrator MUST spawn a Spec Architect
   Sub-Agent and pass this briefing as the sub-agent's instructions.

The Spec Architect consumes the discovery document and produces:
- spec.md: The implementation plan (architecture contract)
- test_spec.md: The behavioral test specification (Gherkin scenarios)

INPUTS:
- ticket_id: The ticket identifier (must have completed Discovery phase)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a text briefing. The Orchestrator spawns the Spec Architect Sub-Agent with it.
The sub-agent fills in the spec.md and test_spec.md stubs with real content.

HARD HUMAN GATE: After the sub-agent completes, the Orchestrator MUST present
spec.md and test_spec.md to the Architect for approval. NO tests or code may be
written until explicit approval is granted.""",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "Ticket identifier (must have completed Discovery phase)"
                },
                "tier": {
                    "type": "string",
                    "description": "Tier classification: 'Tier 2' or 'Tier 3'. Defaults to 'Tier 2'.",
                    "default": "Tier 2"
                }
            },
            "required": ["ticket_id"]
        }
    ),
    Tool(
        name="generate_tdd_red_briefing",
        description="""Generates a Sub-Agent Briefing for the SDET Sub-Agent.

This tool does NOT execute the sub-agent. It does three things:
1. Verifies spec.md and test_spec.md exist for the ticket
2. Writes plans/{ticket_id}/stub_implementation.py (empty stubs for tests to compile against)
3. Returns a text briefing — the Orchestrator MUST spawn an SDET Sub-Agent
   and pass this briefing as the sub-agent's instructions.

The SDET Sub-Agent writes failing tests based on the approved test_spec.md.

INPUTS:
- ticket_id: The ticket identifier (must have Architect-approved spec)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a text briefing. The Orchestrator spawns the SDET Sub-Agent with it.
The sub-agent writes tests against the stub_implementation.py skeleton.

HUMAN GATE: The Architect must verify all tests are genuinely RED before
the Implementation phase begins. After verification, mark tdd_red as
completed before calling generate_implementation_briefing.""",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "Ticket identifier (must have Architect-approved spec)"
                },
                "tier": {
                    "type": "string",
                    "description": "Tier classification: 'Tier 2' or 'Tier 3'. Defaults to 'Tier 2'.",
                    "default": "Tier 2"
                }
            },
            "required": ["ticket_id"]
        }
    ),
    Tool(
        name="generate_implementation_briefing",
        description="""Generates a Sub-Agent Briefing for the Implementation Engineer Sub-Agent.

This tool does NOT execute the sub-agent. It does two things:
1. Verifies tdd_red phase is completed (tests written and verified RED)
2. Returns a text briefing — the Orchestrator MUST spawn an Implementation
   Engineer Sub-Agent and pass this briefing as the sub-agent's instructions.

The Implementation Engineer writes production code to pass all failing tests.

INPUTS:
- ticket_id: The ticket identifier (must have completed TDD Red phase)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a text briefing. The Orchestrator spawns the Implementation Engineer
Sub-Agent with it.""",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "Ticket identifier (must have completed TDD Red phase)"
                },
                "tier": {
                    "type": "string",
                    "description": "Tier classification: 'Tier 2' or 'Tier 3'. Defaults to 'Tier 2'.",
                    "default": "Tier 2"
                }
            },
            "required": ["ticket_id"]
        }
    ),
    Tool(
        name="generate_audit_briefing",
        description="""Generates a Sub-Agent Briefing for the Principal Auditor Sub-Agent.

This tool does NOT execute the sub-agent. It returns a text briefing — the
Orchestrator MUST spawn a Principal Auditor Sub-Agent and pass this briefing
as the sub-agent's instructions.

The Principal Auditor performs adversarial code review, drift audit, and
TDD guardrail verification.

INPUTS:
- ticket_id: The ticket identifier (must have completed Implementation phase)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a text briefing. The Orchestrator spawns the Principal Auditor
Sub-Agent with it. After completion, the Architect reviews the audit
verdict and approves or rejects merge.""",
        inputSchema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "Ticket identifier (must have completed Implementation phase)"
                },
                "tier": {
                    "type": "string",
                    "description": "Tier classification: 'Tier 2' or 'Tier 3'. Defaults to 'Tier 2'.",
                    "default": "Tier 2"
                }
            },
            "required": ["ticket_id"]
        }
    ),
]


# ============================================================================
# Tool Handlers
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for the Synthitect Protocol.

    Each tool generates a Sub-Agent Briefing — a structured prompt
    that the Orchestrator hands off to a specialized sub-agent.
    The tool returns text; it does NOT execute the sub-agent.
    """
    fm = get_file_manager()

    if name == "generate_discovery_briefing":
        return await generate_discovery_briefing(fm, arguments)
    elif name == "generate_probe_briefing":
        return await generate_probe_briefing(fm, arguments)
    elif name == "generate_spec_briefing":
        return await generate_spec_briefing(fm, arguments)
    elif name == "generate_tdd_red_briefing":
        return await generate_tdd_red_briefing(fm, arguments)
    elif name == "generate_implementation_briefing":
        return await generate_implementation_briefing(fm, arguments)
    elif name == "generate_audit_briefing":
        return await generate_audit_briefing(fm, arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def generate_discovery_briefing(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Discovery Synthesizer Sub-Agent.

    Creates plans/{ticket_id} directory, writes discovery.md, and returns a briefing
    that the Orchestrator gives to the Discovery Synthesizer Sub-Agent.
    """
    ticket_id = arguments["ticket_id"]
    raw_idea = arguments["raw_idea"]
    probe_reports = arguments["probe_reports"]

    fm.create_ticket_directory(ticket_id)

    # Write initial discovery.md with probe reports synthesized
    template = fm.read_template("discovery-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "raw_idea": raw_idea,
        "probe_reports": probe_reports
    }
    briefing = fm.inject_variables(template, variables)

    # Write discovery.md to plans/{ticket_id}/discovery.md
    discovery_content = f"""# Discovery: {ticket_id}

## 1. Goal Summary
{raw_idea}

## 2. Target Module Index

### Existing Data Models
[To be filled by Discovery Synthesizer based on probe reports]

### Dependencies & API Contracts
[To be filled by Discovery Synthesizer based on probe reports]

### Utility/Shared Classes
[To be filled by Discovery Synthesizer based on probe reports]

### Impact Radius
[To be filled by Discovery Synthesizer based on probe reports]

## 3. Cross-Probe Analysis

### Overlaps Identified
[To be filled by Discovery Synthesizer]

### Gaps & Uncertainties
[To be filled by Discovery Synthesizer]

### Conflicts (if any)
[To be filled by Discovery Synthesizer]

## 4. High-Impact Clarifying Questions
*None identified. Proceeding to Spec phase.*

## 5. Probe Coverage Summary
| Layer/Directory | Probe Agent | Key Findings |
|----------------|------------|-------------|
| [TBD] | [TBD] | [TBD] |

---

## Raw Probe Reports (for Synthesis)

```
{probe_reports}
```
"""

    fm.write_file(f"plans/{ticket_id}/discovery.md", discovery_content)

    # Mark discovery phase as in-progress so generate_spec_briefing can proceed
    fm.set_phase_state(ticket_id, "discovery", completed=False)

    return [TextContent(type="text", text=briefing)]


async def generate_probe_briefing(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for a Probe Sub-Agent.

    Returns a text briefing for the Orchestrator to give to a Probe Sub-Agent.
    Multiple probes run in parallel during Scatter-Gather Discovery.
    """
    ticket_id = arguments["ticket_id"]
    layer_name = arguments["layer_name"]
    directory = arguments["directory"]
    raw_idea = arguments["raw_idea"]

    fm.create_ticket_directory(ticket_id)

    template = fm.read_template("probe-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "layer_name": layer_name,
        "directory": directory,
        "raw_idea": raw_idea
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def generate_spec_briefing(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Spec Architect Sub-Agent.

    Creates stub spec files, sets spec phase to in-progress, and returns a briefing
    for the Orchestrator to give to the Spec Architect Sub-Agent.
    """
    ticket_id = arguments["ticket_id"]
    tier = arguments.get("tier", "Tier 2")

    if not fm.ensure_discovery_exists(ticket_id):
        return [TextContent(
            type="text",
            text=f"ERROR: Discovery phase not completed for ticket '{ticket_id}'. "
                 f"Please generate probe briefings and run discovery first."
        )]

    # Write stub spec files so subsequent tools can check for their existence
    spec_stub = f"""# Technical Specification: {ticket_id}

## 1. Objective
[To be filled by Spec Architect based on discovery.md]

## 2. System Architecture
[To be filled by Spec Architect]

## 3. Data Models & Schemas
[To be filled by Spec Architect]

## 4. API Contracts & Interfaces
[To be filled by Spec Architect]

## 5. Permissions & Config Delta
[To be filled by Spec Architect]

## 6. Constitution Audit
[To be filled by Spec Architect]

## 7. Cross-Spec Dependencies
[To be filled by Spec Architect]
"""
    test_spec_stub = f"""# Test Specification: {ticket_id}

## 1. Happy Path Scenarios
[To be filled by Spec Architect based on discovery.md]

## 2. Error Path & Edge Case Scenarios
[To be filled by Spec Architect]

## 3. Mutation Defense
[To be filled by Spec Architect]
"""
    fm.write_file(f"plans/{ticket_id}/spec.md", spec_stub)
    fm.write_file(f"plans/{ticket_id}/test_spec.md", test_spec_stub)

    # Mark spec phase as in-progress so generate_tdd_red_briefing can proceed
    fm.set_phase_state(ticket_id, "spec", completed=False)

    template = fm.read_template("spec-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "tier": tier
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def generate_tdd_red_briefing(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for SDET Sub-Agent.

    Creates stub implementation files, sets tdd_red phase to in-progress, and returns
    a briefing for the Orchestrator to give to the SDET Sub-Agent.
    """
    ticket_id = arguments["ticket_id"]
    tier = arguments.get("tier", "Tier 2")

    if not fm.ensure_spec_exists(ticket_id):
        return [TextContent(
            type="text",
            text=f"ERROR: Spec phase not completed for ticket '{ticket_id}'. "
                 f"Please generate a spec briefing and obtain Architect approval first."
        )]

    # Write stub implementation files so tests have something to compile against
    stub_content = f"""# Implementation Stub: {ticket_id}

# This file is a placeholder. The Implementation Engineer will replace
# these stubs with actual implementation after TDD Red phase is complete.

class StubClass:
    pass
"""
    fm.write_file(f"plans/{ticket_id}/stub_implementation.py", stub_content)

    # Mark tdd_red phase as in-progress (Architect verifies RED state before implementation)
    fm.set_phase_state(ticket_id, "tdd_red", completed=False)

    template = fm.read_template("tdd-red-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "tier": tier
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def generate_implementation_briefing(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Implementation Engineer Sub-Agent.

    Returns a briefing for the Orchestrator to give to the Implementation Engineer
    Sub-Agent. Verifies TDD Red phase was completed.
    """
    ticket_id = arguments["ticket_id"]
    tier = arguments.get("tier", "Tier 2")

    if not fm.check_phase_prerequisite(ticket_id, "tdd_red"):
        return [TextContent(
            type="text",
            text=f"ERROR: TDD Red phase not completed for ticket '{ticket_id}'. "
                 f"Please generate a TDD red briefing, spawn the SDET Sub-Agent, "
                 f"and verify RED state before proceeding."
        )]

    # Mark implementation phase as in-progress
    fm.set_phase_state(ticket_id, "implementation", completed=False)

    template = fm.read_template("implement-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "tier": tier
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def generate_audit_briefing(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Principal Auditor Sub-Agent.

    Returns a briefing for the Orchestrator to give to the Principal Auditor Sub-Agent.
    """
    ticket_id = arguments["ticket_id"]
    tier = arguments.get("tier", "Tier 2")

    template = fm.read_template("audit-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "tier": tier
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


# ============================================================================
# Server Entry Point
# ============================================================================

async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main_cli():
    """CLI entry point."""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    main_cli()
