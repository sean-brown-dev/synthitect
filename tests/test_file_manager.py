"""Unit tests for FileManager."""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from synthitect_mcp.file_manager import FileManager, VALID_PHASES


class TestFileManager:
    """Tests for FileManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    @pytest.fixture
    def fm(self, temp_dir):
        """Create a FileManager instance with temp directory."""
        return FileManager(str(temp_dir))

    @pytest.fixture
    def fm_with_ticket(self, fm):
        """Create a FileManager with a pre-created ticket directory."""
        ticket_dir = fm.create_ticket_directory("TEST-001")
        return fm, ticket_dir

    # =========================================================================
    # Directory Creation Tests
    # =========================================================================

    def test_create_ticket_directory(self, fm):
        """Test creating a ticket directory."""
        path = fm.create_ticket_directory("TEST-001")
        assert path == fm.base_dir / "plans" / "TEST-001"
        assert path.exists()
        assert path.is_dir()

    def test_create_ticket_directory_nested(self, fm):
        """Test that ticket directories are created under plans/."""
        path = fm.create_ticket_directory("FEAT-123")
        assert "plans" in path.parts
        assert "FEAT-123" in path.parts

    def test_create_ticket_directory_idempotent(self, fm):
        """Test that creating the same directory twice is safe."""
        fm.create_ticket_directory("TEST-001")
        path = fm.create_ticket_directory("TEST-001")  # Should not raise
        assert path.exists()

    # =========================================================================
    # File I/O Tests
    # =========================================================================

    def test_write_and_read_file(self, fm):
        """Test writing and reading a file."""
        content = "Hello, World!"
        fm.write_file("test.txt", content)
        result = fm.read_file("test.txt")
        assert result == content

    def test_read_file_not_found(self, fm):
        """Test that reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            fm.read_file("nonexistent.txt")

    def test_read_template(self, fm, temp_dir):
        """Test reading a template from prompts directory."""
        # Create prompts directory and template
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        template_content = "Hello {{ name }}"
        (prompts_dir / "test-template.md").write_text(template_content)

        result = fm.read_template("test-template.md")
        assert result == template_content

    # =========================================================================
    # Variable Injection Tests
    # =========================================================================

    def test_inject_variables(self, fm):
        """Test basic variable injection."""
        template = "Hello {{ name }}, you have {{ count }} messages."
        variables = {"name": "Alice", "count": "5"}
        result = fm.inject_variables(template, variables)
        assert result == "Hello Alice, you have 5 messages."

    def test_inject_variables_multiple(self, fm):
        """Test injecting multiple variables."""
        template = "{{ greeting }} {{ name }}"
        variables = {"greeting": "Hi", "name": "Bob"}
        result = fm.inject_variables(template, variables)
        assert result == "Hi Bob"

    def test_inject_variables_missing(self, fm):
        """Test that missing variables are left as placeholders."""
        template = "Hello {{ name }}, your code is {{ ticket_id }}"
        variables = {"name": "Alice"}  # Missing ticket_id
        result = fm.inject_variables(template, variables)
        assert "Alice" in result
        assert "{{ ticket_id }}" in result

    def test_inject_variables_empty_value(self, fm):
        """Test injecting empty string value."""
        template = "Name: {{ name }}"
        variables = {"name": ""}
        result = fm.inject_variables(template, variables)
        assert result == "Name: "

    # =========================================================================
    # Discovery/Spec Existence Tests
    # =========================================================================

    def test_ensure_discovery_exists_false(self, fm):
        """Test discovery check returns False when file doesn't exist."""
        fm.create_ticket_directory("TEST-001")
        assert fm.ensure_discovery_exists("TEST-001") is False

    def test_ensure_discovery_exists_true(self, fm):
        """Test discovery check returns True when file exists."""
        fm.create_ticket_directory("TEST-001")
        (fm.base_dir / "plans" / "TEST-001" / "discovery.md").write_text("# Discovery")
        assert fm.ensure_discovery_exists("TEST-001") is True

    def test_ensure_spec_exists_false_missing_spec(self, fm):
        """Test spec check returns False when spec.md is missing."""
        fm.create_ticket_directory("TEST-001")
        (fm.base_dir / "plans" / "TEST-001" / "test_spec.md").write_text("# Test Spec")
        assert fm.ensure_spec_exists("TEST-001") is False

    def test_ensure_spec_exists_false_missing_test_spec(self, fm):
        """Test spec check returns False when test_spec.md is missing."""
        fm.create_ticket_directory("TEST-001")
        (fm.base_dir / "plans" / "TEST-001" / "spec.md").write_text("# Spec")
        assert fm.ensure_spec_exists("TEST-001") is False

    def test_ensure_spec_exists_true(self, fm):
        """Test spec check returns True when both files exist."""
        fm.create_ticket_directory("TEST-001")
        (fm.base_dir / "plans" / "TEST-001" / "spec.md").write_text("# Spec")
        (fm.base_dir / "plans" / "TEST-001" / "test_spec.md").write_text("# Test Spec")
        assert fm.ensure_spec_exists("TEST-001") is True

    # =========================================================================
    # Phase State Tests
    # =========================================================================

    def test_get_phase_state_initial(self, fm):
        """Test that initial phase state is empty."""
        fm.create_ticket_directory("TEST-001")
        state = fm.get_phase_state("TEST-001")
        assert state == {"current_phase": None, "completed_phases": []}

    def test_get_phase_state_nonexistent(self, fm):
        """Test getting phase state for nonexistent ticket returns empty state."""
        state = fm.get_phase_state("NONEXISTENT")
        assert state == {"current_phase": None, "completed_phases": []}

    def test_set_phase_state_completed(self, fm):
        """Test setting a phase as completed."""
        fm.create_ticket_directory("TEST-001")
        state = fm.set_phase_state("TEST-001", "discovery", completed=True)
        assert "discovery" in state["completed_phases"]
        assert state["current_phase"] is None

    def test_set_phase_state_in_progress(self, fm):
        """Test setting a phase as in-progress."""
        fm.create_ticket_directory("TEST-001")
        state = fm.set_phase_state("TEST-001", "spec", completed=False)
        assert state["current_phase"] == "spec"
        assert "spec" not in state["completed_phases"]

    def test_set_phase_state_invalid_phase(self, fm):
        """Test that setting an invalid phase raises ValueError."""
        fm.create_ticket_directory("TEST-001")
        with pytest.raises(ValueError) as exc_info:
            fm.set_phase_state("TEST-001", "invalid_phase", completed=True)
        assert "invalid_phase" in str(exc_info.value)

    def test_set_phase_state_idempotent(self, fm):
        """Test that setting same phase twice doesn't duplicate."""
        fm.create_ticket_directory("TEST-001")
        fm.set_phase_state("TEST-001", "discovery", completed=True)
        fm.set_phase_state("TEST-001", "discovery", completed=True)
        state = fm.get_phase_state("TEST-001")
        assert state["completed_phases"].count("discovery") == 1

    def test_check_phase_prerequisite_true(self, fm):
        """Test that prerequisite check returns True when phase is completed."""
        fm.create_ticket_directory("TEST-001")
        fm.set_phase_state("TEST-001", "discovery", completed=True)
        assert fm.check_phase_prerequisite("TEST-001", "discovery") is True

    def test_check_phase_prerequisite_false(self, fm):
        """Test that prerequisite check returns False when phase is not completed."""
        fm.create_ticket_directory("TEST-001")
        assert fm.check_phase_prerequisite("TEST-001", "discovery") is False

    def test_check_phase_prerequisite_invalid(self, fm):
        """Test that checking invalid phase raises ValueError."""
        fm.create_ticket_directory("TEST-001")
        with pytest.raises(ValueError):
            fm.check_phase_prerequisite("TEST-001", "invalid")

    def test_get_current_phase(self, fm):
        """Test getting current in-progress phase."""
        fm.create_ticket_directory("TEST-001")
        assert fm.get_current_phase("TEST-001") is None
        fm.set_phase_state("TEST-001", "spec", completed=False)
        assert fm.get_current_phase("TEST-001") == "spec"

    def test_clear_phase_state(self, fm):
        """Test clearing phase state."""
        fm.create_ticket_directory("TEST-001")
        fm.set_phase_state("TEST-001", "discovery", completed=True)
        fm.clear_phase_state("TEST-001")
        state = fm.get_phase_state("TEST-001")
        assert state == {"current_phase": None, "completed_phases": []}

    # =========================================================================
    # Plans Directory Tests
    # =========================================================================

    def test_get_plans_directory(self, fm):
        """Test getting plans directory creates it if needed."""
        plans = fm.get_plans_directory()
        assert plans == fm.base_dir / "plans"
        assert plans.exists()

    def test_list_tickets(self, fm):
        """Test listing all tickets."""
        fm.create_ticket_directory("TASK-001")
        fm.create_ticket_directory("TASK-002")
        fm.create_ticket_directory("TASK-003")
        tickets = fm.list_tickets()
        assert len(tickets) == 3
        assert "TASK-001" in tickets
        assert "TASK-002" in tickets
        assert "TASK-003" in tickets


class TestPhaseStatePersistence:
    """Tests for phase state file persistence."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    @pytest.fixture
    def fm(self, temp_dir):
        """Create a FileManager instance with temp directory."""
        return FileManager(str(temp_dir))

    def test_phase_state_persists(self, fm):
        """Test that phase state is written to disk."""
        fm.create_ticket_directory("TEST-001")
        fm.set_phase_state("TEST-001", "discovery", completed=True)

        # Create new FileManager pointing to same directory
        fm2 = FileManager(str(fm.base_dir))
        state = fm2.get_phase_state("TEST-001")

        assert "discovery" in state["completed_phases"]

    def test_phase_state_file_format(self, fm):
        """Test that phase state is stored as valid JSON."""
        fm.create_ticket_directory("TEST-001")
        fm.set_phase_state("TEST-001", "discovery", completed=True)
        fm.set_phase_state("TEST-001", "spec", completed=True)

        state_file = fm.base_dir / "plans" / "TEST-001" / ".phase_state.json"
        content = state_file.read_text()

        # Should be valid JSON
        parsed = json.loads(content)
        assert parsed["completed_phases"] == ["discovery", "spec"]
