"""Synthitect Protocol MCP Server.

A Model Context Protocol server implementing the Contract-First Agentic Workflow (CFAW).
Provides tools that generate Sub-Agent Briefings — structured prompts that the
Orchestrator hands off to specialized sub-agents. These tools DO NOT execute
sub-agents; they return text briefings for the Orchestrator to delegate.

Usage:
    from synthitect_mcp import server
    # Run with: python -m synthitect_mcp

Architecture:
    - server.py: Core MCP server with 6 briefing-generation tools
    - file_manager.py: File I/O utility for plan artifacts

Tools (all return text briefings; Orchestrator must spawn sub-agents):
    1. generate_probe_briefing(ticket_id, layer_name, directory, raw_idea) -> str
    2. generate_discovery_briefing(ticket_id, raw_idea, probe_reports) -> str
    3. generate_spec_briefing(ticket_id, tier) -> str
    4. generate_tdd_red_briefing(ticket_id, tier) -> str
    5. generate_implementation_briefing(ticket_id, tier) -> str
    6. generate_audit_briefing(ticket_id, tier) -> str
"""

__version__ = "1.0.0"
__description__ = "Synthitect Protocol MCP Server - CFAW Implementation"
