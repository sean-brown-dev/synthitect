"""Synthitect Protocol MCP Server.

A Model Context Protocol server implementing the Contract-First Agentic Workflow (CFAW).
Provides tools for executing the full CFAW lifecycle: Discovery, Spec, TDD Red, Implement, and Audit.

Usage:
    from synthitect_mcp import server
    # Run with: python -m synthitect_mcp

Architecture:
    - server.py: Core MCP server with 5 tools
    - file_manager.py: File I/O utility for plan artifacts

Tools:
    1. run_discovery(ticket_id, raw_idea) -> str
    2. generate_specs(ticket_id) -> str
    3. execute_tdd_red(ticket_id) -> str
    4. implement_green(ticket_id) -> str
    5. run_audit(ticket_id) -> str
"""

__version__ = "1.0.0"
__description__ = "Synthitect Protocol MCP Server - CFAW Implementation"
