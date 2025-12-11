"""State management for KIWI-Video projects."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from kiwi_video.core.exceptions import StateError
from kiwi_video.utils.logger import get_logger


class StateManager:
    """
    Manages project state and history using JSON file storage.
    
    State is stored in project_state.json while history is stored
    in JSONL format for efficient append operations.
    """

    def __init__(self, workspace_dir: Path) -> None:
        """
        Initialize the state manager.
        
        Args:
            workspace_dir: Directory to store state files
        """
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = workspace_dir / "project_state.json"
        self.history_file = workspace_dir / "history.jsonl"

        self.logger = get_logger("state_manager")

        # Initialize state if doesn't exist
        if not self.state_file.exists():
            self._initialize_state()

    def _initialize_state(self) -> None:
        """Initialize a new project state file."""
        initial_state = {
            "project_id": self.workspace_dir.name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "initialized",
            "current_phase": None,
            "phases": {
                "story_loader": {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "output": {}
                },
                "storyboard": {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "output": {}
                },
                "film_crew": {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "scenes": []
                },
                "voice_actor": {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "output": {}
                }
            },
            "final_output": None,
            "metadata": {}
        }

        self._save_state(initial_state)
        self.logger.info(f"Initialized new project state: {self.workspace_dir.name}")

    def get_state(self) -> dict[str, Any]:
        """
        Get the current project state.
        
        Returns:
            Dictionary containing the current state
            
        Raises:
            StateError: If state file cannot be read
        """
        try:
            with open(self.state_file, encoding="utf-8") as f:
                state = json.load(f)
            return state

        except FileNotFoundError:
            self.logger.warning("State file not found, initializing...")
            self._initialize_state()
            return self.get_state()

        except json.JSONDecodeError as e:
            raise StateError(f"Failed to decode state file: {e}")

        except Exception as e:
            raise StateError(f"Failed to read state: {e}")

    def update_state(self, updates: dict[str, Any]) -> None:
        """
        Update the project state.
        
        Args:
            updates: Dictionary of updates to apply to state
        """
        try:
            state = self.get_state()

            # Deep update
            self._deep_update(state, updates)

            # Update timestamp
            state["updated_at"] = datetime.now().isoformat()

            # Save updated state
            self._save_state(state)

            self.logger.debug(f"State updated: {list(updates.keys())}")

        except Exception as e:
            raise StateError(f"Failed to update state: {e}")

    def _save_state(self, state: dict[str, Any]) -> None:
        """Save state to file."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise StateError(f"Failed to save state: {e}")

    def _deep_update(self, target: dict, source: dict) -> None:
        """
        Recursively update target dictionary with source.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with updates
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def start_phase(self, phase_name: str) -> None:
        """
        Mark a phase as started.
        
        Args:
            phase_name: Name of the phase
        """
        self.update_state({
            "current_phase": phase_name,
            "phases": {
                phase_name: {
                    "status": "in_progress",
                    "started_at": datetime.now().isoformat()
                }
            }
        })

        self.log_action(
            agent=phase_name,
            action="phase_started",
            data={}
        )

    def complete_phase(self, phase_name: str, output: dict[str, Any]) -> None:
        """
        Mark a phase as completed.
        
        Args:
            phase_name: Name of the phase
            output: Output data from the phase
        """
        self.update_state({
            "phases": {
                phase_name: {
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "output": output
                }
            }
        })

        self.log_action(
            agent=phase_name,
            action="phase_completed",
            data=output
        )

    def fail_phase(self, phase_name: str, error: str) -> None:
        """
        Mark a phase as failed.
        
        Args:
            phase_name: Name of the phase
            error: Error message
        """
        self.update_state({
            "phases": {
                phase_name: {
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "error": error
                }
            }
        })

        self.log_action(
            agent=phase_name,
            action="phase_failed",
            data={"error": error}
        )

    def log_action(
        self,
        agent: str,
        action: str,
        data: dict[str, Any] | None = None
    ) -> None:
        """
        Log an action to the history file (JSONL format).
        
        Args:
            agent: Name of the agent performing the action
            action: Action being performed
            data: Optional data associated with the action
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "action": action,
                "data": data or {}
            }

            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            self.logger.error(f"Failed to log action: {e}")

    def get_history(self, agent: str | None = None) -> list[dict[str, Any]]:
        """
        Get history entries, optionally filtered by agent.
        
        Args:
            agent: Optional agent name to filter by
            
        Returns:
            List of history entries
        """
        try:
            if not self.history_file.exists():
                return []

            history = []
            with open(self.history_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if agent is None or entry.get("agent") == agent:
                            history.append(entry)

            return history

        except Exception as e:
            self.logger.error(f"Failed to read history: {e}")
            return []

    def get_phase_status(self, phase_name: str) -> str:
        """
        Get the status of a specific phase.
        
        Args:
            phase_name: Name of the phase
            
        Returns:
            Phase status string
        """
        state = self.get_state()
        return state.get("phases", {}).get(phase_name, {}).get("status", "unknown")

    def set_final_output(self, output: dict[str, Any]) -> None:
        """
        Set the final project output.
        
        Args:
            output: Final output data
        """
        self.update_state({
            "final_output": output,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        })

        self.log_action(
            agent="orchestrator",
            action="project_completed",
            data=output
        )

    def get_scene_state(self, scene_id: str) -> dict[str, Any] | None:
        """
        Get state for a specific scene.
        
        Args:
            scene_id: Scene identifier
            
        Returns:
            Scene state dictionary or None if not found
        """
        state = self.get_state()
        scenes = state.get("phases", {}).get("film_crew", {}).get("scenes", [])

        for scene in scenes:
            if scene.get("scene_id") == scene_id:
                return scene

        return None

    def update_scene_state(self, scene_id: str, scene_data: dict[str, Any]) -> None:
        """
        Update state for a specific scene.
        
        Args:
            scene_id: Scene identifier
            scene_data: Updated scene data
        """
        state = self.get_state()
        scenes = state.get("phases", {}).get("film_crew", {}).get("scenes", [])

        # Find and update existing scene or add new one
        found = False
        for i, scene in enumerate(scenes):
            if scene.get("scene_id") == scene_id:
                scenes[i] = {**scene, **scene_data}
                found = True
                break

        if not found:
            scenes.append({"scene_id": scene_id, **scene_data})

        self.update_state({
            "phases": {
                "film_crew": {
                    "scenes": scenes
                }
            }
        })

