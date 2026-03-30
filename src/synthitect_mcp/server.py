"""Synthitect Protocol MCP Server.

A Model Context Protocol server implementing the Contract-First Agentic Workflow (CFAW).
Provides tools for executing the full CFAW lifecycle using a Mixture-of-Agents (MoA) architecture.

The Orchestrator (the AI using this server) delegates work to specialized sub-agents:
- Discovery Synthesizer Sub-Agent: Synthesizes probe reports into discovery.md
- Spec Architect Sub-Agent: Produces spec.md and test_spec.md
- SDET Sub-Agent: Writes failing tests
- Implementation Engineer Sub-Agent: Writes production code
- Principal Auditor Sub-Agent: Performs adversarial code review

Each tool generates a "Sub-Agent Briefing" — a structured prompt handed off to a specialized
sub-agent with a pristine context window.
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
        name="run_discovery",
        description="""Generates a Sub-Agent Briefing for the Discovery Synthesizer Sub-Agent.

This tool takes raw probe intelligence from multiple parallel Probe Sub-Agents and synthesizes
them into a coherent discovery.md artifact.

INPUTS:
- ticket_id: Unique identifier for this feature/ticket (e.g., 'TASK-123')
- raw_idea: The user's raw description of the feature to build
- probe_reports: Concatenated output from N parallel Probe Sub-Agents, each having
  indexed a specific layer/directory of the codebase

OUTPUT:
Returns a structured Sub-Agent Briefing for the Discovery Synthesizer Sub-Agent.
The briefing instructs the sub-agent to:
1. Analyze the probe reports for overlaps, gaps, and conflicts
2. Stitch together a unified Target Module Index
3. Generate High-Impact Clarifying Questions ONLY if they are true architectural blockers
4. Output discovery.md

