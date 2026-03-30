"""File manager utility for Synthitect Protocol MCP server."""

import json
import os
from pathlib import Path
from typing import Optional

# Valid phases in order
VALID_PHASES = ["discovery", "spec", "tdd_red", "implementation", "audit"]


class FileManager:
    """Manages file I/O for Synthitect Protocol plan artifacts."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize FileManager.

        Args:
            base_dir: Base directory for plans. Defaults to current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def create_ticket_directory(self, ticket_id: str) -> Path:
        """Create the plans/{ticket_id} directory.

        Args:
            ticket_id: The ticket identifier.

        Returns:
            Path to the created ticket directory.
        """
        ticket_dir = self.base_dir / "plans" / ticket_id
        ticket_dir.mkdir(parents=True, exist_ok=True)
        return ticket_dir

    def read_file(self, relative_path: str) -> str:
        """Read a file from the base directory.

        Args:
            relative_path: Path relative to base_dir.

        Returns:
            File contents as string.

        Raises:
            FileNotFoundError: If file does not exist.
        """
        file_path = self.base_dir / relative_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> Path:
        """Write content to a file.

        Args:
            relative_path: Path relative to base_dir.
            content: Content to write.

        Returns:
            Path to the written file.
        """
        file_path = self.base_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def read_template(self, template_name: str) -> str:
        """Read a prompt template from the prompts directory.

        Args:
            template_name: Name of the template file (e.g., 'discovery-phase.md').

        Returns:
            Template contents as string.
        """
        return self.read_file(f"prompts/{template_name}")

    def inject_variables(self, template: str, variables: dict[str, str]) -> str:
        """Inject variables into a template using {{ variable }} syntax.

        Args:
            template: Template string with {{ variable }} placeholders.
            variables: Dictionary of variable names to values.

        Returns:
            Template with variables replaced.
        """
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{ {key} }}}}"
            result = result.replace(placeholder, value)
        return result

    def ensure_discovery_exists(self, ticket_id: str) -> bool:
        """Check if discovery.md exists for a ticket.

        Args:
            ticket_id: The ticket identifier.

        Returns:
            True if discovery.md exists, False otherwise.
        """
        discovery_path = self.base_dir / "plans" / ticket_id / "discovery.md"
        return discovery_path.exists()

    def ensure_spec_exists(self, ticket_id: str) -> bool:
        """Check if spec.md and test_spec.md exist for a ticket.

        Args:
            ticket_id: The ticket identifier.

        Returns:
            True if both specs exist, False otherwise.
        """
        spec_path = self.base_dir / "plans" / ticket_id / "spec.md"
        test_spec_path = self.base_dir / "plans" / ticket_id / "test_spec.md"
        return spec_path.exists() and test_spec_path.exists()

    def get_plans_directory(self) -> Path:
        """Get the plans directory path.

        Returns:
            Path to the plans directory.
        """
        plans_dir = self.base_dir / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        return plans_dir

    def list_tickets(self) -> list[str]:
        """List all ticket IDs in the plans directory.

        Returns:
            List of ticket IDs.
        """
        plans_dir = self.get_plans_directory()
        return [d.name for d in plans_dir.iterdir() if d.is_dir()]

    def _get_phase_state_path(self, ticket_id: str) -> Path:
        """Get path to the phase state file.

        Args:
            ticket_id: The ticket identifier.

        Returns:
            Path to .phase_state.json file.
        """
        return self.base_dir / "plans" / ticket_id / ".phase_state.json"

    def get_phase_state(self, ticket_id: str) -> dict:
        """Get the phase state for a ticket.

        Args:
            ticket_id: The ticket identifier.

        Returns:
            Dict with 'current_phase' and 'completed_phases' keys.
        """
        state_path = self._get_phase_state_path(ticket_id)
        if not state_path.exists():
            return {"current_phase": None, "completed_phases": []}
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return {"current_phase": None, "completed_phases": []}

    def set_phase_state(self, ticket_id: str, phase: str, completed: bool = True) -> dict:
        """Set the phase state for a ticket.

        Args:
            ticket_id: The ticket identifier.
            phase: The phase to mark (discovery, spec, tdd_red, implementation, audit).
            completed: Whether this phase is completed (True) or in_progress (False).

        Returns:
            Updated phase state dict.

        Raises:
            ValueError: If phase is not a valid phase name.
        """
        if phase not in VALID_PHASES:
            raise ValueError(f"Invalid phase: {phase}. Must be one of {VALID_PHASES}")

        state = self.get_phase_state(ticket_id)

        if completed:
            if phase not in state["completed_phases"]:
                state["completed_phases"].append(phase)
            state["current_phase"] = None
        else:
            state["current_phase"] = phase

        state_path = self._get_phase_state_path(ticket_id)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

        return state

    def check_phase_prerequisite(self, ticket_id: str, required_phase: str) -> bool:
        """Check if a required phase has been completed.

        Args:
            ticket_id: The ticket identifier.
            required_phase: The phase that must be completed.

        Returns:
            True if the required phase is in completed_phases, False otherwise.
        """
        if required_phase not in VALID_PHASES:
            raise ValueError(f"Invalid phase: {required_phase}. Must be one of {VALID_PHASES}")

        state = self.get_phase_state(ticket_id)
        return required_phase in state["completed_phases"]

    def get_current_phase(self, ticket_id: str) -> Optional[str]:
        """Get the current in-progress phase for a ticket.

        Args:
            ticket_id: The ticket identifier.

        Returns:
            Current phase name or None if no phase is in progress.
        """
        state = self.get_phase_state(ticket_id)
        return state.get("current_phase")

    def clear_phase_state(self, ticket_id: str) -> None:
        """Clear the phase state for a ticket (used for resets).

        Args:
            ticket_id: The ticket identifier.
        """
        state_path = self._get_phase_state_path(ticket_id)
        if state_path.exists():
            state_path.unlink()
