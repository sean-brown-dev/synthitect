"""Unit tests for MCP server tools."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from synthitect_mcp.file_manager import FileManager
from synthitect_mcp.server import (
    spawn_probe,
    run_discovery,
    generate_specs,
    execute_tdd_red,
    implement_green,
    run_audit,
)

# Project root directory (for accessing prompts/)
PROJECT_ROOT = Path(__file__).parent.parent


class TestServerTools:
    """Tests for MCP server tool functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    @pytest.fixture
    def fm(self, temp_dir):
        """Create a FileManager instance with temp directory."""
        # Copy prompts directory to temp so server tools can find templates
        temp_prompts = temp_dir / "prompts"
        shutil.copytree(PROJECT_ROOT / "prompts", temp_prompts)
        return FileManager(str(temp_dir))

    @pytest.fixture
    def fm_with_artifacts(self, fm):
        """Create a FileManager with complete test artifacts."""
        ticket_id = "TEST-001"
        ticket_dir = fm.create_ticket_directory(ticket_id)

        # Create discovery.md
        (ticket_dir / "discovery.md").write_text("# Discovery: Test Feature\n\n## Goal Summary\nTest.")

        # Create spec.md
        (ticket_dir / "spec.md").write_text("# Technical Specification\n\n## 1. System Architecture")

        # Create test_spec.md
        (ticket_dir / "test_spec.md").write_text("# Test Specification\n\n## 1. Happy Path Scenarios")

        # Set all phases complete
        fm.set_phase_state(ticket_id, "discovery", completed=True)
        fm.set_phase_state(ticket_id, "spec", completed=True)
        fm.set_phase_state(ticket_id, "tdd_red", completed=True)
        fm.set_phase_state(ticket_id, "implementation", completed=True)

        return fm, ticket_id

    # =========================================================================
    # spawn_probe Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_spawn_probe_returns_briefing(self, fm):
        """Test that spawn_probe returns a briefing string."""
        result = await spawn_probe(fm, {
            "ticket_id": "TEST-001",
            "layer_name": "Domain Layer",
            "directory": "src/domain/",
            "raw_idea": "Add user authentication"
        })

        assert len(result) == 1
        assert result[0].type == "text"
        assert len(result[0].text) > 100

    @pytest.mark.asyncio
    async def test_spawn_probe_injects_variables(self, fm):
        """Test that spawn_probe injects variables into template."""
        result = await spawn_probe(fm, {
            "ticket_id": "TEST-001",
            "layer_name": "Data Layer",
            "directory": "src/data/",
            "raw_idea": "Add persistence"
        })

        text = result[0].text
        assert "TEST-001" in text
        assert "Data Layer" in text
        assert "src/data/" in text
        assert "Add persistence" in text

    @pytest.mark.asyncio
    async def test_spawn_probe_creates_ticket_directory(self, fm):
        """Test that spawn_probe creates the ticket directory."""
        await spawn_probe(fm, {
            "ticket_id": "PROBE-001",
            "layer_name": "Test",
            "directory": "test/",
            "raw_idea": "Test"
        })

        assert (fm.base_dir / "plans" / "PROBE-001").exists()

    # =========================================================================
    # run_discovery Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_run_discovery_returns_briefing(self, fm):
        """Test that run_discovery returns a briefing string."""
        result = await run_discovery(fm, {
            "ticket_id": "TEST-001",
            "raw_idea": "Add offline sync",
            "probe_reports": "# Probe: Domain Layer\n- User entity found"
        })

        assert len(result) == 1
        assert result[0].type == "text"
        assert len(result[0].text) > 100

    @pytest.mark.asyncio
    async def test_run_discovery_injects_variables(self, fm):
        """Test that run_discovery injects all variables."""
        result = await run_discovery(fm, {
            "ticket_id": "DISC-001",
            "raw_idea": "Add caching",
            "probe_reports": "# Probe Report\n## Existing Data Models\n- Cache model"
        })

        text = result[0].text
        assert "DISC-001" in text
        assert "Add caching" in text
        assert "Probe Report" in text
        assert "Cache model" in text

    # =========================================================================
    # generate_specs Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_generate_specs_returns_briefing(self, fm_with_artifacts):
        """Test that generate_specs returns a briefing."""
        fm, ticket_id = fm_with_artifacts
        result = await generate_specs(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert len(result[0].text) > 100

    @pytest.mark.asyncio
    async def test_generate_specs_injects_tier(self, fm_with_artifacts):
        """Test that generate_specs injects tier variable."""
        fm, ticket_id = fm_with_artifacts
        result = await generate_specs(fm, {"ticket_id": ticket_id, "tier": "Tier 3"})

        text = result[0].text
        assert "Tier 3" in text
        assert "{{ tier }}" not in text

    @pytest.mark.asyncio
    async def test_generate_specs_requires_discovery(self, fm):
        """Test that generate_specs fails without discovery.md."""
        fm.create_ticket_directory("NO-DISCOVERY")

        result = await generate_specs(fm, {"ticket_id": "NO-DISCOVERY", "tier": "Tier 2"})

        assert "ERROR" in result[0].text
        assert "Discovery phase not completed" in result[0].text

    # =========================================================================
    # execute_tdd_red Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_execute_tdd_red_returns_briefing(self, fm_with_artifacts):
        """Test that execute_tdd_red returns a briefing."""
        fm, ticket_id = fm_with_artifacts
        result = await execute_tdd_red(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert len(result[0].text) > 100

    @pytest.mark.asyncio
    async def test_execute_tdd_red_injects_tier(self, fm_with_artifacts):
        """Test that execute_tdd_red injects tier variable."""
        fm, ticket_id = fm_with_artifacts
        result = await execute_tdd_red(fm, {"ticket_id": ticket_id, "tier": "Tier 3"})

        text = result[0].text
        assert "Tier 3" in text
        assert "{{ tier }}" not in text

    @pytest.mark.asyncio
    async def test_execute_tdd_red_requires_spec(self, fm):
        """Test that execute_tdd_red fails without spec files."""
        fm.create_ticket_directory("NO-SPEC")
        # Only create discovery, not spec files
        (fm.base_dir / "plans" / "NO-SPEC" / "discovery.md").write_text("# Discovery")

        result = await execute_tdd_red(fm, {"ticket_id": "NO-SPEC", "tier": "Tier 2"})

        assert "ERROR" in result[0].text
        assert "Spec phase not completed" in result[0].text

    # =========================================================================
    # implement_green Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_implement_green_returns_briefing(self, fm_with_artifacts):
        """Test that implement_green returns a briefing."""
        fm, ticket_id = fm_with_artifacts
        result = await implement_green(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert len(result[0].text) > 100

    @pytest.mark.asyncio
    async def test_implement_green_injects_tier(self, fm_with_artifacts):
        """Test that implement_green injects tier variable."""
        fm, ticket_id = fm_with_artifacts
        result = await implement_green(fm, {"ticket_id": ticket_id, "tier": "Tier 3"})

        text = result[0].text
        assert "Tier 3" in text
        assert "{{ tier }}" not in text

    @pytest.mark.asyncio
    async def test_implement_green_requires_tdd_red(self, fm):
        """Test that implement_green fails without tdd_red phase."""
        fm.create_ticket_directory("NO-TDD")

        result = await implement_green(fm, {"ticket_id": "NO-TDD", "tier": "Tier 2"})

        assert "ERROR" in result[0].text
        assert "TDD Red phase not completed" in result[0].text

    @pytest.mark.asyncio
    async def test_implement_green_with_tdd_red_complete(self, fm):
        """Test that implement_green succeeds when tdd_red is complete."""
        # Setup: create ticket with all phases complete
        fm.create_ticket_directory("READY")
        (fm.base_dir / "plans" / "READY" / "discovery.md").write_text("# Discovery")
        (fm.base_dir / "plans" / "READY" / "spec.md").write_text("# Spec")
        (fm.base_dir / "plans" / "READY" / "test_spec.md").write_text("# Test Spec")
        fm.set_phase_state("READY", "discovery", completed=True)
        fm.set_phase_state("READY", "spec", completed=True)
        fm.set_phase_state("READY", "tdd_red", completed=True)

        result = await implement_green(fm, {"ticket_id": "READY", "tier": "Tier 2"})

        assert "ERROR" not in result[0].text
        assert len(result[0].text) > 100

    # =========================================================================
    # run_audit Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_run_audit_returns_briefing(self, fm_with_artifacts):
        """Test that run_audit returns a briefing."""
        fm, ticket_id = fm_with_artifacts
        result = await run_audit(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert len(result[0].text) > 100

    @pytest.mark.asyncio
    async def test_run_audit_injects_tier(self, fm_with_artifacts):
        """Test that run_audit injects tier variable."""
        fm, ticket_id = fm_with_artifacts
        result = await run_audit(fm, {"ticket_id": ticket_id, "tier": "Tier 3"})

        text = result[0].text
        assert "Tier 3" in text
        assert "{{ tier }}" not in text

    # =========================================================================
    # Template Content Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_spec_phase_has_scope_limits(self, fm_with_artifacts):
        """Test that spec phase briefing contains scope limits."""
        fm, ticket_id = fm_with_artifacts
        result = await generate_specs(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        text = result[0].text
        assert "Scope Limits" in text
        assert "Tier 2" in text

    @pytest.mark.asyncio
    async def test_tdd_phase_has_scope_limits(self, fm_with_artifacts):
        """Test that TDD phase briefing contains scope limits."""
        fm, ticket_id = fm_with_artifacts
        result = await execute_tdd_red(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        text = result[0].text
        assert "Scope Limits" in text

    @pytest.mark.asyncio
    async def test_implement_phase_has_checklist(self, fm_with_artifacts):
        """Test that implement phase briefing contains pre-implementation checklist."""
        fm, ticket_id = fm_with_artifacts
        result = await implement_green(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        text = result[0].text
        assert "PRE-IMPLEMENTATION CHECKLIST" in text
        assert "ESCALATION REQUIRED" in text

    @pytest.mark.asyncio
    async def test_audit_phase_has_meta_guardrail(self, fm_with_artifacts):
        """Test that audit phase briefing contains meta-guardrail."""
        fm, ticket_id = fm_with_artifacts
        result = await run_audit(fm, {"ticket_id": ticket_id, "tier": "Tier 2"})

        text = result[0].text
        assert "Meta-Guardrail" in text
        assert "most broken implementation" in text


class TestToolDescriptions:
    """Tests for tool input schema validation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    @pytest.fixture
    def fm(self, temp_dir):
        """Create a FileManager instance."""
        return FileManager(str(temp_dir))

    def test_run_discovery_requires_fields(self, fm):
        """Test that run_discovery tool validates required fields."""
        from synthitect_mcp.server import TOOLS

        run_discovery_tool = next(t for t in TOOLS if t.name == "run_discovery")
        schema = run_discovery_tool.inputSchema

        assert schema["type"] == "object"
        assert "ticket_id" in schema["required"]
        assert "raw_idea" in schema["required"]
        assert "probe_reports" in schema["required"]

    def test_spawn_probe_requires_fields(self, fm):
        """Test that spawn_probe tool validates required fields."""
        from synthitect_mcp.server import TOOLS

        spawn_probe_tool = next(t for t in TOOLS if t.name == "spawn_probe")
        schema = spawn_probe_tool.inputSchema

        assert schema["type"] == "object"
        assert "ticket_id" in schema["required"]
        assert "layer_name" in schema["required"]
        assert "directory" in schema["required"]
        assert "raw_idea" in schema["required"]

    def test_tier_has_default(self, fm):
        """Test that tier parameter has a default value."""
        from synthitect_mcp.server import TOOLS

        for tool_name in ["generate_specs", "execute_tdd_red", "implement_green", "run_audit"]:
            tool = next(t for t in TOOLS if t.name == tool_name)
            schema = tool.inputSchema
            assert "tier" in schema["properties"]
            assert schema["properties"]["tier"].get("default") == "Tier 2"