IMPORTANT: This does NOT execute Discovery directly — it generates the briefing for delegation.
The Orchestrator then hands this briefing to a Discovery Synthesizer sub-agent.

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
        name="spawn_probe",
        description="""Generates a Sub-Agent Briefing for a Probe Sub-Agent.

A Probe Sub-Agent is a read-only agent that indexes a specific directory/layer of the codebase
in parallel with other probes during the Scatter-Gather Discovery phase.

INPUTS:
- ticket_id: Unique identifier for this feature/ticket
- layer_name: Human-readable name for this probe's target area (e.g., 'Domain Layer', 'Data Layer', 'UI Layer')
- directory: The specific directory path this probe should index
- raw_idea: The original user description for context

OUTPUT:
Returns a Sub-Agent Briefing instructing the probe to:
1. Analyze the target directory
2. Surface existing data models, dependencies, API contracts, and utility classes
3. Note impact radius and potential integration points
4. Output findings in a structured format

IMPORTANT: Probe Sub-Agents run in PARALLEL during Scatter-Gather Discovery.
All probe reports are concatenated and passed to the Discovery Synthesizer via run_discovery.""",
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
        name="generate_specs",
        description="""Generates a Sub-Agent Briefing for the Spec Architect Sub-Agent.

The Spec Architect Sub-Agent consumes the discovery document and produces:
- spec.md: The implementation plan (architecture contract)
- test_spec.md: The behavioral test specification (Gherkin scenarios)

INPUTS:
- ticket_id: The ticket identifier (must have completed Discovery phase)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a Sub-Agent Briefing instructing the sub-agent to:
1. Read the discovery document
2. Draft spec.md with architecture, data models, API contracts
3. Draft test_spec.md with Gherkin behavioral scenarios
4. Execute the Actor-Critic Reflection Loop to self-critique
5. Output final artifacts only after passing all reflection checks

IMPORTANT: This tool generates a briefing for delegation. The Orchestrator hands this
to a single Spec Architect sub-agent (no parallelization allowed).

HARD HUMAN GATE: After the briefing is generated and the sub-agent completes,
the Orchestrator MUST present spec.md and test_spec.md to the Architect for approval.
NO tests or code may be written until explicit approval is granted.""",
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
        name="execute_tdd_red",
        description="""Generates a Sub-Agent Briefing for the SDET Sub-Agent.

The SDET (Software Development Engineer in Test) Sub-Agent writes failing tests
based on the approved test_spec.md behavioral scenarios.

INPUTS:
- ticket_id: The ticket identifier (must have Architect-approved spec)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a Sub-Agent Briefing instructing the sub-agent to:
1. Read spec.md for type signatures (NOT implementation logic)
2. Read test_spec.md for behavioral scenarios
3. Generate skeleton stubs with NotImplementedError
4. Write test methods for every scenario
5. Execute the Actor-Critic Reflection Loop (tautology check, mock/spy audit, etc.)
6. Confirm all tests fail (RED state)

IMPORTANT: Single-threaded delegation — spawn ONE SDET sub-agent only.

HUMAN GATE: The Architect must verify all tests are genuinely RED before
the Implementation phase begins. Any test that passes against the skeleton
is INVALID and must be rewritten.""",
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
        name="implement_green",
        description="""Generates a Sub-Agent Briefing for the Implementation Engineer Sub-Agent.

The Implementation Engineer Sub-Agent writes production-ready code to pass all failing tests.

INPUTS:
- ticket_id: The ticket identifier (must have completed TDD Red phase)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a Sub-Agent Briefing instructing the sub-agent to:
1. Read spec.md as the absolute source of truth
2. Read test_spec.md for behavioral contracts
3. Derive implementation from spec, NOT from test assertions
4. Implement one component at a time with test verification
5. STOP if new behavior is needed without a test
6. Report GREEN state when all tests pass

IMPORTANT: Single-threaded delegation — spawn ONE Implementation Engineer only.
The sub-agent must flag drift and halt if files outside the spec are needed.

PHASE PREREQUISITE: Must have completed TDD Red phase. The Orchestrator verifies
RED state before calling this tool.""",
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
        name="run_audit",
        description="""Generates a Sub-Agent Briefing for the Principal Auditor Sub-Agent.

The Principal Auditor Sub-Agent performs adversarial code review, drift audit,
and TDD guardrail verification.

INPUTS:
- ticket_id: The ticket identifier (must have completed Implementation phase)
- tier: The tier classification (Tier 2 or Tier 3). Defaults to Tier 2.

OUTPUT:
Returns a Sub-Agent Briefing instructing the sub-agent to:
1. Execute the Meta-Guardrail: "What is the most broken implementation that still passes?"
2. Perform Drift Audit against spec.md file manifest
3. Verify TDD guardrails (no tautologies, proper expected value provenance)
4. Scan for Constitution violations
5. Categorize findings into Bucket A/B/C triage
6. Output structured Audit Report with Pass/Minor Drift/Fail verdict

IMPORTANT: Single-threaded delegation — spawn ONE Auditor only.
Do NOT propose fixes — only diagnose and verify.

HUMAN GATE: The Architect reviews the audit verdict and approves or rejects merge.

NOTE: Test execution results should be injected by the Orchestrator if available.""",
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
    )
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
    """
    fm = get_file_manager()

    if name == "run_discovery":
        return await run_discovery(fm, arguments)
    elif name == "spawn_probe":
        return await spawn_probe(fm, arguments)
    elif name == "generate_specs":
        return await generate_specs(fm, arguments)
    elif name == "execute_tdd_red":
        return await execute_tdd_red(fm, arguments)
    elif name == "implement_green":
        return await implement_green(fm, arguments)
    elif name == "run_audit":
        return await run_audit(fm, arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def run_discovery(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Discovery Synthesizer Sub-Agent.

    Creates plans/{ticket_id} directory and returns a briefing that instructs
    the Discovery Synthesizer to synthesize probe reports into discovery.md.
    """
    ticket_id = arguments["ticket_id"]
    raw_idea = arguments["raw_idea"]
    probe_reports = arguments["probe_reports"]

    fm.create_ticket_directory(ticket_id)

    template = fm.read_template("discovery-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "raw_idea": raw_idea,
        "probe_reports": probe_reports
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def spawn_probe(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for a Probe Sub-Agent.

    A Probe Sub-Agent indexes a specific directory/layer in read-only mode.
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


async def generate_specs(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Spec Architect Sub-Agent.

    Returns a briefing for the Spec Architect to produce spec.md and test_spec.md.
    Verifies Discovery phase was completed first.
    """
    ticket_id = arguments["ticket_id"]
    tier = arguments.get("tier", "Tier 2")

    if not fm.ensure_discovery_exists(ticket_id):
        return [TextContent(
            type="text",
            text=f"ERROR: Discovery phase not completed for ticket '{ticket_id}'. "
                 f"Please execute Scatter-Gather Discovery first using run_discovery."
        )]

    template = fm.read_template("spec-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "tier": tier
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def execute_tdd_red(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for SDET Sub-Agent.

    Returns a briefing for the SDET to write failing tests.
    Verifies Spec phase was completed with Architect approval.
    """
    ticket_id = arguments["ticket_id"]
    tier = arguments.get("tier", "Tier 2")

    if not fm.ensure_spec_exists(ticket_id):
        return [TextContent(
            type="text",
            text=f"ERROR: Spec phase not completed for ticket '{ticket_id}'. "
                 f"Please run generate_specs first and obtain Architect approval."
        )]

    template = fm.read_template("tdd-red-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "tier": tier
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def implement_green(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Implementation Engineer Sub-Agent.

    Returns a briefing for the Implementation Engineer to write production code.
    Verifies TDD Red phase was completed.
    """
    ticket_id = arguments["ticket_id"]
    tier = arguments.get("tier", "Tier 2")

    if not fm.check_phase_prerequisite(ticket_id, "tdd_red"):
        return [TextContent(
            type="text",
            text=f"ERROR: TDD Red phase not completed for ticket '{ticket_id}'. "
                 f"Please run execute_tdd_red and verify RED state first."
        )]

    template = fm.read_template("implement-phase.md")

    variables = {
        "ticket_id": ticket_id,
        "tier": tier
    }
    briefing = fm.inject_variables(template, variables)

    return [TextContent(type="text", text=briefing)]


async def run_audit(fm: FileManager, arguments: dict) -> list[TextContent]:
    """Generate Sub-Agent Briefing for Principal Auditor Sub-Agent.

    Returns a briefing for the Principal Auditor to perform adversarial review.
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
